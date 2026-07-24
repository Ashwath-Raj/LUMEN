"""
Prediction platform tables — LUMEN_MASTER_SPEC_V3 §3.6 (Session 10, §13).

Two `lumen_` tables, defined verbatim from §3.6's "geo / prediction" block:

    lumen_hotspot(cluster_id PK, centroid_lat, centroid_lng, radius_m, weight,
                  district_id, crime_head_id, window_start, window_end, method)
    lumen_district_risk(district_id FK, window_start, band, score,
                        factors JSON, model_version)

§13: "All models batch-score into tables; the API reads." These are the two
tables §3.6 assigns to prediction output. The other four §13 models have no
dedicated §3.6 table; their findings surface as `lumen_insight` rows via the
Session 8 pipeline (§8: "Everything in the platform that carries meaning is
one of these").

§3.6 declares no PK for `lumen_district_risk` — a composite key over
(district_id, window_start) is used, the §3.3 no-declared-PK precedent.
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    JSON,
    PrimaryKeyConstraint,
    String,
)

from lumen.db.session import Base


class LumenHotspot(Base):
    __tablename__ = "lumen_hotspot"

    cluster_id = Column(Integer, primary_key=True, autoincrement=False)
    centroid_lat = Column(Float)
    centroid_lng = Column(Float)
    radius_m = Column(Float)
    weight = Column(Float)
    district_id = Column(Integer, ForeignKey("District.DistrictID"))
    crime_head_id = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID"))
    window_start = Column(Date)
    window_end = Column(Date)
    method = Column(String(40))


class LumenDistrictRisk(Base):
    __tablename__ = "lumen_district_risk"
    __table_args__ = (
        # §3.6 declares no PK; composite identity per the §3.3 precedent.
        PrimaryKeyConstraint("district_id", "window_start"),
    )

    district_id = Column(Integer, ForeignKey("District.DistrictID"))
    window_start = Column(Date)
    band = Column(String(20))
    score = Column(Float)
    factors = Column(JSON)
    model_version = Column(String(40))
