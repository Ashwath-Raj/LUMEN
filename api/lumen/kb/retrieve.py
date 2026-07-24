"""
Scope-filtered retrieval — LUMEN_MASTER_SPEC_V3 §15.2.

Rule 1 (the load-bearing sentence): "Retrieval is scope-filtered BEFORE
ranking. A Station Officer's query never retrieves a chunk from a case
outside their scope. Filter first, then rank — never the reverse." The
implementation is structurally faithful: the candidate set is narrowed by
index and scope, and the rank function runs only on what survived.

Rule 3: "The legal corpus (PUBLIC) and the case corpus (CONFIDENTIAL) are
separate indexes. Legal answers never leak case text." Indexes here are
disjoint kind-sets; a legal retrieval cannot touch a case_brief row because
the query itself excludes the kind — separation is structural, not a filter
that could be forgotten.

Rule 2: retrieved chunks carry doc_id, classification, effective_from and
become §8 `Evidence` entries with clickable URLs — returned as the §7
`EvidenceContract` bundle (the retriever's contract).

Ranking: §15 defines no ranking function, and embeddings are the QuickML
boundary (Session 14+). §24's degradation ladder itself names the fallback —
"QuickML RAG unavailable → Retrieval falls back to Data Store full-text" —
so the T1 default rank is deterministic lexical term overlap (count of query
terms present in the chunk, ties by chunk_id), exposed as a configurable
`rank_fn`. No embeddings, vector store, or semantic search here.

Scope model: jurisdiction scope is a set of district ids (§4.1 "Role +
jurisdiction scope"). `district_scope=None` means unscoped (e.g. State
Analyst); an explicit set restricts the CASE index to briefs whose case's
unit lies in-scope (case → Unit.DistrictID join at query time — the case's
district is not duplicated into the KB rows; §3.6 gives lumen_kb_document no
scope column).
"""
from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session

from lumen.contracts.evidence import EvidenceContract, RetrievedChunk
from lumen.contracts.insight import Evidence
from lumen.db.models import canonical as m
from lumen.db.models.kb import LumenKbChunk, LumenKbDocument

# §15.2 rule 3 — the separate indexes, as disjoint kind-sets. `sop` is
# INTERNAL and belongs to neither legal nor case (§15.2 names only those
# two); it stands as its own index — disclosed placement.
INDEXES: dict[str, tuple[str, ...]] = {
    "legal": ("act", "section", "crime_taxonomy"),   # PUBLIC corpus
    "case": ("case_brief",),                          # CONFIDENTIAL corpus
    "sop": ("sop",),                                  # INTERNAL, optional corpus
}

RankFn = Callable[[str, str], float]


def lexical_overlap(query: str, text: str) -> float:
    """The T1 fallback rank (§24: full-text fallback): how many distinct
    query terms appear in the chunk text. Deterministic, case-insensitive."""
    terms = {t for t in query.lower().split() if t}
    if not terms:
        return 0.0
    hay = text.lower()
    return float(sum(1 for t in terms if t in hay))


def _case_district(session: Session, case_id: int) -> int | None:
    case = session.get(m.CaseMaster, case_id)
    if case is None or case.PoliceStationID is None:
        return None
    unit = session.get(m.Unit, case.PoliceStationID)
    return unit.DistrictID if unit is not None else None


def retrieve(session: Session, query: str, *, index: str,
             district_scope: list[int] | None = None, k: int = 5,
             rank_fn: RankFn = lexical_overlap) -> EvidenceContract:
    """§15.2 retrieval: candidate set = one index (rule 3), scope-filtered
    (rule 1), THEN ranked; top-k returned as the EvidenceContract bundle
    (rule 2)."""
    if index not in INDEXES:
        raise ValueError(f"Unknown index {index!r}; §15.2 defines separate "
                         f"indexes {sorted(INDEXES)}.")

    # ── 1. index separation (rule 3) — structural, in the query itself ────
    kinds = INDEXES[index]
    rows = (
        session.query(LumenKbChunk, LumenKbDocument)
        .join(LumenKbDocument, LumenKbChunk.doc_id == LumenKbDocument.doc_id)
        .filter(LumenKbDocument.kind.in_(kinds))
        .order_by(LumenKbChunk.chunk_id)
        .all()
    )

    # ── 2. scope filter BEFORE ranking (rule 1) ────────────────────────────
    if index == "case" and district_scope is not None:
        allowed = set(district_scope)
        in_scope = []
        for chunk, doc in rows:
            case_id = int(doc.doc_id.split(":", 1)[1])
            district = _case_district(session, case_id)
            if district is not None and district in allowed:
                in_scope.append((chunk, doc))
        rows = in_scope

    # ── 3. rank what survived, never the reverse ───────────────────────────
    scored = [(rank_fn(query, chunk.text), chunk, doc) for chunk, doc in rows]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
    top = scored[:k]

    # ── 4. rule 2: chunks carry their metadata; docs become Evidence chips ─
    chunks = [
        RetrievedChunk(
            chunk_id=chunk.chunk_id, doc_id=doc.doc_id,
            classification=doc.classification,
            effective_from=doc.effective_from, ordinal=chunk.ordinal,
            text=chunk.text, score=score,
        )
        for score, chunk, doc in top
    ]
    seen: set[str] = set()
    evidence: list[Evidence] = []
    for score, chunk, doc in top:
        if doc.doc_id in seen:
            continue
        seen.add(doc.doc_id)
        evidence.append(Evidence(entity="kb_document", id=doc.doc_id,
                                 label=doc.title, url=f"/kb/{doc.doc_id}"))
    return EvidenceContract(index=index, query=query, chunks=chunks,
                            evidence=evidence)
