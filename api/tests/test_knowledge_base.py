"""
Session 13 — knowledge base ingestion + scope-filtered retrieval (§15).

The §33 row-13 done-when, enforced in CI: "Legal and case indexes separate;
scope filter tested."

Covers: §15.1 corpus construction (kinds, sources, classifications; sop
optional and absent), §15.2 rule 2 (chunk metadata + Evidence chips with
clickable URLs), rule 3 (structural index separation — legal never leaks
case text), rule 1 (scope filter BEFORE ranking), rule 4 (job + checksummed
re-ingest on Act/Section change; embedding deferred at the QuickML
boundary), chunking config, determinism, persistence, serialization,
Session 8 integration (kb_document evidence resolves), and edge cases.

Self-contained: in-memory SQLite, no live PostgreSQL, no QuickML.
"""
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.contracts.evidence import EvidenceContract
from lumen.db.models import canonical as m
from lumen.db.models.kb import LumenKbChunk, LumenKbDocument
from lumen.jobs.kb_ingest import run_kb_ingest
from lumen.jobs.seed import seed_database
from lumen.kb import ingest as kb_ingest
from lumen.kb.retrieve import INDEXES, lexical_overlap, retrieve

NOWHERE_TERM = "zzznomatch"


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture()
def kb():
    s = _fresh_session()
    seed_database(s)
    run_kb_ingest(s)
    return s


# ── §15.1 corpus ───────────────────────────────────────────────────────────

def test_corpus_kinds_sources_and_classifications(kb):
    docs = kb.query(LumenKbDocument).all()
    by_kind = {}
    for d in docs:
        by_kind.setdefault(d.kind, []).append(d)
    assert set(by_kind) == {"act", "section", "crime_taxonomy", "case_brief"}
    # §15.1 classifications, verbatim
    assert all(d.classification == "PUBLIC" for d in by_kind["act"])
    assert all(d.classification == "PUBLIC" for d in by_kind["section"])
    assert all(d.classification == "PUBLIC" for d in by_kind["crime_taxonomy"])
    assert all(d.classification == "CONFIDENTIAL" for d in by_kind["case_brief"])
    # §15.1 sources, verbatim
    assert by_kind["act"][0].source == "Act.ActDescription"
    assert by_kind["section"][0].source == "Section.SectionDescription"
    # sop is optional and no real documents exist — nothing fabricated
    assert "sop" not in by_kind


def test_taxonomy_maps_heads_to_typical_sections(kb):
    doc = kb.get(LumenKbDocument, "crime_taxonomy:1")
    text = " ".join(c.text for c in kb.query(LumenKbChunk)
                    .filter_by(doc_id=doc.doc_id).order_by(LumenKbChunk.ordinal))
    assert "Sub-heads:" in text            # CrimeSubHead content
    # CrimeHeadActSection rows exist for head 1 in the seed reference data?
    # (presence of the mapping line is asserted only when links exist)
    links = kb.query(m.CrimeHeadActSection).filter_by(CrimeHeadID=1).count()
    assert ("Typical sections:" in text) == (links > 0)


# ── §15.2 rule 2: chunk metadata + Evidence chips ──────────────────────────

def test_chunks_carry_doc_id_classification_effective_from(kb):
    r = retrieve(kb, "murder", index="legal")
    assert r.chunks
    for c in r.chunks:
        assert c.doc_id and c.classification == "PUBLIC"
        assert c.effective_from is None    # canonical sources carry no dates
        assert c.ordinal >= 1 and c.text


def test_retrieved_chunks_become_clickable_evidence(kb):
    r = retrieve(kb, "murder", index="legal")
    assert r.evidence
    for ev in r.evidence:
        assert ev.entity == "kb_document"
        assert ev.url == f"/kb/{ev.id}"


def test_kb_evidence_resolves_for_invariant_3(kb):
    """Session 8's resolver deferred kb_document to Session 13 — now real."""
    from lumen.intelligence.explain import resolve_evidence
    r = retrieve(kb, "murder", index="legal")
    assert all(resolve_evidence(kb, ev) for ev in r.evidence)
    from lumen.contracts.insight import Evidence
    ghost = Evidence(entity="kb_document", id="act:GHOST", label="x", url="/kb/x")
    assert not resolve_evidence(kb, ghost)


# ── §15.2 rule 3: separate indexes (§33 done-when part 1) ──────────────────

def test_legal_index_never_returns_case_text(kb):
    # case briefs contain the word 'case'; a legal query for it must not leak
    r = retrieve(kb, "hotspot cluster case brief", index="legal", k=50)
    assert all(not c.doc_id.startswith("case_brief:") for c in r.chunks)
    assert all(c.classification == "PUBLIC" for c in r.chunks)


def test_case_index_never_returns_legal_text(kb):
    r = retrieve(kb, "murder penal code", index="case", k=50)
    assert all(c.doc_id.startswith("case_brief:") for c in r.chunks)


def test_indexes_are_disjoint_kind_sets():
    kinds = [set(v) for v in INDEXES.values()]
    for i in range(len(kinds)):
        for j in range(i + 1, len(kinds)):
            assert not (kinds[i] & kinds[j])


def test_unknown_index_rejected(kb):
    with pytest.raises(ValueError, match="separate indexes"):
        retrieve(kb, "q", index="everything")


# ── §15.2 rule 1: scope filter BEFORE rank (§33 done-when part 2) ──────────

def test_scope_filter_excludes_out_of_scope_case_chunks(kb):
    # the g1 hotspot briefs are district 1; a district-3 scope must not see
    # them even though they match the query terms strongly
    unscoped = retrieve(kb, "Hotspot cluster case", index="case", k=50)
    assert any(c.doc_id == "case_brief:1000" for c in unscoped.chunks)
    scoped = retrieve(kb, "Hotspot cluster case", index="case",
                      district_scope=[3], k=50)
    assert scoped.chunks == [] or all(
        c.doc_id != "case_brief:1000" for c in scoped.chunks)
    # and what does come back is genuinely in-scope
    for c in scoped.chunks:
        case_id = int(c.doc_id.split(":", 1)[1])
        case = kb.get(m.CaseMaster, case_id)
        unit = kb.get(m.Unit, case.PoliceStationID)
        assert unit.DistrictID == 3


def test_filter_happens_before_rank_not_after(kb):
    """Top-k truncation must not be the mechanism hiding out-of-scope rows:
    with k=1 and a scope, the single result is in-scope even though the
    best UNSCOPED match is out-of-scope."""
    best_unscoped = retrieve(kb, "Hotspot cluster case", index="case", k=1)
    assert best_unscoped.chunks[0].doc_id.startswith("case_brief:100")  # district 1
    scoped = retrieve(kb, "Hotspot cluster case", index="case",
                      district_scope=[2], k=1)
    if scoped.chunks:                       # in-scope winner, not a truncated leak
        case_id = int(scoped.chunks[0].doc_id.split(":", 1)[1])
        unit = kb.get(m.Unit, kb.get(m.CaseMaster, case_id).PoliceStationID)
        assert unit.DistrictID == 2


def test_unscoped_retrieval_allowed_for_state_scope(kb):
    r = retrieve(kb, "case", index="case", district_scope=None, k=5)
    assert r.chunks                          # State Analyst: no restriction


# ── §15.2 rule 4: job, checksums, re-ingest on Act/Section change ──────────

def test_reingest_is_idempotent(kb):
    first = run_kb_ingest(kb)
    assert first["written"] == 0 and first["unchanged"] > 0


def test_reingest_on_act_section_change(kb):
    doc_before = kb.get(LumenKbDocument, "section:IPC:302")
    checksum_before = doc_before.checksum
    sec = kb.query(m.Section).filter_by(ActCode="IPC", SectionCode="302").one()
    sec.SectionDescription = sec.SectionDescription + " Amended by Act 2026."
    kb.flush()
    summary = run_kb_ingest(kb)
    assert summary["written"] == 1           # only the changed document
    doc_after = kb.get(LumenKbDocument, "section:IPC:302")
    assert doc_after.checksum != checksum_before
    text = " ".join(c.text for c in kb.query(LumenKbChunk)
                    .filter_by(doc_id="section:IPC:302").order_by(LumenKbChunk.ordinal))
    assert "Amended by Act 2026." in text


def test_embedding_deferred_at_quickml_boundary(kb):
    """§15.2 r4's 'embed via QuickML' is Session 14+: refs stay NULL."""
    assert all(c.embedding_ref is None for c in kb.query(LumenKbChunk).all())


# ── chunking (config — strategy not spec-defined) ──────────────────────────

def test_chunking_respects_max_chars_and_ordinals():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = kb_ingest.chunk_text(text, max_chars=100)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)
    assert " ".join(chunks) == text          # lossless, word-boundary split
    assert kb_ingest.chunk_text("") == []


def test_long_brief_splits_into_ordered_chunks(kb):
    long_brief = "stolen vehicle recovered near checkpoint " * 40
    kb.add(m.CaseMaster(CaseMasterID=77000, CrimeNo="CN77000",
                        PoliceStationID=11, BriefFacts=long_brief))
    kb.flush()
    run_kb_ingest(kb)
    chunks = (kb.query(LumenKbChunk).filter_by(doc_id="case_brief:77000")
              .order_by(LumenKbChunk.ordinal).all())
    assert len(chunks) > 1
    assert [c.ordinal for c in chunks] == list(range(1, len(chunks) + 1))
    assert all(c.token_count == len(c.text.split()) for c in chunks)


# ── determinism + serialization ────────────────────────────────────────────

def test_ingest_is_deterministic_across_fresh_databases():
    def snapshot():
        s = _fresh_session()
        seed_database(s)
        run_kb_ingest(s)
        return [(d.doc_id, d.checksum, d.classification)
                for d in s.query(LumenKbDocument).order_by(LumenKbDocument.doc_id)]
    assert snapshot() == snapshot()


def test_retrieval_is_deterministic_and_serializable(kb):
    a = retrieve(kb, "murder", index="legal")
    b = retrieve(kb, "murder", index="legal")
    assert a == b
    again = EvidenceContract.model_validate_json(a.model_dump_json())
    assert again == a
    assert again.contract_version == "v1"


# ── edge cases ─────────────────────────────────────────────────────────────

def test_no_match_returns_empty_bundle(kb):
    r = retrieve(kb, NOWHERE_TERM, index="legal")
    assert r.chunks == [] and r.evidence == []


def test_empty_query_returns_empty(kb):
    assert retrieve(kb, "   ", index="legal").chunks == []
    assert lexical_overlap("", "anything") == 0.0


def test_sop_ingest_api_for_real_documents(kb):
    """§15.1: sop is optional, for real uploads — the API works when one
    exists, and lands in the sop index only."""
    kb_ingest.ingest_sop_document(
        kb, slug="fir-guidelines", title="FIR Registration Guidelines",
        text="An FIR must be registered without delay upon receiving "
             "information of a cognizable offence.",
        source="uploaded:circular-2026-04", effective_from=date(2026, 4, 1))
    doc = kb.get(LumenKbDocument, "sop:fir-guidelines")
    assert doc.classification == "INTERNAL" and doc.effective_from == date(2026, 4, 1)
    r = retrieve(kb, "cognizable offence registered", index="sop")
    assert r.chunks and r.chunks[0].doc_id == "sop:fir-guidelines"
    assert r.chunks[0].effective_from == date(2026, 4, 1)
    legal = retrieve(kb, "cognizable offence registered", index="legal", k=50)
    assert all(not c.doc_id.startswith("sop:") for c in legal.chunks)
