"""
Case surface — LUMEN_MASTER_SPEC_V3 §29.1, served from the canonical §3.5
schema and the precomputed `lumen_` tables.

  GET /cases                  — filters: head, sub-head, gravity, status,
                                category, district, unit, date range, `q`
                                full-text; §29.2 total + limit/offset
  GET /cases/{id}             — "full aggregate in semantic form"
  GET /cases/{id}/timeline    — "derived lifecycle with gaps and district
                                benchmarks" (§2.1 ProcessEvents, §2.3 labels)
  GET /cases/{id}/insights    — the case's §8 Insights
  GET /cases/{id}/linked      — ranked linked cases (§13 case_linkage)
  GET /cases/{id}/graph       — investigation-board payload (§14)

§4.2 identity masking is applied through `governance.masking` on every
participant name and on `BriefFacts`; §8 invariant 1 keeps numeric scores
inside Insights, so these rows carry the derived BAND only.
"""
from __future__ import annotations

from statistics import median

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from lumen.db.session import get_db
from lumen.db.models import canonical as m
from lumen.governance import masking
from lumen.db.models.intelligence import LumenInsight
from lumen.db.models.quality import LumenQualityScore

router = APIRouter(prefix="/cases", tags=["Cases"])

_NO_MODEL = (
    "No backing tables exist for this surface in the canonical schema (§3.5) "
    "or the platform tables (§3.6); it stays 501 until its subsystem is specified."
)

# ── helpers ──────────────────────────────────────────────────────────────

_BAND_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _risk_by_case(db: Session, case_ids: list[int]) -> dict[str, dict]:
    """kind='risk' insights keyed by case subject_id (§8: scores live in insights)."""
    if not case_ids:
        return {}
    rows = (
        db.query(LumenInsight)
        .filter(
            LumenInsight.kind == "risk",
            LumenInsight.subject_type == "case",
            LumenInsight.subject_id.in_([str(c) for c in case_ids]),
        )
        .all()
    )
    out: dict[str, dict] = {}
    for r in rows:
        band = None
        score = r.score
        if score is not None:
            band = "critical" if score >= 0.8 else "high" if score >= 0.6 else "medium" if score >= 0.4 else "low"
        out[r.subject_id] = {"band": band, "score": score, "confidence": r.confidence}
    return out


def _insight_counts(db: Session, case_ids: list[int]) -> dict[str, int]:
    if not case_ids:
        return {}
    rows = (
        db.query(LumenInsight.subject_id, func.count())
        .filter(
            LumenInsight.subject_type == "case",
            LumenInsight.subject_id.in_([str(c) for c in case_ids]),
        )
        .group_by(LumenInsight.subject_id)
        .all()
    )
    return {sid: n for sid, n in rows}


def _district_quality(db: Session) -> dict[str, float]:
    """Mean of the six §5.2 dimensions per district scope."""
    rows = (
        db.query(LumenQualityScore.scope_id, func.avg(LumenQualityScore.score))
        .filter(LumenQualityScore.scope_type == "district")
        .group_by(LumenQualityScore.scope_id)
        .all()
    )
    return {sid: float(avg) for sid, avg in rows if avg is not None}


def _lookups(db: Session):
    heads = {h.CrimeHeadID: h.CrimeGroupName for h in db.query(m.CrimeHead).all()}
    subheads = {s.CrimeSubHeadID: (s.CrimeHeadID, s.CrimeHeadName) for s in db.query(m.CrimeSubHead).all()}
    gravities = {g.GravityOffenceID: g.LookupValue for g in db.query(m.GravityOffence).all()}
    statuses = {s.CaseStatusID: s.CaseStatusName for s in db.query(m.CaseStatusMaster).all()}
    units = {u.UnitID: u for u in db.query(m.Unit).all()}
    districts = {d.DistrictID: d.DistrictName for d in db.query(m.District).all()}
    employees = {e.EmployeeID: e for e in db.query(m.Employee).all()}
    ranks = {r.RankID: r.RankName for r in db.query(m.Rank).all()}
    return heads, subheads, gravities, statuses, units, districts, employees, ranks


def _officer_name(emp: m.Employee | None, ranks: dict) -> str | None:
    if emp is None:
        return None
    rank = ranks.get(emp.RankID)
    short = "PSI" if rank == "Police Sub-Inspector" else (rank or "")
    return f"{short} {emp.FirstName}".strip()


def _list_item(case: m.CaseMaster, lk, risk: dict, counts: dict, dq: dict) -> dict:
    heads, subheads, gravities, statuses, units, districts, employees, ranks = lk
    unit = units.get(case.PoliceStationID)
    district_id = unit.DistrictID if unit else None
    r = risk.get(str(case.CaseMasterID), {})
    sub = subheads.get(case.CrimeMinorHeadID)
    return {
        "case_master_id": str(case.CaseMasterID),
        "crime_no": case.CrimeNo,
        "title": heads.get(case.CrimeMajorHeadID, "Case"),
        "crime_type": {
            "head_id": str(case.CrimeMajorHeadID or ""),
            "head_name": heads.get(case.CrimeMajorHeadID, "—"),
            "sub_head_id": str(case.CrimeMinorHeadID) if case.CrimeMinorHeadID else None,
            "sub_head_name": sub[1] if sub else None,
        },
        "gravity": {"id": str(case.GravityOffenceID or ""), "name": gravities.get(case.GravityOffenceID, "—")},
        "status": {"id": str(case.CaseStatusID or ""), "name": statuses.get(case.CaseStatusID, "—")},
        "district_name": districts.get(district_id, "—"),
        "station_name": unit.UnitName if unit else "—",
        "officer_name": _officer_name(employees.get(case.PolicePersonID), ranks),
        "crime_registered_date": case.CrimeRegisteredDate.isoformat() if case.CrimeRegisteredDate else None,
        "updated_at": None,  # no audit column on CaseMaster (§3.5) — honest null
        # §8 invariant 1: no endpoint returns a score outside an Insight. The
        # case surfaces carry the derived BAND; the numeric risk score,
        # confidence and §5.2 quality score are read from the case's Insights
        # (`/intelligence/workbench?subject_type=case`) and `/quality/scores`.
        "risk_band": r.get("band"),
        "insight_count": counts.get(str(case.CaseMasterID), 0),
        "classification": "CONFIDENTIAL",  # §4.2 asset register: CaseMaster
    }


_SORTABLE = {
    "crime_no": m.CaseMaster.CrimeNo,
    "crime_registered_date": m.CaseMaster.CrimeRegisteredDate,
    "updated_at": m.CaseMaster.CrimeRegisteredDate,
    "status": m.CaseMaster.CaseStatusID,
    "gravity": m.CaseMaster.GravityOffenceID,
    "title": m.CaseMaster.CrimeMajorHeadID,
}


@router.get("")
def list_cases(
    q: str | None = Query(default=None),
    crime_head: str | None = None,
    crime_sub_head: str | None = None,
    gravity: str | None = None,
    status: str | None = None,
    category: str | None = None,
    district: str | None = None,
    station: str | None = None,
    risk_band: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sort: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(m.CaseMaster)

    if q:
        query = query.filter(or_(m.CaseMaster.CrimeNo.ilike(f"%{q}%"), m.CaseMaster.BriefFacts.ilike(f"%{q}%")))
    if crime_head and crime_head.isdigit():
        query = query.filter(m.CaseMaster.CrimeMajorHeadID == int(crime_head))
    if crime_sub_head and crime_sub_head.isdigit():
        query = query.filter(m.CaseMaster.CrimeMinorHeadID == int(crime_sub_head))
    if gravity and gravity.isdigit():
        query = query.filter(m.CaseMaster.GravityOffenceID == int(gravity))
    if status and status.isdigit():
        query = query.filter(m.CaseMaster.CaseStatusID == int(status))
    if category and category.isdigit():
        query = query.filter(m.CaseMaster.CaseCategoryID == int(category))
    if station and station.isdigit():
        query = query.filter(m.CaseMaster.PoliceStationID == int(station))
    if district and district.isdigit():
        unit_ids = [u.UnitID for u in db.query(m.Unit).filter(m.Unit.DistrictID == int(district)).all()]
        query = query.filter(m.CaseMaster.PoliceStationID.in_(unit_ids or [-1]))
    if date_from:
        query = query.filter(m.CaseMaster.CrimeRegisteredDate >= date_from)
    if date_to:
        query = query.filter(m.CaseMaster.CrimeRegisteredDate <= date_to)

    # Multi-sort "field:dir,field:dir" over the sortable columns; unknown
    # fields (risk/confidence/quality — derived, not columns) are ignored here
    # and handled below for the risk_band filter case.
    if sort:
        for token in sort.split(","):
            field, _, direction = token.partition(":")
            col = _SORTABLE.get(field.strip())
            if col is not None:
                query = query.order_by(col.desc() if direction == "desc" else col.asc())
    else:
        query = query.order_by(m.CaseMaster.CrimeRegisteredDate.desc())

    total = query.count()
    rows = query.offset(offset).limit(limit).all()

    lk = _lookups(db)
    ids = [c.CaseMasterID for c in rows]
    risk = _risk_by_case(db, ids)
    counts = _insight_counts(db, ids)
    dq = _district_quality(db)

    items = [_list_item(c, lk, risk, counts, dq) for c in rows]
    if risk_band:
        items = [i for i in items if i["risk_band"] == risk_band]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{case_id}/timeline")
def case_timeline(case_id: int, db: Session = Depends(get_db)) -> dict:
    case = db.get(m.CaseMaster, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    _, _, _, _, units, districts, employees, ranks = _lookups(db)
    unit = units.get(case.PoliceStationID)
    station = unit.UnitName if unit else "station unknown"
    io = _officer_name(employees.get(case.PolicePersonID), ranks) or "IO unknown"

    def label(kind: str, when) -> str:
        d = when.strftime("%d %b %Y") if when else "date unknown"
        return f"{kind} · {d} · {station} · IO {io}"   # §2.3 render form

    events: list[dict] = []

    def add(kind: str, when, extra: dict | None = None) -> None:
        events.append({
            "event_id": f"{case_id}:{kind}:{len(events)}",
            "kind": kind,
            "occurred_at": when.isoformat() if when else None,
            "label": label(kind.replace("_", " ").title(), when),
            "station_name": station,
            "io_display_name": io,
            "chargesheet_type": (extra or {}).get("cstype"),
            "entity_url": None,
            **(extra or {}),
        })

    add("incident", case.IncidentFromDate)
    add("info_received", case.InfoReceivedPSDate)
    add("registered", case.CrimeRegisteredDate)
    for arr in db.query(m.ArrestSurrender).filter(m.ArrestSurrender.CaseMasterID == case_id).all():
        add("arrest", arr.ArrestSurrenderDate)
    for cs in db.query(m.ChargesheetDetails).filter(m.ChargesheetDetails.CaseMasterID == case_id).all():
        add("chargesheet", cs.csdate, {"cstype": cs.cstype})

    events = [e for e in events if e["occurred_at"] is not None]
    events.sort(key=lambda e: e["occurred_at"])

    # District median: registered → chargesheet gap across the district (§30.4).
    med = None
    if unit:
        unit_ids = [u.UnitID for u in units.values() if u.DistrictID == unit.DistrictID]
        gaps = []
        for c, cs in (
            db.query(m.CaseMaster, m.ChargesheetDetails)
            .join(m.ChargesheetDetails, m.ChargesheetDetails.CaseMasterID == m.CaseMaster.CaseMasterID)
            .filter(m.CaseMaster.PoliceStationID.in_(unit_ids))
            .all()
        ):
            if c.CrimeRegisteredDate and cs.csdate:
                # csdate is DATETIME, CrimeRegisteredDate is DATE (§3.5) —
                # normalise both to date before subtracting.
                cs_day = cs.csdate.date() if hasattr(cs.csdate, "date") else cs.csdate
                gaps.append((cs_day - c.CrimeRegisteredDate).days)
        if gaps:
            med = int(median(gaps))

    return {"events": events, "district_median_days": med}


@router.get("/{case_id}")
def get_case(
    case_id: int,
    viewer_role: str = Query(
        default="station_officer",
        description="§20.1 role of the caller; drives §4.2 identity masking. "
                    "The deployed binding is Catalyst Authentication → lumen_user_role.",
    ),
    db: Session = Depends(get_db),
) -> dict:
    case = db.get(m.CaseMaster, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    lk = _lookups(db)
    heads, subheads, gravities, statuses, units, districts, employees, ranks = lk
    unit = units.get(case.PoliceStationID)
    district_id = unit.DistrictID if unit else None
    risk = _risk_by_case(db, [case_id]).get(str(case_id), {})
    dq = _district_quality(db)

    officers = []
    reg = employees.get(case.PolicePersonID)
    if reg is not None:
        officers.append({
            "employee_id": str(reg.EmployeeID),
            "display_name": _officer_name(reg, ranks) or f"Employee {reg.EmployeeID}",
            "rank_short_name": "PSI" if ranks.get(reg.RankID) == "Police Sub-Inspector" else ranks.get(reg.RankID),
            "station_name": unit.UnitName if unit else None,
            "role": "investigating",
        })

    # §4.2 identity masking, applied through the ONE governance module — the
    # response never carries an unmasked name the viewer's role may not see
    # (§20.2 "Build identity masking even though it is T2").
    try:
        role = viewer_role if viewer_role in ("state_analyst", "district_sp",
                                              "investigating_officer", "station_officer") else "station_officer"
    except Exception:  # pragma: no cover — defensive
        role = "station_officer"

    participants = []
    for a in db.query(m.Accused).filter(m.Accused.CaseMasterID == case_id).order_by(m.Accused.AccusedMasterID).all():
        raw = a.AccusedName or "(unnamed)"
        shown = masking.mask_accused_name(raw, role)
        participants.append({
            "role": "accused",
            "label": a.PersonID or f"A{len(participants) + 1}",   # §3.2 fact 2: ordering label
            "display_name": shown if shown != "A1" else f"{a.PersonID or 'A1'} (masked)",
            "masked": shown != raw,
            "person_id": None,
        })
    for v in db.query(m.Victim).filter(m.Victim.CaseMasterID == case_id).all():
        raw = v.VictimName or "(unnamed)"
        shown = masking.mask_victim_name(raw, role)
        label = f"V{sum(1 for p in participants if p['role'] == 'victim') + 1}"
        participants.append({
            "role": "victim",
            "label": label,
            "display_name": shown if shown != "V1" else f"{label} (masked)",
            "masked": shown != raw,
            "person_id": None,
        })
    for c in db.query(m.ComplainantDetails).filter(m.ComplainantDetails.CaseMasterID == case_id).all():
        raw = c.ComplainantName or "(unnamed)"
        shown = masking.mask_complainant_name(raw, role)
        label = f"C{sum(1 for p in participants if p['role'] == 'complainant') + 1}"
        participants.append({
            "role": "complainant",
            "label": label,
            "display_name": shown if shown != "C1" else f"{label} (masked)",
            "masked": shown != raw,
            "person_id": None,
        })

    sections = {(s.ActCode, s.SectionCode): s.SectionDescription for s in db.query(m.Section).all()}
    charges = [
        {
            "act_short_name": a.ActID,
            "section_id": a.SectionID,
            "section_description": sections.get((a.ActID, a.SectionID)),
        }
        for a in db.query(m.ActSectionAssociation)
        .filter(m.ActSectionAssociation.CaseMasterID == case_id)
        .order_by(m.ActSectionAssociation.ActOrderID)
        .all()
    ]

    sub = subheads.get(case.CrimeMinorHeadID)
    return {
        "case_master_id": str(case.CaseMasterID),
        "crime_no": case.CrimeNo,
        "title": heads.get(case.CrimeMajorHeadID, "Case"),
        "crime_type": {
            "head_id": str(case.CrimeMajorHeadID or ""),
            "head_name": heads.get(case.CrimeMajorHeadID, "—"),
            "sub_head_id": str(case.CrimeMinorHeadID) if case.CrimeMinorHeadID else None,
            "sub_head_name": sub[1] if sub else None,
        },
        "gravity": {"id": str(case.GravityOffenceID or ""), "name": gravities.get(case.GravityOffenceID, "—")},
        "status": {"id": str(case.CaseStatusID or ""), "name": statuses.get(case.CaseStatusID, "—")},
        "classification": "CONFIDENTIAL",
        "station": {
            "unit_id": str(case.PoliceStationID or ""),
            "unit_name": unit.UnitName if unit else "—",
            "district_id": str(district_id or ""),
            "district_name": districts.get(district_id, "—"),
        },
        "court": None,  # no Court rows in the seed; honest null
        "officers": officers,
        "participants": participants,
        "charges": charges,
        "crime_registered_date": case.CrimeRegisteredDate.isoformat() if case.CrimeRegisteredDate else None,
        "incident_from_date": case.IncidentFromDate.isoformat() if case.IncidentFromDate else None,
        "incident_to_date": case.IncidentToDate.isoformat() if case.IncidentToDate else None,
        "info_received_ps_date": case.InfoReceivedPSDate.isoformat() if case.InfoReceivedPSDate else None,
        "updated_at": None,
        "brief_facts": (
            case.BriefFacts
            if role in ("state_analyst", "district_sp") or not case.BriefFacts
            else (case.BriefFacts[:80] + "… (truncated — below District SP, §4.2)")
        ),
        "latitude": float(case.latitude) if case.latitude is not None else None,
        "longitude": float(case.longitude) if case.longitude is not None else None,
        # §8 invariant 1 — band only; numerics live in Insights / the quality surface.
        "risk_band": risk.get("band"),
    }


@router.get("/{case_id}/insights")
def case_insights(case_id: int, db: Session = Depends(get_db)) -> dict:
    """§29.1 — the §8 Insights whose subject is this case."""
    from lumen.api.routers.insights import serialize as _ser
    if db.get(m.CaseMaster, case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    rows = (
        db.query(LumenInsight)
        .filter(LumenInsight.subject_type == "case",
                LumenInsight.subject_id == str(case_id))
        .order_by(LumenInsight.generated_at.desc())
        .all()
    )
    return {"insights": [_ser(r) for r in rows], "total": len(rows)}


@router.get("/{case_id}/linked")
def case_linked(case_id: int, db: Session = Depends(get_db)) -> dict:
    """§29.1 linked cases — the §13 case_linkage Insights for this case, each
    naming the shared entities in its evidence (never a bare similarity score:
    §8 invariant 1)."""
    from lumen.api.routers.insights import serialize as _ser
    if db.get(m.CaseMaster, case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    rows = (
        db.query(LumenInsight)
        .filter(LumenInsight.kind == "linkage",
                LumenInsight.subject_type == "case",
                LumenInsight.subject_id == str(case_id))
        .order_by(LumenInsight.generated_at.desc())
        .all()
    )
    return {"linked": [_ser(r) for r in rows], "total": len(rows)}
