"""
Overview surface — LUMEN_MASTER_SPEC_V3 §29.1 (`GET /overview`):
"Command centre: counts, trend, risk bands, anomalies, top network figures,
quality score".

§8 invariant 1 keeps numeric scores inside Insights, so this payload carries
counts, district risk BANDS, trends and network figures; the §5.2 quality
numerics are served by `/quality/scores`.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.db.models import canonical as m
from lumen.db.models.identity import LumenPerson
from lumen.db.models.graph import LumenPersonMetrics
from lumen.db.models.intelligence import LumenInsight
from lumen.db.models.prediction import LumenDistrictRisk
from lumen.db.models.quality import LumenQualityScore

router = APIRouter(tags=["Overview"])


def _district_names(db: Session) -> dict[int, str]:
    return {d.DistrictID: d.DistrictName for d in db.query(m.District).all()}


def _district_risk_rows(db: Session) -> list[dict]:
    names = _district_names(db)
    unit_district = {u.UnitID: u.DistrictID for u in db.query(m.Unit).all()}
    counts: dict[int, int] = defaultdict(int)
    for (station_id, n) in (
        db.query(m.CaseMaster.PoliceStationID, func.count()).group_by(m.CaseMaster.PoliceStationID).all()
    ):
        did = unit_district.get(station_id)
        if did is not None:
            counts[did] += n
    rows = []
    for r in db.query(LumenDistrictRisk).all():
        rows.append({
            "district_id": str(r.district_id),
            "district_name": names.get(r.district_id, f"District {r.district_id}"),
            # Band only — the numeric score lives in the district's risk Insight
            # (§8 invariant 1). `/quality/scores` serves §5.2 quality numerics.
            "risk_band": (r.band or "low").lower(),
            "case_count": counts.get(r.district_id, 0),
        })
    return rows


@router.get("/overview")
def get_summary(db: Session = Depends(get_db)) -> dict:
    district_risk = _district_risk_rows(db)

    period_cases = db.query(m.CaseMaster).count()
    active_anomalies = (
        db.query(LumenInsight)
        .filter(LumenInsight.kind == "anomaly", LumenInsight.lifecycle_state != "expired")
        .count()
    )
    high_band = sum(1 for d in district_risk if d["risk_band"] in ("high", "critical"))
    central_persons = db.query(LumenPersonMetrics).filter(LumenPersonMetrics.degree > 1).count()
    heinous = (
        db.query(m.CaseMaster)
        .join(m.GravityOffence, m.GravityOffence.GravityOffenceID == m.CaseMaster.GravityOffenceID)
        .filter(m.GravityOffence.LookupValue == "Heinous")
        .count()
    )
    awaiting = (
        db.query(LumenInsight)
        .filter(LumenInsight.lifecycle_state.in_(["generated", "verified"]))
        .count()
    )

    figures = []
    metric_rows = (
        db.query(LumenPersonMetrics, LumenPerson)
        .join(LumenPerson, LumenPerson.person_id == LumenPersonMetrics.person_id)
        .order_by(LumenPersonMetrics.betweenness.desc())
        .limit(5)
        .all()
    )
    for met, person in metric_rows:
        figures.append({
            "person_id": person.person_id,
            "label": person.canonical_name,
            "centrality": met.betweenness or 0.0,  # graph metric (§14), not an §8 score
        })

    return {
        "counts": {
            "period_cases": period_cases,
            "active_anomalies": active_anomalies,
            "high_band_districts": high_band,
            "network_central_persons": central_persons,
            "priority_cases": heinous,
            "recommendations_awaiting_review": awaiting,
        },
        "district_risk": [
            {"district_id": d["district_id"], "district_name": d["district_name"],
             "band": d["risk_band"], "case_count": d["case_count"]}
            for d in district_risk
        ],
        "trends": _trends(db),
        "network_figures": figures,
    }


def _trends(db: Session) -> list[dict]:
    heads = {h.CrimeHeadID: h.CrimeGroupName for h in db.query(m.CrimeHead).all()}
    buckets: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in db.query(m.CaseMaster).all():
        d: date | None = c.CrimeRegisteredDate
        if d is None:
            continue
        buckets[c.CrimeMajorHeadID][f"{d.year:04d}-{d.month:02d}"] += 1
    out = []
    for head_id, months in buckets.items():
        pts = [{"month": k, "count": v} for k, v in sorted(months.items())][-12:]
        out.append({"crime_head": heads.get(head_id, f"Head {head_id}"), "points": pts})
    return out


@router.get("/overview/trends")
def get_crime_trend(db: Session = Depends(get_db)) -> dict:
    return {"trends": _trends(db)}
