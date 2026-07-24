"""
EvidenceContract v1 — LUMEN_MASTER_SPEC_V3 §7, §15.2.

§7's contract table lists `EvidenceContract` (v1, produced by the RETRIEVER,
consumed by the AI orchestrator and explainability) but — like Entity/Graph/
Prediction — defines no field-level shape. What §15.2 does fix about a
retrieval result:

  * rule 1: it was scope-filtered before ranking;
  * rule 2: every chunk carries `doc_id`, `classification`, `effective_from`,
    and retrieved chunks become `Evidence` entries with clickable URLs;
  * rule 3: it comes from exactly one index (legal and case never mix).

`EvidenceContract` below is the established minimal versioned envelope: the
retrieved chunks (each carrying rule 2's required metadata) plus their §8
`Evidence` chips, stamped with the index they came from. Nothing further is
invented.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from lumen.contracts.insight import Evidence


class RetrievedChunk(BaseModel):
    """One retrieved chunk with the §15.2 rule-2 metadata it must carry."""
    chunk_id: str
    doc_id: str
    classification: str
    effective_from: date | None = None
    ordinal: int
    text: str
    score: float                       # rank score (T1: lexical fallback, §24)


class EvidenceContract(BaseModel):
    """The retriever's output bundle (§7 EvidenceContract v1)."""
    contract_version: str = "v1"
    index: str                          # which separate index answered (§15.2 r3)
    query: str
    chunks: list[RetrievedChunk]
    evidence: list[Evidence]            # §15.2 r2 — clickable chips, one per chunk's doc
