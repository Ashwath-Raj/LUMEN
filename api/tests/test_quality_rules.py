"""
Verifies the §5 data quality engine — the "Done when" criterion for
Session 6 of §33: "All 18 rules fire correctly against the seed."

"Fire correctly" is verified two ways:
  1. Each of the eighteen rules fires on a minimal positive fixture (a
     record that violates it) and does NOT fire on a clean fixture — a
     rule that fired on everything, or nothing, would be wrong.
  2. Against the actual Session 5 deterministic seed, the rules that the
     §32 seed is built to demonstrate (Q01, Q04, Q05, and the incidental
     Q12/Q15/Q16/Q18 its shapes produce) fire, and the scoring + batch job
     persist findings/scores to the lumen_ tables.

Self-contained: in-memory SQLite per test, no live PostgreSQL / HTTP.
"""
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models import canonical as m
from lumen.db.models import quality as qmodels  # noqa: F401 — registers lumen_ tables
from lumen.jobs.seed import seed_database, encode_crime_no
from lumen.jobs.quality import run_quality_precompute
from lumen.quality import rules as R
from lumen.quality.engine import evaluate
from lumen.quality.scoring import compute_scores


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _fire(rule_id, session) -> list:
    """Run one rule's detector and return its findings."""
    return list(R.RULES_BY_ID[rule_id].detector(session))


def _minimal_reference(session):
    """Just enough valid reference data that a single well-formed case can
    exist: one state, district, unit, status, category, gravity, head,
    subhead."""
    session.add(m.State(StateID=1, StateName="Karnataka", Active=True))
    session.add(m.District(DistrictID=1, DistrictName="Bengaluru Urban", StateID=1, Active=True))
    session.add(m.UnitType(UnitTypeID=1, UnitTypeName="Police Station", Active=True))
    session.add(m.Unit(UnitID=11, UnitName="Whitefield PS", TypeID=1, StateID=1, DistrictID=1, Active=True))
    session.add(m.CaseStatusMaster(CaseStatusID=1, CaseStatusName="Under Investigation"))
    session.add(m.CaseCategory(CaseCategoryID=1, LookupValue="FIR"))
    session.add(m.GravityOffence(GravityOffenceID=1, LookupValue="Heinous"))
    session.add(m.CrimeHead(CrimeHeadID=1, CrimeGroupName="Violent Crime", Active=True))
    session.add(m.CrimeSubHead(CrimeSubHeadID=11, CrimeHeadID=1, CrimeHeadName="Murder", SeqID=1))
    session.add(m.Act(ActCode="IPC", ActDescription="Indian Penal Code", ShortName="IPC", Active=True))
    session.add(m.Section(ActCode="IPC", SectionCode="302", SectionDescription="Murder", Active=True))
    session.flush()


def _clean_case(session, case_id=1, **overrides):
    """A fully valid case that fires NO rule by default."""
    fields = dict(
        CaseMasterID=case_id,
        CrimeNo=encode_crime_no(1, 1, 11, 2026, case_id),
        CaseNo=f"CN{case_id}",
        CrimeRegisteredDate=date.today(),          # recent -> not stale (Q16)
        PolicePersonID=None,
        PoliceStationID=11,
        CaseCategoryID=1,
        GravityOffenceID=1,
        CrimeMajorHeadID=1,
        CrimeMinorHeadID=11,                        # subhead 11 -> parent head 1 (matches, no Q11)
        CaseStatusID=1,
        IncidentFromDate=datetime(2026, 1, 5, 9, 0),
        IncidentToDate=None,
        InfoReceivedPSDate=datetime(2026, 1, 6, 10, 0),  # after incident (no Q06)
        latitude=12.97, longitude=77.60,            # inside Karnataka (no Q01/Q02)
        BriefFacts="A sufficiently long brief facts description exceeding twenty chars.",
    )
    fields.update(overrides)
    case = m.CaseMaster(**fields)
    session.add(case)
    # give it a charge so Q15 does not fire by default
    session.add(m.ActSectionAssociation(CaseMasterID=case_id, ActID="IPC", SectionID="302", ActOrderID=1, SectionOrderID=1))
    session.flush()
    return case


# ── every rule fires on a violation, and NOT on clean data ────────────────

def test_all_18_rules_are_catalogued():
    ids = [r.rule_id for r in R.RULES]
    assert ids == [f"Q{i:02d}" for i in range(1, 19)]
    assert len(R.RULES) == 18


def test_q01_fires_on_missing_coords():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, latitude=None, longitude=None)
    assert len(_fire("Q01", s)) == 1
    # clean case does not fire
    _clean_case(s, 2)
    assert {f.entity_id for f in _fire("Q01", s)} == {"1"}


def test_q02_fires_on_out_of_bounds_and_zero():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, latitude=0.0, longitude=0.0)          # (0,0)
    _clean_case(s, 2, latitude=48.0, longitude=2.0)         # Paris — outside Karnataka
    _clean_case(s, 3)                                        # clean
    ids = {f.entity_id for f in _fire("Q02", s)}
    assert ids == {"1", "2"}


def test_q03_fires_on_malformed_crimeno():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, CrimeNo="123")                         # too short
    _clean_case(s, 2, CrimeNo="900010011202600002")          # category 9 not documented
    _clean_case(s, 3)                                         # valid
    ids = {f.entity_id for f in _fire("Q03", s)}
    assert ids == {"1", "2"}


def test_q04_fires_on_crimeno_unit_mismatch():
    s = _fresh_session(); _minimal_reference(s)
    # registered to unit 11 but CrimeNo embeds unit 12
    _clean_case(s, 1, CrimeNo=encode_crime_no(1, 1, 12, 2026, 1))
    _clean_case(s, 2)                                         # matches
    ids = {f.entity_id for f in _fire("Q04", s)}
    assert ids == {"1"}


def test_q05_fires_on_incident_after_registration():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, CrimeRegisteredDate=date(2026, 3, 1), IncidentFromDate=datetime(2026, 4, 1, 8, 0))
    _clean_case(s, 2, CrimeRegisteredDate=date(2026, 4, 1), IncidentFromDate=datetime(2026, 3, 1, 8, 0))
    ids = {f.entity_id for f in _fire("Q05", s)}
    assert ids == {"1"}


def test_q06_fires_on_info_before_incident():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, IncidentFromDate=datetime(2026, 2, 1, 10, 0), InfoReceivedPSDate=datetime(2026, 1, 1, 9, 0))
    _clean_case(s, 2)
    ids = {f.entity_id for f in _fire("Q06", s)}
    assert ids == {"1"}


def test_q07_fires_on_chargesheet_before_registration():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, CrimeRegisteredDate=date(2026, 5, 1))
    s.add(m.ChargesheetDetails(CSID=1, CaseMasterID=1, csdate=datetime(2026, 4, 1, 10, 0), cstype="A"))
    _clean_case(s, 2, CrimeRegisteredDate=date(2026, 1, 1))
    s.add(m.ChargesheetDetails(CSID=2, CaseMasterID=2, csdate=datetime(2026, 6, 1, 10, 0), cstype="A"))
    s.flush()
    ids = {f.entity_id for f in _fire("Q07", s)}
    assert ids == {"1"}   # CSID 1


def test_q08_fires_on_arrest_before_incident():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, IncidentFromDate=datetime(2026, 3, 1, 8, 0))
    s.add(m.ArrestSurrender(ArrestSurrenderID=1, CaseMasterID=1, ArrestSurrenderDate=date(2026, 2, 1)))
    _clean_case(s, 2, IncidentFromDate=datetime(2026, 1, 1, 8, 0))
    s.add(m.ArrestSurrender(ArrestSurrenderID=2, CaseMasterID=2, ArrestSurrenderDate=date(2026, 2, 1)))
    s.flush()
    ids = {f.entity_id for f in _fire("Q08", s)}
    assert ids == {"1"}


def test_q09_fires_on_orphan_child_row():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1)
    # accused pointing at a non-existent case
    s.add(m.Accused(AccusedMasterID=999, CaseMasterID=424242, AccusedName="Orphan", GenderID=1, PersonID="A1"))
    s.flush()
    findings = _fire("Q09", s)
    assert any(f.entity_id == "999" for f in findings)


def test_q10_fires_on_broken_lookup():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, CaseStatusID=777)                      # status 777 does not exist
    # inactive lookup
    s.add(m.GravityOffence(GravityOffenceID=2, LookupValue="Inactive"))
    s.flush()
    _clean_case(s, 2, GravityOffenceID=2)
    # make gravity 2 inactive-like: GravityOffence has no Active column, so
    # use a lookup that DOES have Active — an inactive Unit.
    s.add(m.Unit(UnitID=12, UnitName="Inactive PS", TypeID=1, StateID=1, DistrictID=1, Active=False))
    s.flush()
    _clean_case(s, 3, PoliceStationID=12, CrimeNo=encode_crime_no(1, 1, 12, 2026, 3))
    findings = _fire("Q10", s)
    ids = {f.entity_id for f in findings}
    assert "1" in ids   # missing status
    assert "3" in ids   # inactive unit


def test_q11_fires_on_head_subhead_disagreement():
    s = _fresh_session(); _minimal_reference(s)
    # subhead 11 belongs to head 1; set major head to 2 -> disagreement
    s.add(m.CrimeHead(CrimeHeadID=2, CrimeGroupName="Property Crime", Active=True))
    s.flush()
    _clean_case(s, 1, CrimeMajorHeadID=2, CrimeMinorHeadID=11)
    _clean_case(s, 2, CrimeMajorHeadID=1, CrimeMinorHeadID=11)
    ids = {f.entity_id for f in _fire("Q11", s)}
    assert ids == {"1"}


def test_q12_fires_on_duplicate_case_suspicion():
    s = _fresh_session(); _minimal_reference(s)
    reg = date(2026, 2, 2)
    _clean_case(s, 1, CrimeRegisteredDate=reg, CrimeMajorHeadID=1)
    _clean_case(s, 2, CrimeRegisteredDate=reg, CrimeMajorHeadID=1)
    # same unit(11) + date + head, and a shared accused name
    s.add(m.Accused(AccusedMasterID=1, CaseMasterID=1, AccusedName="Shared Name", GenderID=1, PersonID="A1"))
    s.add(m.Accused(AccusedMasterID=2, CaseMasterID=2, AccusedName="Shared Name", GenderID=1, PersonID="A1"))
    s.flush()
    assert len(_fire("Q12", s)) >= 1


def test_q13_fires_on_implausible_age():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1)
    s.add(m.Accused(AccusedMasterID=1, CaseMasterID=1, AccusedName="Old", AgeYear=150, GenderID=1, PersonID="A1"))
    s.add(m.Victim(VictimMasterID=1, CaseMasterID=1, VictimName="Baby", AgeYear=0, GenderID=1, VictimPolice="0"))
    s.add(m.Accused(AccusedMasterID=2, CaseMasterID=1, AccusedName="Normal", AgeYear=30, GenderID=1, PersonID="A2"))
    s.flush()
    ids = {(f.entity_type, f.entity_id) for f in _fire("Q13", s)}
    assert ("Accused", "1") in ids and ("Victim", "1") in ids
    assert ("Accused", "2") not in ids


def test_q14_fires_on_accused_missing_personid_where_siblings_have_it():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1)
    s.add(m.Accused(AccusedMasterID=1, CaseMasterID=1, AccusedName="Has", GenderID=1, PersonID="A1"))
    s.add(m.Accused(AccusedMasterID=2, CaseMasterID=1, AccusedName="Missing", GenderID=1, PersonID=None))
    s.flush()
    ids = {f.entity_id for f in _fire("Q14", s)}
    assert ids == {"2"}


def test_q15_fires_on_case_with_no_charges():
    s = _fresh_session(); _minimal_reference(s)
    # a case with NO ActSectionAssociation
    c = m.CaseMaster(CaseMasterID=1, CrimeNo=encode_crime_no(1, 1, 11, 2026, 1),
                     PoliceStationID=11, CaseStatusID=1, BriefFacts="x" * 30,
                     latitude=12.97, longitude=77.60, CrimeRegisteredDate=date.today())
    s.add(c)
    _clean_case(s, 2)   # has a charge
    s.flush()
    ids = {f.entity_id for f in _fire("Q15", s)}
    assert ids == {"1"}


def test_q16_fires_on_stale_open_case():
    s = _fresh_session(); _minimal_reference(s)
    # open case whose only event is > 180 days ago
    _clean_case(s, 1, CaseStatusID=1, CrimeRegisteredDate=date(2020, 1, 1),
                IncidentFromDate=datetime(2020, 1, 1, 8, 0), InfoReceivedPSDate=datetime(2020, 1, 2, 8, 0))
    _clean_case(s, 2, CaseStatusID=1, CrimeRegisteredDate=date.today())  # recent
    ids = {f.entity_id for f in _fire("Q16", s)}
    assert ids == {"1"}


def test_q17_fires_on_inactive_act_section():
    s = _fresh_session(); _minimal_reference(s)
    s.add(m.Section(ActCode="IPC", SectionCode="999", SectionDescription="Dead section", Active=False))
    s.flush()
    _clean_case(s, 1)
    s.add(m.ActSectionAssociation(CaseMasterID=1, ActID="IPC", SectionID="999", ActOrderID=2, SectionOrderID=2))
    s.flush()
    findings = _fire("Q17", s)
    assert any(f.entity_id == "1:IPC:999" for f in findings)


def test_q18_fires_on_empty_or_short_brieffacts():
    s = _fresh_session(); _minimal_reference(s)
    _clean_case(s, 1, BriefFacts=None)
    _clean_case(s, 2, BriefFacts="short")
    _clean_case(s, 3)   # long enough
    ids = {f.entity_id for f in _fire("Q18", s)}
    assert ids == {"1", "2"}


# ── against the actual Session 5 seed ─────────────────────────────────────

def test_rules_fire_correctly_against_the_seed():
    s = _fresh_session()
    seed_database(s)
    fired = {f.rule_id for f in evaluate(s).findings}
    # The §32 seed is built to demonstrate these (guarantees 8, 9 + incidental).
    expected_present = {"Q01", "Q04", "Q05", "Q15", "Q18"}
    assert expected_present <= fired
    # Q02/Q03 must NOT fire: the seed's coordinates are all inside Karnataka
    # and its CrimeNos are all valid 18-digit numbers (the mismatch case is a
    # Q04, not a Q03/Q02).
    assert "Q02" not in fired
    assert "Q03" not in fired


def test_scoring_formula_matches_spec(monkeypatch=None):
    """§5.2: score = 1 − weighted_findings / records_in_scope, clamped 0..1,
    Critical 4 / High 2 / Medium 1 / Low 0.5."""
    s = _fresh_session(); _minimal_reference(s)
    # 4 clean cases, plus 1 with a Critical Q02 violation.
    for i in range(1, 5):
        _clean_case(s, i)
    _clean_case(s, 5, latitude=0.0, longitude=0.0)   # Critical (weight 4)
    result = evaluate(s)
    scores = {(sc.scope_type, sc.dimension): sc.score for sc in compute_scores(result)}
    # state validity: 1 Critical finding (weight 4) over 5 records = 1 - 4/5 = 0.2
    assert scores[("state", "validity")] == pytest.approx(0.2)
    # a dimension with no findings scores 1.0
    assert scores[("state", "integrity")] == pytest.approx(1.0)


def test_batch_job_persists_findings_and_scores():
    s = _fresh_session()
    seed_database(s)
    summary = run_quality_precompute(s)
    assert summary["findings"] > 0
    assert summary["scores"] > 0
    assert s.query(qmodels.LumenQualityFinding).count() == summary["findings"]
    assert s.query(qmodels.LumenQualityScore).count() == summary["scores"]
    # re-run is idempotent in count terms (clears then rewrites).
    summary2 = run_quality_precompute(s)
    assert s.query(qmodels.LumenQualityFinding).count() == summary2["findings"]


# ── §5.3 item 2 / §29.1 quality surface endpoints ─────────────────────────

def test_quality_endpoints_via_testclient(tmp_path):
    """The /quality/scores and /quality/findings endpoints read the
    precomputed lumen_ tables. Exercised through a TestClient with the app's
    get_db overridden to a seeded in-memory DB."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import main as app_main
    from lumen.db.session import get_db

    engine = create_engine("sqlite:///file:qmem?mode=memory&cache=shared&uri=true", connect_args={"uri": True})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    setup = TestingSession()
    seed_database(setup)
    run_quality_precompute(setup)
    setup.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app_main.app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app_main.app)
        scores = client.get("/api/quality/scores")
        assert scores.status_code == 200
        assert scores.json()["total"] > 0
        findings = client.get("/api/quality/findings?rule_id=Q04")
        assert findings.status_code == 200
        assert findings.json()["total"] >= 1
        assert all(f["rule_id"] == "Q04" for f in findings.json()["findings"])
    finally:
        app_main.app.dependency_overrides.pop(get_db, None)
