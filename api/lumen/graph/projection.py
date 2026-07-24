"""
Graph projection pipeline — LUMEN_MASTER_SPEC_V3 §14.5.

    Data Store → resolve persons (§6) → structural edges → derived edges
      → metrics (degree, betweenness, eigenvector, Louvain)
      → write lumen_graph_edge / lumen_person_metrics / lumen_community
      → snapshot to NoSQL → warm Cache for top-N ego graphs → emit GraphProjected

"Nothing here runs per request." This module is the batch step; queries
(queries.py) read only what it wrote.

Session 9 scope covers the pipeline through the three §3.6 table writes. The
last three arrows are other sessions' subsystems and are deliberately NOT
implemented here: NoSQL snapshot and Cache warm are Catalyst adoption
(§26.1 rows 6-7 — Session 21), `GraphProjected` is a §19.2 domain event
(Session 12's bus). Same deferral pattern Sessions 7/8 used for their events.

Person resolution (§6): a graph Person node is a resolved `lumen_person`
where an auto-link exists (link state "linked"); every other Accused row —
including members of 0.65–0.85 candidate pairs, which are "surfaced, never
auto-merged" (§6.2) — participates as its own singleton person identity with
node id "accused:<AccusedMasterID>". ADR-003 records that without resolution
"the network graph has no edge longer than one case": within-case co-accusal
edges always exist; auto-linked resolution is what extends reach across cases.

Node ids are semantic (§14.2 "semantic entities, never table rows"):
  person   → lumen_person UUID, or "accused:<id>" singleton
  case     → str(CaseMasterID)
  officer  → str(EmployeeID)
  station  → str(UnitID)
  jurisdiction → "district:<DistrictID>" / "state:<StateID>"
  court    → str(CourtID)
  charge   → "<ActID>:<SectionID>" (per §2.1 Charge identity: act+section,
             rendered "IPC 302" — one node per charge, shared by cases)

Edge weights: §14.3 defines none explicitly. CO_ACCUSED_WITH carries the
shared-case count as weight because Q5 ("Repeat co-offender pairs — edge-
weight rank") requires the weight to encode co-offending frequency;
SHARES_SIGNATURE carries its jaccard. All other edges use neutral 1.0 —
recorded as an implementation note, not a spec value.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from itertools import combinations

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.db.models.graph import LumenCommunity, LumenGraphEdge, LumenPersonMetrics
from lumen.db.models.identity import LumenPerson, LumenPersonLink
from lumen.db.models.intelligence import LumenModelRegistry
from lumen.graph import metrics as graph_metrics

logger = logging.getLogger("lumen")

# §14.3 derived-edge thresholds — verbatim.
SIGNATURE_JACCARD_MIN = 0.6      # SHARES_SIGNATURE: Jaccard ≥ 0.6, different units
PROXIMATE_KM_MAX = 5.0           # PROXIMATE_TO: ≤ 5 km
PROXIMATE_DAYS_MAX = 14          # PROXIMATE_TO: ≤ 14 days, same major head

# The projection method registered so §8 invariant 5 can hold for the
# insights the ten queries produce (lineage.model_version must exist in
# lumen_model_registry).
METHOD_NAME = "graph_projection"
METHOD_VERSION = "v1"


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance (standard haversine)."""
    r = 6371.0088
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = p2 - p1
    dl = math.radians(float(lng2) - float(lng1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def resolve_person_nodes(session: Session) -> dict[int, str]:
    """§14.5 'resolve persons (§6)': AccusedMasterID → semantic person node id.
    Auto-linked accused (link state 'linked') share their lumen_person UUID;
    everyone else is a singleton 'accused:<id>' (candidates never merge, §6.2)."""
    linked: dict[int, str] = {}
    for link in session.query(LumenPersonLink).filter(LumenPersonLink.state == "linked"):
        linked[link.accused_master_id] = link.person_id
    mapping: dict[int, str] = {}
    for acc in session.query(m.Accused).all():
        mapping[acc.AccusedMasterID] = linked.get(
            acc.AccusedMasterID, f"accused:{acc.AccusedMasterID}"
        )
    return mapping


def run_projection(session: Session, *, now: datetime | None = None) -> dict:
    """Project the graph and persist it. Re-runnable: clears the three graph
    tables first (never canonical, never other lumen_ tables). Returns a
    summary dict for the caller/logs."""
    now = now or datetime.now(timezone.utc)

    session.query(LumenGraphEdge).delete()
    session.query(LumenPersonMetrics).delete()
    session.query(LumenCommunity).delete()
    session.flush()

    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}
    units = {u.UnitID: u for u in session.query(m.Unit).all()}
    person_of = resolve_person_nodes(session)
    accused_rows = session.query(m.Accused).all()

    edges: dict[tuple, dict] = {}   # (src_type,src_id,dst_type,dst_id,rel) -> {weight,props}

    def add(src_type, src_id, dst_type, dst_id, rel, *, weight=1.0, props=None):
        key = (src_type, str(src_id), dst_type, str(dst_id), rel)
        edges[key] = {"weight": weight, "props": props or {}}

    # ── structural edges (§14.3 — from foreign keys) ──────────────────────
    case_persons: dict[int, set[str]] = {}          # case → person nodes
    person_case_districts: dict[str, set[int]] = {} # person → case districts
    person_cases: dict[str, set[int]] = {}          # person → case ids

    for acc in accused_rows:
        if acc.CaseMasterID not in cases:
            continue
        p = person_of[acc.AccusedMasterID]
        add("person", p, "case", acc.CaseMasterID, "ACCUSED_IN")
        case_persons.setdefault(acc.CaseMasterID, set()).add(p)
        person_cases.setdefault(p, set()).add(acc.CaseMasterID)
        unit = units.get(cases[acc.CaseMasterID].PoliceStationID)
        if unit is not None and unit.DistrictID is not None:
            person_case_districts.setdefault(p, set()).add(unit.DistrictID)

    for c in cases.values():
        if c.PoliceStationID is not None:
            add("case", c.CaseMasterID, "station", c.PoliceStationID, "REGISTERED_AT")
            unit = units.get(c.PoliceStationID)
            if unit is not None and unit.DistrictID is not None:
                add("station", c.PoliceStationID, "jurisdiction",
                    f"district:{unit.DistrictID}", "IN")
        if c.PolicePersonID is not None:
            add("officer", c.PolicePersonID, "case", c.CaseMasterID, "REGISTERED")
        if c.CourtID is not None:
            add("case", c.CaseMasterID, "court", c.CourtID, "TRIED_AT")

    charge_sets: dict[int, set[tuple[str, str]]] = {}
    for a in session.query(m.ActSectionAssociation).all():
        if a.CaseMasterID in cases:
            add("case", a.CaseMasterID, "charge", f"{a.ActID}:{a.SectionID}", "CHARGED_UNDER")
            charge_sets.setdefault(a.CaseMasterID, set()).add((a.ActID, a.SectionID))

    person_arrest_districts: dict[str, set[int]] = {}
    person_ios: dict[str, set[int]] = {}
    arrest_count: dict[tuple[str, int], int] = {}   # (person, district) → arrests
    for ar in session.query(m.ArrestSurrender).all():
        acc_id = ar.AccusedMasterID
        if acc_id is None or acc_id not in person_of:
            continue
        p = person_of[acc_id]
        if ar.CaseMasterID in cases and ar.IOID is not None:
            add("officer", ar.IOID, "case", ar.CaseMasterID, "INVESTIGATED")
            person_ios.setdefault(p, set()).add(ar.IOID)
        if ar.ArrestSurrenderDistrictId is not None:
            add("person", p, "jurisdiction",
                f"district:{ar.ArrestSurrenderDistrictId}", "ARRESTED_IN")
            person_arrest_districts.setdefault(p, set()).add(ar.ArrestSurrenderDistrictId)
            arrest_count[(p, ar.ArrestSurrenderDistrictId)] = \
                arrest_count.get((p, ar.ArrestSurrenderDistrictId), 0) + 1

    # ── derived edges (§14.3 table — verbatim derivations) ────────────────

    # CO_ACCUSED_WITH {cases,first,last,districts}: shared CaseMasterID after
    # resolution. weight = shared-case count (Q5 edge-weight rank).
    co: dict[tuple[str, str], dict] = {}
    for cid, persons in case_persons.items():
        case = cases[cid]
        d = case.CrimeRegisteredDate.isoformat() if case.CrimeRegisteredDate else None
        unit = units.get(case.PoliceStationID)
        district = unit.DistrictID if unit is not None else None
        for a, b in combinations(sorted(persons), 2):
            rec = co.setdefault((a, b), {"cases": 0, "first": None, "last": None, "districts": set()})
            rec["cases"] += 1
            if d is not None:
                rec["first"] = d if rec["first"] is None else min(rec["first"], d)
                rec["last"] = d if rec["last"] is None else max(rec["last"], d)
            if district is not None:
                rec["districts"].add(district)
    for (a, b), rec in co.items():
        add("person", a, "person", b, "CO_ACCUSED_WITH", weight=float(rec["cases"]),
            props={"cases": rec["cases"], "first": rec["first"], "last": rec["last"],
                   "districts": sorted(rec["districts"])})

    # SHARES_SIGNATURE {jaccard}: Jaccard ≥ 0.6 on act-section sets, different units.
    sig_cases = sorted(charge_sets)
    for i in range(len(sig_cases)):
        for j in range(i + 1, len(sig_cases)):
            ca, cb = sig_cases[i], sig_cases[j]
            if cases[ca].PoliceStationID == cases[cb].PoliceStationID:
                continue                      # different units required
            sa, sb = charge_sets[ca], charge_sets[cb]
            inter = len(sa & sb)
            union = len(sa | sb)
            if union == 0:
                continue
            jac = inter / union
            if jac >= SIGNATURE_JACCARD_MIN:
                add("case", ca, "case", cb, "SHARES_SIGNATURE",
                    weight=jac, props={"jaccard": round(jac, 4)})

    # OPERATES_IN {cases,arrests}: union of case and arrest districts.
    for p in set(person_case_districts) | set(person_arrest_districts):
        for d in person_case_districts.get(p, set()) | person_arrest_districts.get(p, set()):
            n_cases = sum(
                1 for cid in person_cases.get(p, set())
                if (u := units.get(cases[cid].PoliceStationID)) is not None
                and u.DistrictID == d
            )
            add("person", p, "jurisdiction", f"district:{d}", "OPERATES_IN",
                props={"cases": n_cases, "arrests": arrest_count.get((p, d), 0)})

    # PROXIMATE_TO {km,days}: ≤5 km, ≤14 days, same major head.
    geo_cases = [c for c in cases.values()
                 if c.latitude is not None and c.longitude is not None
                 and c.CrimeRegisteredDate is not None]
    for ca, cb in combinations(sorted(geo_cases, key=lambda c: c.CaseMasterID), 2):
        if ca.CrimeMajorHeadID != cb.CrimeMajorHeadID:
            continue
        days = abs((ca.CrimeRegisteredDate - cb.CrimeRegisteredDate).days)
        if days > PROXIMATE_DAYS_MAX:
            continue
        km = _haversine_km(ca.latitude, ca.longitude, cb.latitude, cb.longitude)
        if km <= PROXIMATE_KM_MAX:
            add("case", ca.CaseMasterID, "case", cb.CaseMasterID, "PROXIMATE_TO",
                props={"km": round(km, 3), "days": days})

    # SAME_IO_AS: shared IOID (caveated as a workload artefact, not guilt).
    io_persons: dict[int, set[str]] = {}
    for p, ios in person_ios.items():
        for io in ios:
            io_persons.setdefault(io, set()).add(p)
    for io, persons in io_persons.items():
        for a, b in combinations(sorted(persons), 2):
            add("person", a, "person", b, "SAME_IO_AS")

    # ── persist edges ─────────────────────────────────────────────────────
    for (src_type, src_id, dst_type, dst_id, rel), attrs in edges.items():
        session.add(LumenGraphEdge(
            src_type=src_type, src_id=src_id, dst_type=dst_type, dst_id=dst_id,
            rel=rel, weight=attrs["weight"], props=attrs["props"], computed_at=now,
        ))
    session.flush()

    # ── metrics (§14.5: degree, betweenness, eigenvector, Louvain) ────────
    summary_metrics = graph_metrics.compute_and_persist(session, now=now)

    # Register the projection method so query insights satisfy §8 invariant 5.
    session.merge(LumenModelRegistry(
        model_id=f"{METHOD_NAME}@{METHOD_VERSION}", name=METHOD_NAME,
        kind="graph", version=METHOD_VERSION, params={}, metrics={},
        trained_at=now, active=True,
    ))

    session.commit()
    summary = {"edges": len(edges), **summary_metrics}
    logger.info("§14 graph projection complete: %s", summary)
    return summary
