"""
Identity (entity-resolution) platform tables — LUMEN_MASTER_SPEC_V3 §3.6, §6.

Three `lumen_` tables, defined verbatim from §3.6's DDL block:

    lumen_person(person_id UUID PK, canonical_name, first_seen, last_seen,
                 case_count, district_count, resolution_confidence, method_version)
    lumen_person_link(person_id FK, accused_master_id FK, confidence,
                      match_features JSON, state, PRIMARY KEY(person_id, accused_master_id))
    lumen_person_dispute(dispute_id PK, person_id FK, accused_master_id FK,
                         raised_by, reason, raised_at, resolution)

These are analytical overlays keyed to the canonical `Accused` rows (§3.6:
"keyed to canonical IDs, and never duplicates a canonical column"). They are
kept here rather than in `canonical.py` because §3.5's canonical schema is the
27 official tables only; the `lumen_` platform tables (§3.6) live alongside it
(same convention `quality.py` follows). Dropping every `lumen_` table must
leave exactly the official schema (§3.6), which these three respect — none
duplicates an `Accused` column; each references `Accused.AccusedMasterID`.

`person_id` is stated as UUID in §3.6. It is stored as a string column so the
same DDL works on both PostgreSQL and Data Store (§26.2 / ADR-002 portability);
the resolution job (§6.2 "persist") generates the UUID values.
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
    Text,
)

from lumen.db.session import Base


class LumenPerson(Base):
    """A resolved (inferred) person — §6. Always carries resolution
    confidence (§3.4 row for `Person`: "Inferred. Carries resolution
    confidence always"; P10)."""

    __tablename__ = "lumen_person"

    person_id = Column(String(36), primary_key=True)      # UUID (§3.6)
    canonical_name = Column(String(200))
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    case_count = Column(Integer)
    district_count = Column(Integer)
    resolution_confidence = Column(Float)                 # 0..1 (P10)
    method_version = Column(String(20))                   # §6.2 feature-weight version


class LumenPersonLink(Base):
    """One membership edge: a resolved person ↔ a canonical `Accused` row,
    with the per-link confidence and match evidence (§6.2 "persist ...
    with per-link confidence + match_features"). `state` distinguishes an
    auto-linked member (≥0.85) from a surfaced candidate (0.65–0.85) — §6.2
    threshold bands / §6.4 "Links below 0.85 render as candidate matches"."""

    __tablename__ = "lumen_person_link"
    __table_args__ = (
        PrimaryKeyConstraint("person_id", "accused_master_id"),
    )

    person_id = Column(String(36), ForeignKey("lumen_person.person_id"))
    accused_master_id = Column(Integer, ForeignKey("Accused.AccusedMasterID"))
    confidence = Column(Float)                             # 0..1 pair/link score
    match_features = Column(JSON)                          # §6.4 "see why" evidence
    state = Column(String(20))                             # "linked" | "candidate"


class LumenPersonDispute(Base):
    """A "report incorrect match" record — §6.4. Human-in-the-loop must be
    visible, not asserted: raising a dispute writes a row here (and the
    surface emits `PersonMatchDisputed`, wired when the event bus lands in
    Session 12; §19)."""

    __tablename__ = "lumen_person_dispute"

    dispute_id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(String(36), ForeignKey("lumen_person.person_id"))
    accused_master_id = Column(Integer, ForeignKey("Accused.AccusedMasterID"))
    raised_by = Column(String(120))
    reason = Column(Text)
    raised_at = Column(DateTime)
    resolution = Column(String(40))                        # NULL until adjudicated
