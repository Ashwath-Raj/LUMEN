"""
Feature store table — LUMEN_MASTER_SPEC_V3 §3.6, §12.

    lumen_feature(entity_type, entity_id, feature_name, value, version,
                  computed_at)

§12: "One table, one loader, versioned." Every feature carries `version` and
`computed_at`; models and prompts READ features, never recompute them.

§3.6 declares no PK for `lumen_feature`; a feature is uniquely identified by
(entity_type, entity_id, feature_name, version) — a composite key over those
four, the §3.3 no-declared-PK precedent. `value` is stored as Float: every
§12 feature is numeric (flags are 0.0 / 1.0); §3.6 gives `value` no type.
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, PrimaryKeyConstraint, String

from lumen.db.session import Base


class LumenFeature(Base):
    __tablename__ = "lumen_feature"
    __table_args__ = (
        PrimaryKeyConstraint("entity_type", "entity_id", "feature_name", "version"),
    )

    entity_type = Column(String(20))     # person | case | district | unit
    entity_id = Column(String(60))
    feature_name = Column(String(60))
    value = Column(Float)
    version = Column(String(20))
    computed_at = Column(DateTime)
