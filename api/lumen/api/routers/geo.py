"""
Geo Intelligence surface — LUMEN_MASTER_SPEC_V3 §29.1, §30.3.

  GET /geo/districts      — choropleth cells (district risk bands, §13)
  GET /geo/hotspots       — DBSCAN clusters + incident points (§13 hotspots)
  GET /geo/units/{id}     — a district's stations (drill level 3)
  GET /geo/delay          — reporting-delay layer (§3.2 fact 5)

§8 invariant 1: these carry risk BANDS and counts; numeric scores live inside
their Insights.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.db.models import canonical as m
from lumen.db.models.prediction import LumenDistrictRisk, LumenHotspot

router = APIRouter(prefix="/geo", tags=["Geo"])

def _band(score: float | None) -> str:
    s = score or 0.0
    return "critical" if s >= 0.8 else "high" if s >= 0.6 else "medium" if s >= 0.4 else "low"


@router.get("/hotspots")
def get_hotspots(
    district: str | None = Query(default=None),
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    heads = {h.CrimeHeadID: h.CrimeGroupName for h in db.query(m.CrimeHead).all()}
    risk_by_district = {r.district_id: (r.band or "low").lower() for r in db.query(LumenDistrictRisk).all()}

    hq = db.query(LumenHotspot)
    if district and district.isdigit():
        hq = hq.filter(LumenHotspot.district_id == int(district))
    hotspots = [
        {
            "hotspot_id": str(h.cluster_id),
            "center": [h.centroid_lat, h.centroid_lng],
            "case_count": int(h.weight or 0),
            "radius_m": h.radius_m or 300.0,
            "risk_band": risk_by_district.get(h.district_id, "medium"),
            "crime_head": heads.get(h.crime_head_id),
        }
        for h in hq.all()
        if h.centroid_lat is not None and h.centroid_lng is not None
    ]

    unit_district = {u.UnitID: u.DistrictID for u in db.query(m.Unit).all()}
    cq = db.query(m.CaseMaster).filter(
        m.CaseMaster.latitude.isnot(None), m.CaseMaster.longitude.isnot(None)
    )
    if date_from:
        cq = cq.filter(m.CaseMaster.CrimeRegisteredDate >= date_from)
    if date_to:
        cq = cq.filter(m.CaseMaster.CrimeRegisteredDate <= date_to)
    incidents = []
    for c in cq.limit(2000).all():
        did = unit_district.get(c.PoliceStationID)
        if district and district.isdigit() and did != int(district):
            continue
        incidents.append({
            "case_master_id": str(c.CaseMasterID),
            "crime_no": c.CrimeNo,
            "point": [float(c.latitude), float(c.longitude)],
            "crime_head": heads.get(c.CrimeMajorHeadID),
            "risk_band": risk_by_district.get(did),
        })

    return {"hotspots": hotspots, "incidents": incidents}


@router.get("/districts")
def get_districts(db: Session = Depends(get_db)) -> list[dict]:
    """§29.1 choropleth: one cell per district with its §13 risk band."""
    from lumen.db.models.canonical import Unit
    from sqlalchemy import func as _f
    names = {d.DistrictID: d.DistrictName for d in db.query(m.District).all()}
    unit_district = {u.UnitID: u.DistrictID for u in db.query(Unit).all()}
    counts: dict[int, int] = {}
    for station_id, n in (
        db.query(m.CaseMaster.PoliceStationID, _f.count())
        .group_by(m.CaseMaster.PoliceStationID).all()
    ):
        did = unit_district.get(station_id)
        if did is not None:
            counts[did] = counts.get(did, 0) + n
    return [
        {
            "district_id": str(r.district_id),
            "district_name": names.get(r.district_id, f"District {r.district_id}"),
            "risk_band": (r.band or "low").lower(),
            "case_count": counts.get(r.district_id, 0),
        }
        for r in db.query(LumenDistrictRisk).all()
    ]


@router.get("/units/{district_id}")
def get_units(district_id: int, db: Session = Depends(get_db)) -> dict:
    """§29.1 drill level 3 — the district's police stations with their case
    load and the district's risk band (§8 invariant 1: band, not score)."""
    from lumen.db.models.canonical import Unit
    from sqlalchemy import func as _f
    risk = {r.district_id: (r.band or "low").lower() for r in db.query(LumenDistrictRisk).all()}
    counts = dict(
        db.query(m.CaseMaster.PoliceStationID, _f.count())
        .group_by(m.CaseMaster.PoliceStationID).all()
    )
    units = []
    for u in db.query(Unit).filter(Unit.DistrictID == district_id).all():
        pts = [
            (float(c.latitude), float(c.longitude))
            for c in db.query(m.CaseMaster)
            .filter(m.CaseMaster.PoliceStationID == u.UnitID,
                    m.CaseMaster.latitude.isnot(None), m.CaseMaster.longitude.isnot(None))
            .all()
        ]
        centre = (
            [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
            if pts else None
        )
        if centre is None:
            continue  # no geocoded case in this catchment — omit, never invent
        units.append({
            "unit_id": str(u.UnitID),
            "unit_name": u.UnitName,
            "district_id": str(district_id),
            "center": centre,
            "case_count": counts.get(u.UnitID, 0),
            "risk_band": risk.get(district_id),
        })
    return {"district_id": str(district_id), "units": units}


@router.get("/delay")
def get_delay(district: str | None = Query(default=None),
              db: Session = Depends(get_db)) -> dict:
    """§29.1 / §3.2 fact 5 — reporting delay: median days between the incident
    and its registration, per station, with the §13 anomaly flag (a unit whose
    median exceeds 1.5x the state median)."""
    from statistics import median as _median
    from lumen.db.models.canonical import Unit
    per_unit: dict[int, list[int]] = {}
    for c in db.query(m.CaseMaster).filter(
        m.CaseMaster.IncidentFromDate.isnot(None),
        m.CaseMaster.CrimeRegisteredDate.isnot(None),
    ).all():
        inc = c.IncidentFromDate.date() if hasattr(c.IncidentFromDate, "date") else c.IncidentFromDate
        days = (c.CrimeRegisteredDate - inc).days
        if days >= 0:
            per_unit.setdefault(c.PoliceStationID, []).append(days)
    if not per_unit:
        return {"units": []}
    medians = {uid: _median(v) for uid, v in per_unit.items()}
    state_median = _median(list(medians.values()))
    threshold = state_median * 1.5

    out = []
    for u in db.query(Unit).all():
        if u.UnitID not in medians:
            continue
        if district and district.isdigit() and u.DistrictID != int(district):
            continue
        pts = [
            (float(c.latitude), float(c.longitude))
            for c in db.query(m.CaseMaster)
            .filter(m.CaseMaster.PoliceStationID == u.UnitID,
                    m.CaseMaster.latitude.isnot(None), m.CaseMaster.longitude.isnot(None))
            .all()
        ]
        if not pts:
            continue
        out.append({
            "unit_id": str(u.UnitID),
            "unit_name": u.UnitName,
            "district_id": str(u.DistrictID),
            "center": [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)],
            "median_delay_days": int(medians[u.UnitID]),
            "anomalous": medians[u.UnitID] > threshold,
        })
    return {"units": out}
