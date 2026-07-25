"""
Deterministic demo-data seed — LUMEN_MASTER_SPEC_V3 §32.

`jobs/seed.py`, fixed random seed, guaranteeing by construction the twelve
demo-path properties in §32. This is Session 5 of §33 ("Seed job", done
when "All twelve guarantees verified by tests").

Design notes:
  - Seeds the canonical §3.5 schema only (models in `db/models/canonical.py`).
    The `lumen_` platform tables (§3.6) belong to later sessions and are
    not touched here; nothing in §32's twelve guarantees requires a
    `lumen_` table (person resolution, communities, hotspot clusters, and
    identity candidates are demanded as *raw seed shapes the later
    subsystems will detect*, not as pre-computed `lumen_` rows).
  - Fixed seed (`settings.SEED_RANDOM`, default 42) drives the small amount
    of filler variation; the twelve guaranteed structures are built by hand
    with fixed IDs, so IDs are identical on every run regardless of the RNG.
  - Every ID a demo or test needs is returned in `SeedManifest`, and the
    same manifest is written to `docs/DEMO_SCRIPT.md` (§32: "Record
    demo-path entity IDs").
  - Idempotent: a second call on an already-seeded DB is a no-op and returns
    the manifest reconstructed from the fixed constants.

CrimeNo encoding (§3.2 fact 4): 1 category + 4 district + 4 unit + 4 year +
5 serial = 18 digits. Category 1 = FIR (§3.2/§31.3). `encode_crime_no`
builds a valid one; guarantee 8 deliberately builds one whose embedded
unit disagrees with its registering `Unit`, for Q04.
"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import date, datetime

from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.db.models import canonical as m

logger = logging.getLogger("lumen")

# ── Karnataka bounding box (for guarantee 7 / §5.1 Q02 "inside real
# Karnataka boundaries"). Karnataka spans roughly 11.5–18.5°N, 74–78.6°E.
KARNATAKA_LAT = (11.5, 18.5)
KARNATAKA_LNG = (74.0, 78.6)

DEMO_YEAR = 2026


def encode_crime_no(category: int, district_id: int, unit_id: int, year: int, serial: int) -> str:
    """§3.2 fact 4 — 1 category + 4 district + 4 unit + 4 year + 5 serial."""
    return f"{category:1d}{district_id:04d}{unit_id:04d}{year:04d}{serial:05d}"


@dataclass
class SeedManifest:
    """Every demo-path ID §32 asks to be recorded, keyed by guarantee.
    Written verbatim into docs/DEMO_SCRIPT.md and asserted by the tests."""

    seed_random: int = 0
    # g1
    hotspot_district_id: int = 0
    hotspot_case_ids: list[int] = field(default_factory=list)
    # g2
    community_person_labels: list[str] = field(default_factory=list)
    community_district_ids: list[int] = field(default_factory=list)
    community_broker_label: str = ""
    community_accused_ids: list[int] = field(default_factory=list)
    # g3
    name_variant_persons: dict = field(default_factory=dict)  # canonical name -> [accused_master_id...]
    # g4
    shared_signature_case_ids: list[int] = field(default_factory=list)
    shared_signature: list[str] = field(default_factory=list)  # [ActID, SectionID]
    # g5
    lifecycle_case_id: int = 0
    lifecycle_charge_delay_days: int = 0
    # g6
    spike_district_id: int = 0
    spike_week_start: str = ""
    spike_case_ids: list[int] = field(default_factory=list)
    # g8
    crimeno_unit_mismatch_case_id: int = 0
    crimeno_unit_mismatch_crime_no: str = ""
    # g9
    missing_coords_case_id: int = 0
    impossible_timestamp_case_id: int = 0
    # g10
    cstype_distribution: dict = field(default_factory=dict)
    # g11
    low_confidence_candidate: dict = field(default_factory=dict)  # {personA, personB, confidence}
    # g12
    masking_divergent_case_ids: list[int] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def seed_database(session: Session) -> SeedManifest:
    """Deterministically seed the canonical schema per §32. Returns the
    demo-path manifest. Idempotent."""
    manifest = SeedManifest(seed_random=settings.SEED_RANDOM)

    if session.query(m.CaseMaster).count():
        logger.info("Seed skipped — CaseMaster already populated.")
        return _rebuild_manifest_constants(manifest)

    random.seed(settings.SEED_RANDOM)

    _seed_reference_data(session)
    session.flush()

    _seed_guarantees(session, manifest)
    session.commit()

    logger.info("§32 deterministic demo seed complete.")
    return manifest


# ══════════════════════════════════════════════════════════════════════
# Reference / lookup data — the fixed spine the guarantees hang off.
# ══════════════════════════════════════════════════════════════════════

# Two real Karnataka districts (guarantee 2 needs ≥2). Fixed IDs.
DISTRICTS = {
    1: ("Bengaluru Urban", (12.9716, 77.5946)),
    2: ("Mysuru", (12.2958, 76.6394)),
    3: ("Mangaluru", (12.9141, 74.8560)),
}
STATE_ID = 1
# Units (police stations). Fixed IDs; each belongs to a district.
UNITS = {
    11: ("Whitefield PS", 1),
    12: ("Koramangala PS", 1),
    21: ("Devaraja PS", 2),
    31: ("Mangaluru North PS", 3),
}
# Legal spine
ACTS = {"IPC": "Indian Penal Code"}
SECTIONS = {
    ("IPC", "302"): "Punishment for murder",
    ("IPC", "392"): "Punishment for robbery",
    ("IPC", "420"): "Cheating and dishonestly inducing delivery of property",
}
CRIME_HEADS = {1: "Violent Crime", 2: "Property Crime"}
CRIME_SUBHEADS = {11: (1, "Murder"), 21: (2, "Robbery")}
CASE_STATUS = {1: "Under Investigation", 2: "Chargesheeted", 3: "Closed"}
CASE_CATEGORY = {1: "FIR"}
GRAVITY = {1: "Heinous", 2: "Non-Heinous"}


def _seed_reference_data(session: Session) -> None:
    # STAGED FLUSHES (FK-ordering fix): with FK-only models and no
    # relationship() config, the unit of work flushes unrelated mappers in
    # table-name order — "District" sorts before "State" and violates the FK
    # under PostgreSQL (SQLite unit tests don't enforce FKs, so they never saw
    # it). Each dependency level is therefore flushed before the next level
    # references it. Seed-time cost is negligible.

    # Level 0 — no intra-seed FK dependencies.
    session.add(m.State(StateID=STATE_ID, StateName="Karnataka", Active=True))
    session.add(m.UnitType(UnitTypeID=1, UnitTypeName="Police Station", Active=True))
    session.add(m.Rank(RankID=1, RankName="Police Sub-Inspector", Hierarchy=3, Active=True))
    session.add(m.Designation(DesignationID=1, DesignationName="Investigating Officer", Active=True, SortOrder=1))
    for code, desc in ACTS.items():
        session.add(m.Act(ActCode=code, ActDescription=desc, ShortName=code, Active=True))
    for hid, name in CRIME_HEADS.items():
        session.add(m.CrimeHead(CrimeHeadID=hid, CrimeGroupName=name, Active=True))
    for sid, name in CASE_STATUS.items():
        session.add(m.CaseStatusMaster(CaseStatusID=sid, CaseStatusName=name))
    for cid, name in CASE_CATEGORY.items():
        session.add(m.CaseCategory(CaseCategoryID=cid, LookupValue=name))
    for gid, name in GRAVITY.items():
        session.add(m.GravityOffence(GravityOffenceID=gid, LookupValue=name))
    # P9 lookups exist so foreign keys resolve; never analysed (§4.2 / P9).
    session.add(m.ReligionMaster(ReligionID=1, ReligionName="Religion-1"))
    session.add(m.CasteMaster(caste_master_id=1, caste_master_name="Caste-1"))
    session.add(m.OccupationMaster(OccupationID=1, OccupationName="Occupation-1"))
    session.flush()

    # Level 1 — references level 0 (State, Act, CrimeHead).
    for did, (name, _) in DISTRICTS.items():
        session.add(m.District(DistrictID=did, DistrictName=name, StateID=STATE_ID, Active=True))
    for (act, sec), desc in SECTIONS.items():
        session.add(m.Section(ActCode=act, SectionCode=sec, SectionDescription=desc, Active=True))
    for shid, (hid, name) in CRIME_SUBHEADS.items():
        session.add(m.CrimeSubHead(CrimeSubHeadID=shid, CrimeHeadID=hid, CrimeHeadName=name, SeqID=shid))
    session.flush()

    # Level 2 — references District/UnitType.
    for uid, (name, did) in UNITS.items():
        session.add(m.Unit(UnitID=uid, UnitName=name, TypeID=1, StateID=STATE_ID, DistrictID=did, Active=True))
    session.flush()

    # Level 3 — references District/Unit/Rank/Designation.
    # One IO per unit, fixed EmployeeIDs = unit_id + 1000.
    for uid, (_, did) in UNITS.items():
        session.add(
            m.Employee(
                EmployeeID=1000 + uid, DistrictID=did, UnitID=uid, RankID=1, DesignationID=1,
                KGID=f"KGID{1000 + uid}", FirstName=f"IO{uid}", GenderID=1,
                AppointmentDate=date(2018, 1, 1),
            )
        )
    session.flush()


def _io_for(unit_id: int) -> int:
    return 1000 + unit_id


def _add_case(
    session: Session, *, case_id: int, district_id: int, unit_id: int, serial: int,
    status_id: int = 1, head_id: int = 1, subhead_id: int = 11, gravity_id: int = 1,
    registered: date | None = None, incident: datetime | None = None,
    info_received: datetime | None = None, lat: float | None = None, lng: float | None = None,
    brief: str = "Seeded demo case.", crime_no: str | None = None,
) -> m.CaseMaster:
    if crime_no is None:
        crime_no = encode_crime_no(1, district_id, unit_id, DEMO_YEAR, serial)
    case = m.CaseMaster(
        CaseMasterID=case_id, CrimeNo=crime_no, CaseNo=f"CN{case_id}",
        CrimeRegisteredDate=registered or date(DEMO_YEAR, 1, 1),
        PolicePersonID=_io_for(unit_id), PoliceStationID=unit_id,
        CaseCategoryID=1, GravityOffenceID=gravity_id,
        CrimeMajorHeadID=head_id, CrimeMinorHeadID=subhead_id,
        CaseStatusID=status_id, IncidentFromDate=incident,
        InfoReceivedPSDate=info_received, latitude=lat, longitude=lng, BriefFacts=brief,
    )
    session.add(case)
    # FK-ordering fix (see _seed_reference_data): children ("Accused",
    # "ActSectionAssociation", …) sort alphabetically BEFORE "CaseMaster" in an
    # unrelated-mapper flush, so the parent must be flushed before any child a
    # guarantee-builder adds next.
    session.flush()
    return case


def _add_accused(session: Session, *, accused_id: int, case_id: int, name: str, person_label: str, age: int = 30) -> None:
    session.add(
        m.Accused(AccusedMasterID=accused_id, CaseMasterID=case_id, AccusedName=name,
                  AgeYear=age, GenderID=1, PersonID=person_label)
    )


def _add_charge(session: Session, *, case_id: int, act: str, section: str, order: int = 1) -> None:
    session.add(
        m.ActSectionAssociation(CaseMasterID=case_id, ActID=act, SectionID=section,
                                ActOrderID=order, SectionOrderID=order)
    )


# ══════════════════════════════════════════════════════════════════════
# The twelve guarantees, built by construction with fixed IDs.
# ══════════════════════════════════════════════════════════════════════

def _seed_guarantees(session: Session, man: SeedManifest) -> None:
    _g1_hotspot(session, man)
    _g2_community(session, man)
    _g3_name_variants(session, man)
    _g4_shared_signature(session, man)
    _g5_lifecycle_charge_delay(session, man)
    _g6_spike(session, man)
    # g7 (valid coords + correct CrimeNo) is satisfied by every case above/below
    # using encode_crime_no and Karnataka-boundary coordinates; recorded implicitly.
    _g8_crimeno_unit_mismatch(session, man)
    _g9_missing_coords_and_impossible_timestamp(session, man)
    _g10_cstype_distribution(session, man)
    _g11_low_confidence_candidate(session, man)
    _g12_masking_divergence(session, man)


def _g1_hotspot(session: Session, man: SeedManifest) -> None:
    """Guarantee 1: a district with a visually obvious hotspot — many cases
    clustered within a few hundred metres in district 1 (Bengaluru Urban)."""
    man.hotspot_district_id = 1
    base_lat, base_lng = 12.9716, 77.5946
    for i in range(10):
        cid = 1000 + i
        lat = base_lat + (i % 5) * 0.0008  # ~<500m spread
        lng = base_lng + (i // 5) * 0.0008
        _add_case(session, case_id=cid, district_id=1, unit_id=11, serial=100 + i, lat=lat, lng=lng,
                  brief="Hotspot cluster case.")
        man.hotspot_case_ids.append(cid)


def _g2_community(session: Session, man: SeedManifest) -> None:
    """Guarantee 2: a resolved community of ≥8 persons spanning ≥2 districts
    with exactly one high-betweenness broker.

    Built as raw co-accusal shape (shared CaseMasterIDs) so §6 resolution +
    §14 graph will detect it — not pre-computed into lumen_ tables.
    Structure: two clusters (district 1 and district 2), joined only through
    one broker person who co-appears in a case with a member of each cluster.
    """
    man.community_district_ids = [1, 2]
    man.community_broker_label = "P-BROKER"
    # Cluster A (district 1): persons A1..A4 co-accused in case 2000.
    _add_case(session, case_id=2000, district_id=1, unit_id=11, serial=200, lat=12.98, lng=77.60)
    for idx, label in enumerate(["P-A1", "P-A2", "P-A3", "P-A4"], start=1):
        aid = 2000 + idx
        _add_accused(session, accused_id=aid, case_id=2000, name=f"Cluster A Person {idx}", person_label=f"A{idx}")
        man.community_accused_ids.append(aid)
        man.community_person_labels.append(label)
    # Cluster B (district 2): persons B1..B4 co-accused in case 2100.
    _add_case(session, case_id=2100, district_id=2, unit_id=21, serial=210, lat=12.30, lng=76.64)
    for idx, label in enumerate(["P-B1", "P-B2", "P-B3", "P-B4"], start=1):
        aid = 2100 + idx
        _add_accused(session, accused_id=aid, case_id=2100, name=f"Cluster B Person {idx}", person_label=f"A{idx}")
        man.community_accused_ids.append(aid)
        man.community_person_labels.append(label)
    # Broker: co-accused with A1 (case 2200) and B1 (case 2210) — the only
    # path between the two clusters, so betweenness centrality peaks on it.
    _add_case(session, case_id=2200, district_id=1, unit_id=11, serial=220, lat=12.99, lng=77.61)
    _add_accused(session, accused_id=2201, case_id=2200, name="Broker Person", person_label="A1")
    _add_accused(session, accused_id=2202, case_id=2200, name="Cluster A Person 1", person_label="A2")
    _add_case(session, case_id=2210, district_id=2, unit_id=21, serial=221, lat=12.31, lng=76.65)
    _add_accused(session, accused_id=2211, case_id=2210, name="Broker Person", person_label="A1")
    _add_accused(session, accused_id=2212, case_id=2210, name="Cluster B Person 1", person_label="A2")
    man.community_accused_ids += [2201, 2202, 2211, 2212]
    man.community_person_labels.append("P-BROKER")  # ≥8 distinct persons total (4+4+broker)


def _g3_name_variants(session: Session, man: SeedManifest) -> None:
    """Guarantee 3: ≥3 persons appearing in ≥3 cases each under name variants
    (so resolution does real work, not exact-string matching)."""
    variant_people = {
        "Ravi Kumar": ["Ravi Kumar", "Ravikumar", "Ravi Kumr"],
        "Sunil Rao": ["Sunil Rao", "Suneel Rao", "Sunil Raoo"],
        "Anil Shetty": ["Anil Shetty", "Aneel Shetty", "Anil Shety"],
    }
    next_case = 3000
    next_accused = 3000
    for canonical_name, variants in variant_people.items():
        ids = []
        for i, variant in enumerate(variants):
            _add_case(session, case_id=next_case, district_id=1, unit_id=11, serial=300 + next_case % 1000,
                      lat=12.97 + i * 0.001, lng=77.59 + i * 0.001, brief="Name-variant case.")
            _add_accused(session, accused_id=next_accused, case_id=next_case, name=variant, person_label="A1")
            ids.append(next_accused)
            next_case += 1
            next_accused += 1
        man.name_variant_persons[canonical_name] = ids


def _g4_shared_signature(session: Session, man: SeedManifest) -> None:
    """Guarantee 4: two cases sharing an act-section signature, different
    districts, months apart."""
    signature = [("IPC", "392"), ("IPC", "420")]
    man.shared_signature = ["IPC 392", "IPC 420"]
    # Case in district 1, January.
    _add_case(session, case_id=4000, district_id=1, unit_id=11, serial=400,
              registered=date(DEMO_YEAR, 1, 15), lat=12.97, lng=77.60, head_id=2, subhead_id=21)
    # Case in district 3, May (months apart, different district).
    _add_case(session, case_id=4001, district_id=3, unit_id=31, serial=401,
              registered=date(DEMO_YEAR, 5, 20), lat=12.91, lng=74.85, head_id=2, subhead_id=21)
    for cid in (4000, 4001):
        for order, (act, sec) in enumerate(signature, start=1):
            _add_charge(session, case_id=cid, act=act, section=sec, order=order)
        man.shared_signature_case_ids.append(cid)


def _g5_lifecycle_charge_delay(session: Session, man: SeedManifest) -> None:
    """Guarantee 5: a full-lifecycle case with a conspicuous charge delay
    (incident → info → registered → arrest → chargesheet), chargesheet filed
    long after registration."""
    case_id = 5000
    registered = date(DEMO_YEAR, 1, 10)
    _add_case(
        session, case_id=case_id, district_id=1, unit_id=11, serial=500, status_id=2,
        registered=registered, incident=datetime(DEMO_YEAR, 1, 5, 9, 0),
        info_received=datetime(DEMO_YEAR, 1, 6, 10, 0), lat=12.9718, lng=77.5948,
        brief="Full-lifecycle case with a nine-month charge delay.",
    )
    _add_accused(session, accused_id=5001, case_id=case_id, name="Lifecycle Accused", person_label="A1")
    # Arrest
    session.add(
        m.ArrestSurrender(
            ArrestSurrenderID=5000, CaseMasterID=case_id, ArrestSurrenderTypeID=1,
            ArrestSurrenderDate=date(DEMO_YEAR, 1, 20), ArrestSurrenderStateId=STATE_ID,
            ArrestSurrenderDistrictId=1, PoliceStationID=11, IOID=_io_for(11),
            AccusedMasterID=5001, IsAccused=True, IsComplainantAccused=False,
        )
    )
    session.add(m.InvArrestSurrenderAccused(ArrestSurrenderID=5000, AccusedMasterID=5001))
    # Chargesheet — filed ~9 months after registration (conspicuous delay).
    csdate = datetime(DEMO_YEAR, 10, 15, 12, 0)
    session.add(
        m.ChargesheetDetails(CSID=5000, CaseMasterID=case_id, csdate=csdate, cstype="A", PolicePersonID=_io_for(11))
    )
    man.lifecycle_case_id = case_id
    man.lifecycle_charge_delay_days = (csdate.date() - registered).days


def _g6_spike(session: Session, man: SeedManifest) -> None:
    """Guarantee 6: a district-week ≥3σ above baseline. District 2 gets one
    week with far more registrations than its steady baseline weeks."""
    man.spike_district_id = 2
    cid = 6000
    # Baseline: 12 weeks with 1 case each (mean≈1, low variance).
    for wk in range(12):
        reg = date(DEMO_YEAR, 1, 1)
        reg = date(DEMO_YEAR, 1 + wk // 4, 1 + (wk % 4) * 7)
        _add_case(session, case_id=cid, district_id=2, unit_id=21, serial=600 + wk,
                  registered=reg, lat=12.29, lng=76.63, brief="Baseline-week case.")
        cid += 1
    # Spike week: 15 cases in one week — a >3σ outlier against the baseline.
    spike_start = date(DEMO_YEAR, 6, 1)
    man.spike_week_start = spike_start.isoformat()
    for i in range(15):
        _add_case(session, case_id=cid, district_id=2, unit_id=21, serial=650 + i,
                  registered=spike_start, lat=12.30, lng=76.64, brief="Spike-week case.")
        man.spike_case_ids.append(cid)
        cid += 1


def _g8_crimeno_unit_mismatch(session: Session, man: SeedManifest) -> None:
    """Guarantee 8: one deliberate CrimeNo/Unit mismatch so Q04 has something
    to catch. Registered to unit 11, but its CrimeNo embeds unit 12."""
    case_id = 8000
    bad_crime_no = encode_crime_no(1, 1, 12, DEMO_YEAR, 800)  # embeds unit 12
    _add_case(session, case_id=case_id, district_id=1, unit_id=11, serial=800,
              crime_no=bad_crime_no, lat=12.97, lng=77.60,
              brief="CrimeNo encodes unit 0012 but is registered to unit 0011.")
    man.crimeno_unit_mismatch_case_id = case_id
    man.crimeno_unit_mismatch_crime_no = bad_crime_no


def _g9_missing_coords_and_impossible_timestamp(session: Session, man: SeedManifest) -> None:
    """Guarantee 9: one case with missing coordinates (Q01) and one with an
    impossible timestamp — incident after registration (Q05)."""
    # Missing coordinates.
    _add_case(session, case_id=9000, district_id=1, unit_id=11, serial=900,
              lat=None, lng=None, brief="Case with missing coordinates (Q01).")
    man.missing_coords_case_id = 9000
    # Impossible timestamp: incident dated AFTER registration (Q05).
    _add_case(
        session, case_id=9001, district_id=1, unit_id=11, serial=901,
        registered=date(DEMO_YEAR, 3, 1), incident=datetime(DEMO_YEAR, 4, 1, 8, 0),
        lat=12.97, lng=77.59, brief="Incident dated after registration (Q05).",
    )
    man.impossible_timestamp_case_id = 9001


def _g10_cstype_distribution(session: Session, man: SeedManifest) -> None:
    """Guarantee 10: a realistic cstype A/B/C distribution for the outcome
    model. A=chargesheet, B=false, C=undetected (§3.2 fact 6)."""
    # Realistic skew: mostly A, fewer B, some C.
    plan = [("A", 12), ("B", 3), ("C", 5)]
    cid = 10000
    csid = 10000
    for cstype, n in plan:
        for _ in range(n):
            _add_case(session, case_id=cid, district_id=1, unit_id=11, serial=cid % 100000,
                      status_id=2, registered=date(DEMO_YEAR, 2, 1), lat=12.97, lng=77.59,
                      brief=f"Outcome-distribution case (cstype {cstype}).")
            session.add(
                m.ChargesheetDetails(CSID=csid, CaseMasterID=cid,
                                     csdate=datetime(DEMO_YEAR, 4, 1, 10, 0), cstype=cstype,
                                     PolicePersonID=_io_for(11))
            )
            cid += 1
            csid += 1
    man.cstype_distribution = {t: n for t, n in plan}


def _g11_low_confidence_candidate(session: Session, man: SeedManifest) -> None:
    """Guarantee 11: one low-confidence identity candidate (0.66–0.75) so the
    candidate-match UI is demonstrable.

    Built as two Accused rows that are a *near* match (same phonetic name,
    close age, but different district and no shared co-accused) — the raw
    shape §6 scores into the 0.66–0.75 candidate band. The intended
    confidence is recorded in the manifest so §6 tuning and the test can
    target it; no lumen_person_link row is written here (that is §6/Session
    7's output, not seed input).
    """
    _add_case(session, case_id=11000, district_id=1, unit_id=11, serial=1100, lat=12.97, lng=77.59)
    _add_accused(session, accused_id=11001, case_id=11000, name="Mohammed Ali", person_label="A1", age=41)
    _add_case(session, case_id=11001, district_id=3, unit_id=31, serial=1101, lat=12.91, lng=74.85)
    _add_accused(session, accused_id=11002, case_id=11001, name="Mohammad Ali", person_label="A1", age=43)
    man.low_confidence_candidate = {
        "person_a_accused_id": 11001,
        "person_b_accused_id": 11002,
        "intended_confidence": 0.70,
        "confidence_band": [0.66, 0.75],
    }


def _g12_masking_divergence(session: Session, man: SeedManifest) -> None:
    """Guarantee 12: ≥5 cases whose scope masking differs between a Station
    Officer and a District SP. Any case with a Victim or Accused name diverges
    (Victim/Accused names mask below District SP / Investigating Officer per
    §4.2). Five such cases in district 1 with named victims and accused."""
    cid = 12000
    vid = 12000
    aid = 12000
    for i in range(5):
        _add_case(session, case_id=cid, district_id=1, unit_id=11, serial=1200 + i, lat=12.97, lng=77.59,
                  brief="Masking-divergence case (named victim + accused).")
        session.add(m.Victim(VictimMasterID=vid, CaseMasterID=cid, VictimName=f"Victim {i}",
                             AgeYear=25 + i, GenderID=1, VictimPolice="0"))
        _add_accused(session, accused_id=aid, case_id=cid, name=f"Accused {i}", person_label="A1")
        man.masking_divergent_case_ids.append(cid)
        cid += 1
        vid += 1
        aid += 1


# ══════════════════════════════════════════════════════════════════════
# Idempotent re-entry — rebuild the manifest from the fixed constants
# without touching the DB (IDs are deterministic, so this always matches).
# ══════════════════════════════════════════════════════════════════════

def _rebuild_manifest_constants(man: SeedManifest) -> SeedManifest:
    """Reconstruct the manifest from the same fixed constants a fresh seed
    would produce, so a second (idempotent) call still returns identical IDs.
    Runs the guarantee builders against a throwaway in-memory recorder rather
    than the live session."""
    recorder = _NullSession()
    _seed_guarantees(recorder, man)
    return man


class _NullSession:
    """Swallows .add() so the guarantee builders can populate the manifest
    without writing rows (used on the idempotent no-op path)."""

    def add(self, _obj):  # noqa: D401
        return None

    def flush(self):
        return None
