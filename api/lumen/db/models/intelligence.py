"""
Intelligence platform tables — LUMEN_MASTER_SPEC_V3 §3.6 (Session 8, §8–§10).

Two `lumen_` tables, defined verbatim from §3.6's DDL block:

    lumen_insight(insight_id UUID PK, kind, subject_type, subject_id, headline,
                  score, confidence, confidence_components JSON, factors JSON,
                  counterfactuals JSON, evidence JSON, limitations JSON,
                  lineage JSON, contract_version, lifecycle_state,
                  generated_at, expires_at, approved_by, approved_at)

    lumen_model_registry(model_id PK, name, kind, version, params JSON,
                         metrics JSON, trained_at, active BOOLEAN)

`lumen_model_registry` is created in THIS session because §8 invariant 5
("lineage.model_version exists in lumen_model_registry") cannot be enforced in
CI without the table existing. Only the table is created here — the registry
*module* (`lumen/registry/models.py`, §21) is Session 22 and remains untouched.

Notes kept faithful to the spec rather than smoothed over:
  * §3.6's `lumen_insight` DDL has NO `classification` column although §8's
    `Insight` model carries `classification`. The table follows §3.6 verbatim;
    classification lives on the contract and is validated by invariant 6 at
    construction/verification time (and §4.2's register row for `lumen_insight`
    says it "inherits the classification of its subject").
  * `approved_by` / `approved_at` exist here (not on the §8 contract) — §10:
    "Approval is recorded with approver and timestamp."
  * `person_id`-style UUIDs are stored as String(36) for PostgreSQL/Data Store
    portability, the same convention `identity.py` uses.
  * §3.6 gives no type for `lumen_model_registry.model_id`; String(80) is used
    (e.g. "isolation_forest@v1") — recorded as an implementation choice.
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, JSON, String

from lumen.db.session import Base


class LumenInsight(Base):
    __tablename__ = "lumen_insight"

    insight_id = Column(String(36), primary_key=True)     # UUID (§3.6)
    kind = Column(String(20))
    subject_type = Column(String(20))
    subject_id = Column(String(60))
    headline = Column(String(400))
    score = Column(Float)                                  # nullable — §8 score: float | None
    confidence = Column(Float)
    confidence_components = Column(JSON)                   # §8 ConfidenceBreakdown
    factors = Column(JSON)
    counterfactuals = Column(JSON)
    evidence = Column(JSON)
    limitations = Column(JSON)
    lineage = Column(JSON)
    contract_version = Column(String(10))
    lifecycle_state = Column(String(20))                   # §10
    generated_at = Column(DateTime)
    expires_at = Column(DateTime)
    approved_by = Column(String(120))                      # §10 approval record
    approved_at = Column(DateTime)


class LumenModelRegistry(Base):
    __tablename__ = "lumen_model_registry"

    model_id = Column(String(80), primary_key=True)
    name = Column(String(120))
    kind = Column(String(40))
    version = Column(String(40))
    params = Column(JSON)
    metrics = Column(JSON)
    trained_at = Column(DateTime)
    active = Column(Boolean)
