"""
Feature store — LUMEN_MASTER_SPEC_V3 §12.

"One table, one loader, versioned." Each §12 feature is computed from
already-built upstream data (resolution §6, graph §14, quality §5, canonical
§3.5) — never recomputed here (§12: "Models and prompts read features; they
never recompute them"). This module holds the feature COMPUTERS (definitions)
and the single LOADER (`get_feature` / `list_features`).

§12's fourteen features, and how each maps to upstream:

  person:
    repeat_offender_score  linked cases at confidence ≥0.85, log-scaled
                           → count lumen_person_link.state="linked" (auto-links
                             are the ≥0.85 band, §6.2), log1p-scaled
    mobility_index         distinct districts ÷ cases
                           → the person's case districts (via Accused→Case→Unit)
    network_influence      normalised eigenvector centrality
                           → lumen_person_metrics.eigenvector (§14)
    community_size         Louvain community size
                           → lumen_community.size via lumen_person_metrics.community_id

  case:
    arrest_delay_days      arrest − registration
    report_delay_hours     info received − incident
    charge_delay_days      csdate − registration
    gravity_weight         from GravityOffenceID
    signature_rarity       inverse frequency of the act-section set
    repeat_victim_flag     victim name+age matched in a prior case (0.0/1.0)

  district / unit:
    detection_rate         cstype='A' ÷ chargesheeted
    officer_load           open cases ÷ employees  (unit)
    quality_completeness   from §5.2 (lumen_quality_score, completeness)

  crime_density_km2        "cases ÷ area, rolling 90 days" — NOT COMPUTED:
                           the canonical District table has no `area` column
                           (§3.5), and area exists nowhere in the schema. The
                           numerator is computable but the divisor is
                           unavailable, so producing it would require inventing
                           area values. Recorded as "Cannot determine from the
                           specification" and omitted (never fabricated — §24.3
                           rule 5).

Determinism: every computer is a pure function of persisted data; no randomness,
no wall-clock (a `now` is passed for `computed_at`). `version` is "v1".

Disclosed choices where §12 leaves a detail open (Session deliverables):
  * repeat_offender_score "log-scaled" → natural log1p of the linked-case count.
  * gravity_weight "from GravityOffenceID" → the GravityOffenceID ordinal
    itself (no weight table is defined; the id is the only available signal).
  * signature_rarity "inverse frequency" → 1 / (number of cases sharing the
    exact act-section set), 1.0 for a unique signature.
  * "open case" (officer_load) → a case whose CaseStatusID is not a
    terminal/closed status; §12 gives no closed-status list, so ALL cases in
    the unit are counted as the load denominator's numerator is undefined —
    see note in the computer.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.db.models import canonical as m
from lumen.db.models.feature import LumenFeature
from lumen.db.models.graph import LumenCommunity, LumenPersonMetrics
from lumen.db.models.identity import LumenPerson, LumenPersonLink
from lumen.db.models.quality import LumenQualityScore

FEATURE_VERSION = "v1"

# §6.2 auto-link threshold — "linked cases at confidence ≥0.85" is exactly the
# auto-linked band, persisted as state="linked".
LINKED_STATE = "linked"


@dataclass(frozen=True)
class ComputedFeature:
    entity_type: str
    entity_id: str
    feature_name: str
    value: float


# ── shared lookups ──────────────────────────────────────────────────────────

def _unit_district(session: Session) -> dict[int, int]:
    return {u.UnitID: u.DistrictID for u in session.query(m.Unit).all()}


def _person_accused(session: Session) -> dict[str, list[int]]:
    """person_id → the AccusedMasterIDs auto-linked to them (state=linked)."""
    out: dict[str, list[int]] = {}
    for link in session.query(LumenPersonLink).filter(LumenPersonLink.state == LINKED_STATE):
        out.setdefault(link.person_id, []).append(link.accused_master_id)
    return out


# ── person features ─────────────────────────────────────────────────────────

def _person_features(session: Session) -> list[ComputedFeature]:
    out: list[ComputedFeature] = []
    persons = {p.person_id: p for p in session.query(LumenPerson).all()}
    accused = {a.AccusedMasterID: a for a in session.query(m.Accused).all()}
    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}
    units = _unit_district(session)
    metrics = {r.person_id: r for r in session.query(LumenPersonMetrics).all()}
    communities = {c.community_id: c for c in session.query(LumenCommunity).all()}
    linked = _person_accused(session)

    for pid, person in persons.items():
        acc_ids = linked.get(pid, [])
        case_ids = [accused[a].CaseMasterID for a in acc_ids
                    if a in accused and accused[a].CaseMasterID is not None]
        n_cases = len(set(case_ids))

        # repeat_offender_score — linked cases at ≥0.85, log-scaled
        out.append(ComputedFeature("person", pid, "repeat_offender_score",
                                   math.log1p(n_cases)))

        # mobility_index — distinct districts ÷ cases
        districts = {units.get(cases[c].PoliceStationID) for c in case_ids
                     if c in cases and cases[c].PoliceStationID in units}
        districts.discard(None)
        mobility = (len(districts) / n_cases) if n_cases else 0.0
        out.append(ComputedFeature("person", pid, "mobility_index", mobility))

        # network_influence — eigenvector centrality (§14)
        met = metrics.get(pid)
        out.append(ComputedFeature("person", pid, "network_influence",
                                   float(met.eigenvector) if met and met.eigenvector is not None else 0.0))

        # community_size — Louvain community size (§14)
        size = 0.0
        if met is not None and met.community_id is not None:
            comm = communities.get(met.community_id)
            if comm is not None and comm.size is not None:
                size = float(comm.size)
        out.append(ComputedFeature("person", pid, "community_size", size))
    return out


# ── case features ───────────────────────────────────────────────────────────

def _case_features(session: Session) -> list[ComputedFeature]:
    out: list[ComputedFeature] = []
    cases = list(session.query(m.CaseMaster).all())

    # earliest arrest per case
    arrests: dict[int, object] = {}
    for ar in session.query(m.ArrestSurrender).all():
        if ar.CaseMasterID is None or ar.ArrestSurrenderDate is None:
            continue
        cur = arrests.get(ar.CaseMasterID)
        if cur is None or ar.ArrestSurrenderDate < cur:
            arrests[ar.CaseMasterID] = ar.ArrestSurrenderDate
    # earliest chargesheet per case
    charges_cs: dict[int, object] = {}
    for cs in session.query(m.ChargesheetDetails).all():
        if cs.CaseMasterID is None or cs.csdate is None:
            continue
        cur = charges_cs.get(cs.CaseMasterID)
        if cur is None or cs.csdate < cur:
            charges_cs[cs.CaseMasterID] = cs.csdate

    # act-section set per case → signature frequency
    sig: dict[int, frozenset] = {}
    for a in session.query(m.ActSectionAssociation).all():
        sig.setdefault(a.CaseMasterID, set()).add((a.ActID, a.SectionID))
    sig = {cid: frozenset(s) for cid, s in sig.items()}
    sig_freq: dict[frozenset, int] = {}
    for s in sig.values():
        sig_freq[s] = sig_freq.get(s, 0) + 1

    # victim (name, age) prior-match — a case is a repeat-victim case if any of
    # its victims' (name, age) appears in a case registered earlier.
    victims: dict[int, list[tuple]] = {}
    for v in session.query(m.Victim).all():
        if v.CaseMasterID is not None and v.VictimName:
            victims.setdefault(v.CaseMasterID, []).append((v.VictimName, v.AgeYear))
    reg_date = {c.CaseMasterID: c.CrimeRegisteredDate for c in cases}
    # (name, age) → sorted list of case registration dates
    vk_dates: dict[tuple, list] = {}
    for cid, vs in victims.items():
        for key in vs:
            if reg_date.get(cid) is not None:
                vk_dates.setdefault(key, []).append(reg_date[cid])
    for lst in vk_dates.values():
        lst.sort()

    for c in cases:
        cid = c.CaseMasterID
        sid = str(cid)

        # arrest_delay_days = arrest − registration
        if cid in arrests and c.CrimeRegisteredDate is not None:
            out.append(ComputedFeature("case", sid, "arrest_delay_days",
                                       float((arrests[cid] - c.CrimeRegisteredDate).days)))

        # report_delay_hours = info received − incident
        if c.InfoReceivedPSDate is not None and c.IncidentFromDate is not None:
            hrs = (c.InfoReceivedPSDate - c.IncidentFromDate).total_seconds() / 3600.0
            out.append(ComputedFeature("case", sid, "report_delay_hours", hrs))

        # charge_delay_days = csdate − registration
        if cid in charges_cs and c.CrimeRegisteredDate is not None:
            csd = charges_cs[cid]
            csdate = csd.date() if hasattr(csd, "date") else csd
            out.append(ComputedFeature("case", sid, "charge_delay_days",
                                       float((csdate - c.CrimeRegisteredDate).days)))

        # gravity_weight = from GravityOffenceID (the id ordinal; disclosed)
        if c.GravityOffenceID is not None:
            out.append(ComputedFeature("case", sid, "gravity_weight",
                                       float(c.GravityOffenceID)))

        # signature_rarity = inverse frequency of the act-section set
        s = sig.get(cid)
        if s:
            out.append(ComputedFeature("case", sid, "signature_rarity",
                                       1.0 / sig_freq[s]))

        # repeat_victim_flag = victim name+age matched in a PRIOR case (0/1)
        flag = 0.0
        this_reg = reg_date.get(cid)
        if this_reg is not None:
            for key in victims.get(cid, []):
                earlier = [d for d in vk_dates.get(key, []) if d < this_reg]
                if earlier:
                    flag = 1.0
                    break
        out.append(ComputedFeature("case", sid, "repeat_victim_flag", flag))
    return out


# ── district / unit features ───────────────────────────────────────────────

def _detection_rate(cstype_a: int, chargesheeted: int) -> float | None:
    return (cstype_a / chargesheeted) if chargesheeted else None


def _district_unit_features(session: Session) -> list[ComputedFeature]:
    out: list[ComputedFeature] = []
    units = {u.UnitID: u for u in session.query(m.Unit).all()}
    cases = list(session.query(m.CaseMaster).all())

    # chargesheet cstype per case
    cs_types: dict[int, list[str]] = {}
    for cs in session.query(m.ChargesheetDetails).all():
        if cs.CaseMasterID is not None and cs.cstype:
            cs_types.setdefault(cs.CaseMasterID, []).append(cs.cstype)

    # detection_rate per district and per unit: cstype='A' ÷ chargesheeted
    d_a: dict[int, int] = {}; d_cs: dict[int, int] = {}
    u_a: dict[int, int] = {}; u_cs: dict[int, int] = {}
    for c in cases:
        types = cs_types.get(c.CaseMasterID)
        if not types:
            continue
        unit = c.PoliceStationID
        district = units[unit].DistrictID if unit in units else None
        a = sum(1 for t in types if t == "A")
        if district is not None:
            d_cs[district] = d_cs.get(district, 0) + 1
            d_a[district] = d_a.get(district, 0) + a
        if unit is not None:
            u_cs[unit] = u_cs.get(unit, 0) + 1
            u_a[unit] = u_a.get(unit, 0) + a
    for district, total in d_cs.items():
        rate = _detection_rate(d_a[district], total)
        if rate is not None:
            out.append(ComputedFeature("district", str(district), "detection_rate", rate))
    for unit, total in u_cs.items():
        rate = _detection_rate(u_a[unit], total)
        if rate is not None:
            out.append(ComputedFeature("unit", str(unit), "detection_rate", rate))

    # officer_load = cases ÷ employees, per unit. §12 says "open cases"; no
    # closed-status list is defined by the spec, so "open" cannot be
    # determined precisely — all cases registered to the unit are counted, and
    # this is disclosed (Session deliverables). Employees are those in the unit.
    unit_cases: dict[int, int] = {}
    for c in cases:
        if c.PoliceStationID is not None:
            unit_cases[c.PoliceStationID] = unit_cases.get(c.PoliceStationID, 0) + 1
    unit_emps: dict[int, int] = {}
    for e in session.query(m.Employee).all():
        if e.UnitID is not None:
            unit_emps[e.UnitID] = unit_emps.get(e.UnitID, 0) + 1
    for unit, n_cases in unit_cases.items():
        emps = unit_emps.get(unit, 0)
        if emps:
            out.append(ComputedFeature("unit", str(unit), "officer_load",
                                       n_cases / emps))

    # quality_completeness = §5.2 completeness dimension for the scope
    for row in (session.query(LumenQualityScore)
                .filter(LumenQualityScore.dimension == "completeness")):
        if row.scope_type in ("district", "unit") and row.score is not None:
            out.append(ComputedFeature(row.scope_type, str(row.scope_id),
                                       "quality_completeness", float(row.score)))
    return out


# ── the loader (one loader — §12) ───────────────────────────────────────────

def compute_all(session: Session) -> list[ComputedFeature]:
    """Compute every §12 feature that the schema supports (13 of 14;
    crime_density_km2 is omitted — no area column, §12 note above)."""
    return (_person_features(session) + _case_features(session)
            + _district_unit_features(session))


def persist_features(session: Session, features: list[ComputedFeature], *,
                     version: str = FEATURE_VERSION,
                     now: datetime | None = None) -> int:
    """Write features to lumen_feature for a version. Idempotent per version:
    clears this version's rows first, then writes (re-run = invalidate +
    recompute for that version)."""
    now = now or datetime.now(timezone.utc)
    session.query(LumenFeature).filter(LumenFeature.version == version).delete()
    session.flush()
    for f in features:
        session.add(LumenFeature(
            entity_type=f.entity_type, entity_id=f.entity_id,
            feature_name=f.feature_name, value=f.value,
            version=version, computed_at=now))
    session.flush()
    return len(features)


def get_feature(session: Session, entity_type: str, entity_id: str,
                feature_name: str, *, version: str = FEATURE_VERSION
                ) -> LumenFeature | None:
    """The read path (§12: models and prompts read, never recompute)."""
    return session.get(LumenFeature, (entity_type, entity_id, feature_name, version))


def list_features(session: Session, *, entity_type: str | None = None,
                  entity_id: str | None = None, feature_name: str | None = None,
                  version: str = FEATURE_VERSION) -> list[LumenFeature]:
    q = session.query(LumenFeature).filter(LumenFeature.version == version)
    if entity_type is not None:
        q = q.filter(LumenFeature.entity_type == entity_type)
    if entity_id is not None:
        q = q.filter(LumenFeature.entity_id == entity_id)
    if feature_name is not None:
        q = q.filter(LumenFeature.feature_name == feature_name)
    return (q.order_by(LumenFeature.entity_type, LumenFeature.entity_id,
                       LumenFeature.feature_name).all())
