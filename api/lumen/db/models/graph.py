"""
Graph platform tables — LUMEN_MASTER_SPEC_V3 §3.6 (Session 9, §14).

Three `lumen_` tables, defined verbatim from §3.6's DDL block:

    lumen_graph_edge(src_type, src_id, dst_type, dst_id, rel, weight,
                     props JSON, computed_at)
    lumen_person_metrics(person_id FK, degree, betweenness, eigenvector,
                         community_id, district_span, computed_at)
    lumen_community(community_id PK, size, district_ids JSON,
                    broker_person_id, computed_at)

Notes kept faithful to the spec:
  * §3.6 declares NO primary key for `lumen_graph_edge`. A composite key over
    the five identity columns (src_type, src_id, dst_type, dst_id, rel) is
    declared here because the ORM requires one — the same treatment §3.3's
    "no declared PK" note gave `ActSectionAssociation`.
  * `lumen_person_metrics.person_id` is an FK to `lumen_person` (§3.6). Only
    resolved persons can therefore carry persisted metrics; §6.4 already
    excludes candidate matches from centrality, and unresolved singleton
    participants are not `lumen_person` rows at all.
  * Node/edge identity columns are strings: `src_id`/`dst_id` hold semantic
    entity ids (§2.1/§14.2 — "semantic entities, never table rows").
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    PrimaryKeyConstraint,
    String,
)

from lumen.db.session import Base


class LumenGraphEdge(Base):
    __tablename__ = "lumen_graph_edge"
    __table_args__ = (
        # §3.6 declares no PK; composite identity per the §3.3 precedent.
        PrimaryKeyConstraint("src_type", "src_id", "dst_type", "dst_id", "rel"),
    )

    src_type = Column(String(20))
    src_id = Column(String(60))
    dst_type = Column(String(20))
    dst_id = Column(String(60))
    rel = Column(String(30))
    weight = Column(Float)
    props = Column(JSON)
    computed_at = Column(DateTime)


class LumenPersonMetrics(Base):
    __tablename__ = "lumen_person_metrics"

    person_id = Column(String(36), ForeignKey("lumen_person.person_id"), primary_key=True)
    degree = Column(Integer)
    betweenness = Column(Float)
    eigenvector = Column(Float)
    community_id = Column(Integer)
    district_span = Column(Integer)
    computed_at = Column(DateTime)


class LumenCommunity(Base):
    __tablename__ = "lumen_community"

    community_id = Column(Integer, primary_key=True, autoincrement=False)
    size = Column(Integer)
    district_ids = Column(JSON)
    broker_person_id = Column(String(60))
    computed_at = Column(DateTime)
