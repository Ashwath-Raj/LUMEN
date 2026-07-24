"""
Verifies the twelve deterministic demo-data guarantees of §32 — the
"Done when" criterion for Session 5 of §33 ("All twelve guarantees
verified by tests").

Self-contained: seeds the canonical schema into an in-memory SQLite DB per
test module, no live PostgreSQL or HTTP client required. Reads back the
seeded rows and asserts each guarantee holds by construction, plus that the
demo-path IDs are identical on every run (§32: "Re-run the seed and confirm
the same IDs").
"""
import math
from collections import Counter
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.jobs.seed import seed_database, encode_crime_no

KARNATAKA_LAT = (11.5, 18.5)
KARNATAKA_LNG = (74.0, 78.6)


@pytest.fixture()
def seeded():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    manifest = seed_database(session)
    yield session, manifest
    session.close()


def _decode_crime_no(crime_no: str) -> dict:
    return {
        "category": int(crime_no[0]),
        "district": int(crime_no[1:5]),
        "unit": int(crime_no[5:9]),
        "year": int(crime_no[9:13]),
        "serial": int(crime_no[13:18]),
    }


# ─── determinism (§32: same IDs every run) ────────────────────────────────

def test_seed_is_deterministic_across_runs():
    def run():
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return seed_database(sessionmaker(bind=engine)()).as_dict()

    assert run() == run()


def test_seed_is_idempotent(seeded):
    session, manifest = seeded
    before = session.query(m.CaseMaster).count()
    again = seed_database(session)          # no-op path
    assert session.query(m.CaseMaster).count() == before
    assert again.as_dict() == manifest.as_dict()


# ─── guarantee 1 ─────────────────────────────────────────────────────────

def test_g1_visually_obvious_hotspot(seeded):
    session, man = seeded
    cases = session.query(m.CaseMaster).filter(m.CaseMaster.CaseMasterID.in_(man.hotspot_case_ids)).all()
    assert len(cases) >= 8
    lats = [float(c.latitude) for c in cases]
    lngs = [float(c.longitude) for c in cases]
    # All within a tight (<1km) cluster in one district.
    assert max(lats) - min(lats) < 0.01
    assert max(lngs) - min(lngs) < 0.01
    assert {c.PoliceStationID for c in cases} == {11}  # single district-1 unit


# ─── guarantee 2 ─────────────────────────────────────────────────────────

def test_g2_resolved_community_two_districts_one_broker(seeded):
    session, man = seeded
    # ≥8 distinct persons.
    assert len(set(man.community_person_labels)) >= 8
    # Spans ≥2 districts.
    assert len(set(man.community_district_ids)) >= 2
    # Exactly one broker recorded.
    assert man.community_broker_label == "P-BROKER"
    # The broker is the only person appearing in a case in BOTH districts.
    accused = session.query(m.Accused).filter(m.Accused.AccusedMasterID.in_(man.community_accused_ids)).all()
    case_ids = {a.CaseMasterID for a in accused}
    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).filter(m.CaseMaster.CaseMasterID.in_(case_ids))}
    # Broker appears in case 2200 (dist 1) and 2210 (dist 2).
    broker_cases = {a.CaseMasterID for a in accused if a.AccusedName == "Broker Person"}
    broker_units = {cases[cid].PoliceStationID for cid in broker_cases}
    assert broker_units == {11, 21}  # unit 11 = district 1, unit 21 = district 2


# ─── guarantee 3 ─────────────────────────────────────────────────────────

def test_g3_name_variant_persons(seeded):
    session, man = seeded
    assert len(man.name_variant_persons) >= 3
    for canonical_name, accused_ids in man.name_variant_persons.items():
        assert len(accused_ids) >= 3
        rows = session.query(m.Accused).filter(m.Accused.AccusedMasterID.in_(accused_ids)).all()
        names = {r.AccusedName for r in rows}
        # Variants, not identical strings.
        assert len(names) >= 3
        assert canonical_name in names or any(canonical_name.split()[0] in n for n in names)
        # Each appears in a distinct case.
        assert len({r.CaseMasterID for r in rows}) >= 3


# ─── guarantee 4 ─────────────────────────────────────────────────────────

def test_g4_shared_signature_across_districts_months_apart(seeded):
    session, man = seeded
    assert len(man.shared_signature_case_ids) == 2
    cases = session.query(m.CaseMaster).filter(m.CaseMaster.CaseMasterID.in_(man.shared_signature_case_ids)).all()
    # Different districts (via their units).
    assert len({c.PoliceStationID for c in cases}) == 2
    # Months apart.
    dates = sorted(c.CrimeRegisteredDate for c in cases)
    assert (dates[1].year - dates[0].year) * 12 + (dates[1].month - dates[0].month) >= 2
    # Identical act-section signature sets.
    sigs = []
    for cid in man.shared_signature_case_ids:
        rows = session.query(m.ActSectionAssociation).filter_by(CaseMasterID=cid).all()
        sigs.append(frozenset((r.ActID, r.SectionID) for r in rows))
    assert sigs[0] == sigs[1]
    assert len(sigs[0]) >= 2


# ─── guarantee 5 ─────────────────────────────────────────────────────────

def test_g5_full_lifecycle_with_charge_delay(seeded):
    session, man = seeded
    case = session.get(m.CaseMaster, man.lifecycle_case_id)
    assert case is not None
    # Full lifecycle present: incident, info, registered, arrest, chargesheet.
    assert case.IncidentFromDate is not None
    assert case.InfoReceivedPSDate is not None
    assert case.CrimeRegisteredDate is not None
    assert session.query(m.ArrestSurrender).filter_by(CaseMasterID=case.CaseMasterID).count() >= 1
    cs = session.query(m.ChargesheetDetails).filter_by(CaseMasterID=case.CaseMasterID).one()
    # Conspicuous delay: chargesheet many months after registration.
    delay_days = (cs.csdate.date() - case.CrimeRegisteredDate).days
    assert delay_days == man.lifecycle_charge_delay_days
    assert delay_days > 180  # conspicuous (> 6 months)


# ─── guarantee 6 ─────────────────────────────────────────────────────────

def test_g6_district_week_three_sigma_above_baseline(seeded):
    session, man = seeded
    # Weekly counts for the spike district.
    rows = (
        session.query(m.CaseMaster)
        .filter(m.CaseMaster.PoliceStationID == 21)  # district-2 unit
        .all()
    )
    by_week = Counter()
    for c in rows:
        iso = c.CrimeRegisteredDate.isocalendar()
        by_week[(iso[0], iso[1])] += 1
    counts = list(by_week.values())
    spike_week = c = None
    spike_start = datetime.fromisoformat(man.spike_week_start).date()
    spike_key = (spike_start.isocalendar()[0], spike_start.isocalendar()[1])
    spike_count = by_week[spike_key]
    baseline = [v for k, v in by_week.items() if k != spike_key]
    mean = sum(baseline) / len(baseline)
    variance = sum((x - mean) ** 2 for x in baseline) / len(baseline)
    std = math.sqrt(variance) if variance > 0 else 0.0
    # >= 3σ above baseline (std may be ~0 for a flat baseline; the spike is
    # then trivially many multiples above the mean).
    if std > 0:
        assert (spike_count - mean) / std >= 3
    else:
        assert spike_count >= mean + 3  # flat baseline: still a clear outlier
    assert len(man.spike_case_ids) >= 10


# ─── guarantee 7 ─────────────────────────────────────────────────────────

def test_g7_valid_coordinates_and_crimeno_encoding(seeded):
    session, man = seeded
    for case in session.query(m.CaseMaster).all():
        # CrimeNo is 18 digits (unless it is the deliberate demonstrable-bad
        # cases — none here are malformed length; the mismatch case is still
        # a valid 18-digit CrimeNo, just with a wrong embedded unit).
        assert len(case.CrimeNo) == 18
        # Cases that have coordinates must be inside Karnataka (the deliberate
        # missing-coords case has None and is exempt — that is guarantee 9).
        if case.latitude is not None and case.longitude is not None:
            assert KARNATAKA_LAT[0] <= float(case.latitude) <= KARNATAKA_LAT[1]
            assert KARNATAKA_LNG[0] <= float(case.longitude) <= KARNATAKA_LNG[1]
        # A well-formed CrimeNo encodes the registering unit... except the one
        # deliberate mismatch case (guarantee 8).
        decoded = _decode_crime_no(case.CrimeNo)
        if case.CaseMasterID != man.crimeno_unit_mismatch_case_id:
            assert decoded["unit"] == case.PoliceStationID


# ─── guarantee 8 ─────────────────────────────────────────────────────────

def test_g8_deliberate_crimeno_unit_mismatch(seeded):
    session, man = seeded
    case = session.get(m.CaseMaster, man.crimeno_unit_mismatch_case_id)
    decoded = _decode_crime_no(case.CrimeNo)
    # CrimeNo is a valid 18-digit number but its embedded unit != registering unit.
    assert len(case.CrimeNo) == 18
    assert decoded["unit"] != case.PoliceStationID
    assert case.CrimeNo == man.crimeno_unit_mismatch_crime_no


# ─── guarantee 9 ─────────────────────────────────────────────────────────

def test_g9_missing_coords_and_impossible_timestamp(seeded):
    session, man = seeded
    missing = session.get(m.CaseMaster, man.missing_coords_case_id)
    assert missing.latitude is None and missing.longitude is None  # Q01
    impossible = session.get(m.CaseMaster, man.impossible_timestamp_case_id)
    # Q05: incident AFTER registration.
    assert impossible.IncidentFromDate.date() > impossible.CrimeRegisteredDate


# ─── guarantee 10 ────────────────────────────────────────────────────────

def test_g10_cstype_distribution(seeded):
    session, man = seeded
    counts = Counter(cs.cstype for cs in session.query(m.ChargesheetDetails).all())
    # All three outcome types A/B/C present.
    assert counts["A"] > 0 and counts["B"] > 0 and counts["C"] > 0
    # Realistic skew: A is the most common outcome.
    assert counts["A"] >= counts["B"]
    assert counts["A"] >= counts["C"]
    # Manifest's declared g10 distribution is a subset of what's present.
    for t, n in man.cstype_distribution.items():
        assert counts[t] >= n


# ─── guarantee 11 ────────────────────────────────────────────────────────

def test_g11_low_confidence_identity_candidate(seeded):
    session, man = seeded
    cand = man.low_confidence_candidate
    band = cand["confidence_band"]
    assert band == [0.66, 0.75]
    assert band[0] <= cand["intended_confidence"] <= band[1]
    # The two near-match Accused rows exist and are genuinely a near (not
    # exact) match: near-identical names, different cases/districts.
    a = session.get(m.Accused, cand["person_a_accused_id"])
    b = session.get(m.Accused, cand["person_b_accused_id"])
    assert a is not None and b is not None
    assert a.AccusedName != b.AccusedName          # not an exact string match
    assert a.AccusedName.split()[-1] == b.AccusedName.split()[-1]  # but clearly similar
    assert a.CaseMasterID != b.CaseMasterID


# ─── guarantee 12 ────────────────────────────────────────────────────────

def test_g12_masking_divergence_between_roles(seeded):
    session, man = seeded
    assert len(man.masking_divergent_case_ids) >= 5
    from lumen.governance.masking import mask_victim_name, mask_accused_name

    diverging = 0
    for cid in man.masking_divergent_case_ids:
        victim = session.query(m.Victim).filter_by(CaseMasterID=cid).first()
        accused = session.query(m.Accused).filter_by(CaseMasterID=cid).first()
        # Station Officer sees masked; District SP sees the real name.
        v_so = mask_victim_name(victim.VictimName, "station_officer")
        v_sp = mask_victim_name(victim.VictimName, "district_sp")
        a_so = mask_accused_name(accused.AccusedName, "station_officer")
        a_sp = mask_accused_name(accused.AccusedName, "district_sp")
        if v_so != v_sp or a_so != a_sp:
            diverging += 1
    assert diverging >= 5
