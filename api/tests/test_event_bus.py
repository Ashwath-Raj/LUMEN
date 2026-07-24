"""
Session 12 — intelligence bus and domain events (§19).

Covers: the EventContract v1 shape (§19.1) and validation, the closed §19.2
catalogue, the single publish path (§28 rule 6), dual-write to the append-only
lumen_event store AND dispatch to subscribers (§19.2), handler registration +
deterministic registration-order dispatch, the contract↔store mapping (nested
subject flattened, classification not persisted), append-only enforcement
(§21), serialization, and edge cases.

Self-contained: in-memory SQLite, no live PostgreSQL, no Catalyst Signals.
"""
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lumen.db.session import Base
from lumen.db.models.event import LumenEvent
from lumen.contracts.event import EventContract, Subject
from lumen.bus import catalog, repository, signals
from lumen.bus.events import EVENT_TYPES, is_known_event_type

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _event(event_id="e1", event_type="CaseRegistered", subject=None,
           classification="CONFIDENTIAL", occurred_at=NOW, payload=None):
    return EventContract(
        event_id=event_id, event_type=event_type, occurred_at=occurred_at,
        actor_id="system", subject=subject or Subject(type="case", id="12345"),
        payload=payload or {}, trace_id="trace-1", classification=classification)


@pytest.fixture(autouse=True)
def _isolate_subscribers():
    signals.clear_subscribers()
    signals.set_error_policy("log")
    yield
    signals.clear_subscribers()
    signals.set_error_policy("log")


# ── §19.2 catalogue is the closed, exact set ───────────────────────────────

def test_catalogue_is_the_closed_twenty_event_set():
    # 18 §19.2 rows, but the lifecycle row is three event types → 20
    assert len(EVENT_TYPES) == 20
    for name in ("CaseRegistered", "CaseUpdated", "ArrestRecorded",
                 "CaseChargesheeted", "PersonResolved", "PersonMatchDisputed",
                 "GraphProjected", "RiskUpdated", "AnomalyDetected",
                 "HotspotsUpdated", "InsightGenerated", "InsightVerified",
                 "InsightApproved", "InsightExpired", "RecommendationGenerated",
                 "QualityFindingRaised", "EvidenceUploaded", "AIQueryExecuted",
                 "InsightFeedbackGiven", "PolicyDenied"):
        assert is_known_event_type(name)
    assert not is_known_event_type("SomethingInvented")


def test_catalogue_registry_matches_event_types_and_records_subscribers():
    assert set(catalog.CATALOGUE) == set(EVENT_TYPES)
    # §19.2 verbatim subscriber names, spot-checked
    assert catalog.declared_subscribers("CaseRegistered") == (
        "Resolution", "graph", "quality", "cache", "insight", "notify")
    assert catalog.declared_subscribers("PolicyDenied") == ("Audit", "security metrics")
    assert catalog.entry("AnomalyDetected").emitted_when == "Anomaly crosses threshold"


# ── §19.1 EventContract validation ─────────────────────────────────────────

def test_contract_has_exactly_the_spec_fields():
    fields = set(EventContract.model_fields)
    assert fields == {"event_id", "event_type", "event_version", "occurred_at",
                      "actor_id", "subject", "payload", "trace_id", "classification"}
    assert EventContract.model_fields["event_version"].default == "v1"


def test_unknown_event_type_rejected_at_construction():
    with pytest.raises(ValidationError):
        _event(event_type="NotACatalogueEvent")


def test_invalid_classification_rejected():
    with pytest.raises(ValidationError):
        _event(classification="TOP_SECRET")


def test_missing_required_field_rejected():
    with pytest.raises(ValidationError):
        EventContract(event_id="e", event_type="CaseRegistered", occurred_at=NOW,
                      actor_id="system", subject=Subject(type="case", id="1"),
                      trace_id="t")   # classification missing


def test_serialization_round_trip():
    ev = _event(payload={"CaseMasterID": 12345, "nested": {"k": [1, 2]}})
    again = EventContract.model_validate_json(ev.model_dump_json())
    assert again == ev


# ── publish: dual-write (store + bus), §28 rule-6 single path ──────────────

def test_publish_writes_store_and_dispatches():
    s = _fresh_session()
    got = []
    signals.subscribe("CaseRegistered", lambda ev: got.append(ev.event_id))
    signals.publish(s, _event())
    # store
    rows = repository.read(s)
    assert len(rows) == 1 and rows[0].event_id == "e1"
    # bus
    assert got == ["e1"]


def test_contract_to_store_mapping_flattens_subject_and_drops_classification():
    s = _fresh_session()
    signals.publish(s, _event(subject=Subject(type="person", id="P-9")))
    row = repository.get(s, "e1")
    assert row.subject_type == "person" and row.subject_id == "P-9"
    assert row.event_version == "v1"
    # §3.6 lumen_event has no classification column
    assert "classification" not in {c.name for c in LumenEvent.__table__.columns}


def test_only_matching_subscribers_receive():
    s = _fresh_session()
    case_hits, arrest_hits = [], []
    signals.subscribe("CaseRegistered", lambda ev: case_hits.append(ev.event_id))
    signals.subscribe("ArrestRecorded", lambda ev: arrest_hits.append(ev.event_id))
    signals.publish(s, _event(event_id="c1", event_type="CaseRegistered"))
    signals.publish(s, _event(event_id="a1", event_type="ArrestRecorded",
                              subject=Subject(type="case", id="1")))
    assert case_hits == ["c1"] and arrest_hits == ["a1"]


def test_dispatch_is_in_registration_order():
    s = _fresh_session()
    order = []
    signals.subscribe("RiskUpdated", lambda ev: order.append("first"))
    signals.subscribe("RiskUpdated", lambda ev: order.append("second"))
    signals.subscribe("RiskUpdated", lambda ev: order.append("third"))
    signals.publish(s, _event(event_type="RiskUpdated",
                              subject=Subject(type="district", id="1")))
    assert order == ["first", "second", "third"]


def test_subscribe_rejects_unknown_event_type():
    with pytest.raises(ValueError, match="closed"):
        signals.subscribe("Nope", lambda ev: None)


def test_subscribe_is_idempotent_and_unsubscribe_works():
    h = lambda ev: None
    signals.subscribe("CaseUpdated", h)
    signals.subscribe("CaseUpdated", h)
    assert signals.subscribers("CaseUpdated") == [h]
    signals.unsubscribe("CaseUpdated", h)
    assert signals.subscribers("CaseUpdated") == []


# ── error policy (delivery semantics beyond this are spec-undefined) ───────

def test_error_policy_log_isolates_failing_handler():
    s = _fresh_session()
    good = []
    signals.subscribe("CaseRegistered", lambda ev: (_ for _ in ()).throw(RuntimeError("boom")))
    signals.subscribe("CaseRegistered", lambda ev: good.append(ev.event_id))
    signals.publish(s, _event())               # default 'log' — does not raise
    assert good == ["e1"]                        # subsequent handler still ran
    assert repository.get(s, "e1") is not None   # store write already happened


def test_error_policy_raise_propagates():
    s = _fresh_session()
    signals.set_error_policy("raise")
    signals.subscribe("CaseRegistered", lambda ev: (_ for _ in ()).throw(RuntimeError("boom")))
    with pytest.raises(RuntimeError):
        signals.publish(s, _event())


# ── append-only store (§21) ────────────────────────────────────────────────

def test_store_is_append_only_no_duplicate():
    s = _fresh_session()
    signals.publish(s, _event())
    with pytest.raises(repository.AppendOnlyViolation):
        signals.publish(s, _event())            # same event_id re-published


def test_store_rejects_update_of_persisted_event():
    s = _fresh_session()
    signals.publish(s, _event())
    row = repository.get(s, "e1")
    row.actor_id = "tampered"
    with pytest.raises(repository.AppendOnlyViolation):
        repository.assert_append_only(s)


def test_store_rejects_delete_of_persisted_event():
    s = _fresh_session()
    signals.publish(s, _event())
    s.delete(repository.get(s, "e1"))
    with pytest.raises(repository.AppendOnlyViolation):
        repository.assert_append_only(s)


# ── replay-log reads are deterministic (§21) ───────────────────────────────

def test_replay_log_read_is_ordered_and_filterable():
    s = _fresh_session()
    signals.publish(s, _event(event_id="b", occurred_at=datetime(2026, 7, 2, tzinfo=timezone.utc)))
    signals.publish(s, _event(event_id="a", occurred_at=datetime(2026, 7, 1, tzinfo=timezone.utc)))
    signals.publish(s, _event(event_id="c", event_type="ArrestRecorded",
                              occurred_at=datetime(2026, 7, 3, tzinfo=timezone.utc),
                              subject=Subject(type="case", id="1")))
    ids = [r.event_id for r in repository.read(s)]
    assert ids == ["a", "b", "c"]                # ordered by occurred_at
    assert [r.event_id for r in repository.read(s, event_type="CaseRegistered")] == ["a", "b"]
    assert [r.event_id for r in repository.read(s, subject_id="12345")] == ["a", "b"]
