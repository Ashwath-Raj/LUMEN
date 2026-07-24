"""
LUMEN-owned quality tables — LUMEN_MASTER_SPEC_V3 §3.6 (quality & governance).

Two tables, reproduced verbatim from §3.6's DDL sketch:

    lumen_quality_finding(finding_id PK, rule_id, severity, entity_type,
                          entity_id, detail JSON, detected_at, state)
    lumen_quality_score(scope_type, scope_id, dimension, score, computed_at)

These are the §3.6 `lumen_` platform tables that back the Session 6 data
quality engine (§5). They are kept in a separate module from
`db/models/canonical.py` because that file's own docstring states it holds
"ONLY the 26 canonical tables from §3.5" and that the `lumen_` tables are
out of its scope. They share the same declarative `Base`, so
`Base.metadata` sees them once this module is imported.

`lumen_quality_score` has no single-column PK in §3.6. A composite primary
key over its four identifying columns is the minimal key that makes each
(scope_type, scope_id, dimension, computed_at) row addressable — the same
approach §3.3 prescribes for canonical tables lacking a declared PK.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, JSON, PrimaryKeyConstraint, String

from lumen.db.session import Base


class LumenQualityFinding(Base):
    __tablename__ = "lumen_quality_finding"

    finding_id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(10))          # "Q01".."Q18"
    severity = Column(String(20))         # Critical | High | Medium | Low
    entity_type = Column(String(60))      # canonical entity/table name the finding is about
    entity_id = Column(String(60))        # its identifier, rendered as text
    detail = Column(JSON)                 # rule-specific evidence
    detected_at = Column(DateTime)
    state = Column(String(20))            # lifecycle state of the finding


class LumenQualityScore(Base):
    __tablename__ = "lumen_quality_score"
    __table_args__ = (
        PrimaryKeyConstraint("scope_type", "scope_id", "dimension", "computed_at"),
    )

    scope_type = Column(String(20))       # state | district | unit  (§5.2)
    scope_id = Column(String(60))
    dimension = Column(String(20))        # one of the six §5.2 dimensions
    score = Column(Float)                 # 0..1
    computed_at = Column(DateTime)
