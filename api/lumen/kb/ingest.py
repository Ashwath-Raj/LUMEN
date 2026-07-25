"""
Knowledge base ingestion — LUMEN_MASTER_SPEC_V3 §15.1, §15.2 rule 4.

Builds the §15.1 corpus from the canonical tables and persists it to
`lumen_kb_document` / `lumen_kb_chunk` (§3.6):

    act            Act.ActDescription                        PUBLIC
    section        Section.SectionDescription                PUBLIC
    crime_taxonomy CrimeHead / CrimeSubHead / CrimeHeadActSection  PUBLIC
    case_brief     CaseMaster.BriefFacts                     CONFIDENTIAL
    sop            uploaded documents — OPTIONAL (§15.1: "include only if
                   real documents exist"); `ingest_sop_document` is the entry
                   point for real uploads, nothing is fabricated.

§15.2 rule 4: "Ingestion is a job: chunk → embed via QuickML → store refs in
lumen_kb_chunk. Re-ingest on Act/Section change." The EMBED step is the exact
Session 13/14 boundary (QuickML is §16/§26.1 territory) and is deferred:
chunks persist with `embedding_ref = NULL`, filled when QuickML lands.
Re-ingest-on-change is implemented via the document `checksum` (sha256 of the
source text): an unchanged document is left untouched; a changed one has its
chunks rewritten.

Disclosed (cannot be determined from the specification):
  * The chunking strategy. §15.1 says case briefs are "chunked" but no
    strategy is given → configuration: word-boundary splitting at
    `max_chars` (default 500). Short legal texts fit one chunk.
  * `token_count` — no tokenizer is named → whitespace word count.
  * `effective_from` — Act/Section/CaseMaster carry no effectivity dates →
    None for canonical corpus kinds; sop uploads may supply one.
  * doc_id conventions ("act:IPC", "section:IPC:302", "crime_taxonomy:1",
    "case_brief:1000", "sop:<slug>") — composite-id formats, the established
    precedent.

Deterministic throughout: fixed doc_id/chunk_id formats, sha256 checksums,
stable iteration order, no randomness, no timestamps in ids.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.db.models.kb import LumenKbChunk, LumenKbDocument

DEFAULT_MAX_CHARS = 500        # chunking config (strategy not spec-defined)

# §15.1 classification per corpus kind — verbatim.
KIND_CLASSIFICATION = {
    "act": "PUBLIC",
    "section": "PUBLIC",
    "crime_taxonomy": "PUBLIC",
    "case_brief": "CONFIDENTIAL",
    "sop": "INTERNAL",
}


@dataclass(frozen=True)
class SourceDoc:
    doc_id: str
    kind: str
    title: str
    source: str
    text: str
    effective_from: date | None = None


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, *, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    """Word-boundary chunking at `max_chars` (configuration; §15.1 mandates
    chunking for case briefs but defines no strategy)."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        added = len(word) + (1 if current else 0)
        if current and length + added > max_chars:
            chunks.append(" ".join(current))
            current, length = [], 0
            added = len(word)
        current.append(word)
        length += added
    chunks.append(" ".join(current))
    return chunks


# ── §15.1 corpus builders (canonical sources, verbatim) ────────────────────

def _act_docs(session: Session) -> list[SourceDoc]:
    docs = []
    for act in session.query(m.Act).order_by(m.Act.ActCode):
        if act.ActDescription:
            docs.append(SourceDoc(
                doc_id=f"act:{act.ActCode}", kind="act",
                title=act.ShortName or act.ActCode, source="Act.ActDescription",
                text=act.ActDescription))
    return docs


def _section_docs(session: Session) -> list[SourceDoc]:
    docs = []
    for sec in session.query(m.Section).order_by(m.Section.ActCode, m.Section.SectionCode):
        if sec.SectionDescription:
            docs.append(SourceDoc(
                doc_id=f"section:{sec.ActCode}:{sec.SectionCode}", kind="section",
                title=f"{sec.ActCode} {sec.SectionCode}",
                source="Section.SectionDescription", text=sec.SectionDescription))
    return docs


def _taxonomy_docs(session: Session) -> list[SourceDoc]:
    """One document per CrimeHead: its sub-heads and its typical act-sections
    (CrimeHeadActSection) — 'maps heads to typical sections' (§15.1)."""
    subheads: dict[int, list[str]] = {}
    for sh in session.query(m.CrimeSubHead).order_by(m.CrimeSubHead.CrimeSubHeadID):
        if sh.CrimeHeadID is not None and sh.CrimeHeadName:
            subheads.setdefault(sh.CrimeHeadID, []).append(sh.CrimeHeadName)
    sections: dict[int, list[str]] = {}
    for link in session.query(m.CrimeHeadActSection).order_by(
            m.CrimeHeadActSection.CrimeHeadID, m.CrimeHeadActSection.ActCode,
            m.CrimeHeadActSection.SectionCode):
        sections.setdefault(link.CrimeHeadID, []).append(
            f"{link.ActCode} {link.SectionCode}")
    docs = []
    for head in session.query(m.CrimeHead).order_by(m.CrimeHead.CrimeHeadID):
        if not head.CrimeGroupName:
            continue
        parts = [head.CrimeGroupName]
        if subheads.get(head.CrimeHeadID):
            parts.append("Sub-heads: " + "; ".join(subheads[head.CrimeHeadID]))
        if sections.get(head.CrimeHeadID):
            parts.append("Typical sections: " + "; ".join(sections[head.CrimeHeadID]))
        docs.append(SourceDoc(
            doc_id=f"crime_taxonomy:{head.CrimeHeadID}", kind="crime_taxonomy",
            title=head.CrimeGroupName,
            source="CrimeHead/CrimeSubHead/CrimeHeadActSection",
            text=". ".join(parts)))
    return docs


def _case_brief_docs(session: Session) -> list[SourceDoc]:
    docs = []
    for case in session.query(m.CaseMaster).order_by(m.CaseMaster.CaseMasterID):
        if case.BriefFacts:
            docs.append(SourceDoc(
                doc_id=f"case_brief:{case.CaseMasterID}", kind="case_brief",
                title=f"Case {case.CaseMasterID} brief",
                source="CaseMaster.BriefFacts", text=case.BriefFacts))
    return docs


def collect_corpus(session: Session) -> list[SourceDoc]:
    """The §15.1 canonical corpus. `sop` is NOT collected here — §15.1 makes
    it optional pending real uploaded documents (`ingest_sop_document`)."""
    return (_act_docs(session) + _section_docs(session)
            + _taxonomy_docs(session) + _case_brief_docs(session))


# ── persistence (chunk → [embed: deferred] → store refs, §15.2 r4) ─────────

def ingest_document(session: Session, doc: SourceDoc,
                    *, max_chars: int = DEFAULT_MAX_CHARS) -> bool:
    """Ingest one document. Returns True if (re)written, False if unchanged
    (checksum match — §15.2 r4's re-ingest-on-change)."""
    checksum = _checksum(doc.text)
    existing = session.get(LumenKbDocument, doc.doc_id)
    if existing is not None and existing.checksum == checksum:
        return False
    if existing is not None:   # changed → rewrite chunks
        session.query(LumenKbChunk).filter(LumenKbChunk.doc_id == doc.doc_id).delete()
        session.delete(existing)
        session.flush()
    session.add(LumenKbDocument(
        doc_id=doc.doc_id, kind=doc.kind, title=doc.title, source=doc.source,
        effective_from=doc.effective_from,
        classification=KIND_CLASSIFICATION[doc.kind], checksum=checksum))
    # FK-ordering fix: with FK-only models the unit of work flushes unrelated
    # mappers in table-name order, and "lumen_kb_chunk" sorts before
    # "lumen_kb_document" — flush the parent before adding its chunks.
    session.flush()
    for ordinal, text in enumerate(chunk_text(doc.text, max_chars=max_chars), start=1):
        session.add(LumenKbChunk(
            chunk_id=f"{doc.doc_id}#{ordinal}", doc_id=doc.doc_id, ordinal=ordinal,
            text=text, embedding_ref=None,          # QuickML embed: Session 14+
            token_count=len(text.split())))
    session.flush()
    return True


def ingest_sop_document(session: Session, *, slug: str, title: str, text: str,
                        source: str, effective_from: date | None = None,
                        max_chars: int = DEFAULT_MAX_CHARS) -> bool:
    """§15.1 `sop` — optional, for REAL uploaded documents only. Nothing is
    fabricated at ingest time; this is the entry point an upload surface
    calls."""
    return ingest_document(session, SourceDoc(
        doc_id=f"sop:{slug}", kind="sop", title=title, source=source,
        text=text, effective_from=effective_from), max_chars=max_chars)
