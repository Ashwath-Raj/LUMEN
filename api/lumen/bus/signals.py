"""
The intelligence bus publisher — LUMEN_MASTER_SPEC_V3 §19, §28 rule 6.

§28 structural rule 6: "`bus/signals.py` is the only publisher." Every domain
event enters the platform through `publish()` here — nothing else writes
`lumen_event` or dispatches to subscribers.

§19.2: "Every event lands in `lumen_event` (append-only) **and** on the bus.
The store is the replay log; the bus is delivery." `publish()` therefore does
BOTH, in that order: it appends the immutable store row first (the durable
replay log), then dispatches the validated `EventContract` to every subscriber
registered for that event type.

The named production runtime is Catalyst Signals + Event Functions (§26.1 rows
21–22, Session 21). §19 specifies no in-process broker, ordering guarantee,
retry policy, or delivery guarantee, so the T1 bus is the simplest thing the
spec's words require: SYNCHRONOUS, in-process, at-most-once (a handler runs
once per event), with subscribers dispatched in registration order. Those
choices are all "Cannot determine from the specification" and are exposed:
error handling is routed through a configurable policy. Nothing here is a
broker, queue, or retry engine.

Session 12 provides the mechanism and the registration API. It does NOT wire
Sessions 6–10 engines as live subscribers — §19.2's subscriber names
(Resolution, graph, quality, …) are those subsystems, and wiring them would
re-run and thereby change their behaviour, which this session must preserve.
The §33 row-12 live path is left for its own integration step.
"""
from __future__ import annotations

import logging
from typing import Callable

from sqlalchemy.orm import Session

from lumen.bus import repository
from lumen.bus.events import EVENT_TYPES
from lumen.contracts.event import EventContract
from lumen.db.models.event import LumenEvent

logger = logging.getLogger("lumen")

# A subscriber: a callable receiving the validated EventContract.
Handler = Callable[[EventContract], None]

# event_type -> ordered list of handlers (registration order = dispatch order).
_SUBSCRIBERS: dict[str, list[Handler]] = {}

# Error policy: "log" (default — a failing handler is logged, others still
# run) or "raise" (propagate). Delivery/retry semantics are undefined by the
# spec; this is the exposed configuration, not an invented retry engine.
_ERROR_POLICY = "log"


# ── subscription API ───────────────────────────────────────────────────────

def subscribe(event_type: str, handler: Handler) -> None:
    """Register `handler` for `event_type`. Raises for an unknown event type
    (the §19.2 catalogue is closed)."""
    if event_type not in EVENT_TYPES:
        raise ValueError(
            f"Unknown event_type {event_type!r}; the §19.2 catalogue is closed."
        )
    _SUBSCRIBERS.setdefault(event_type, [])
    if handler not in _SUBSCRIBERS[event_type]:
        _SUBSCRIBERS[event_type].append(handler)


def unsubscribe(event_type: str, handler: Handler) -> None:
    if handler in _SUBSCRIBERS.get(event_type, []):
        _SUBSCRIBERS[event_type].remove(handler)


def subscribers(event_type: str) -> list[Handler]:
    """The registered handlers for an event type, in dispatch order."""
    return list(_SUBSCRIBERS.get(event_type, []))


def clear_subscribers(event_type: str | None = None) -> None:
    """Remove all handlers (all types, or one). For test isolation and app
    re-init; not a runtime path."""
    if event_type is None:
        _SUBSCRIBERS.clear()
    else:
        _SUBSCRIBERS.pop(event_type, None)


def set_error_policy(policy: str) -> None:
    """'log' (default) or 'raise'. Delivery semantics beyond this are
    undefined by the spec."""
    global _ERROR_POLICY
    if policy not in ("log", "raise"):
        raise ValueError("error policy must be 'log' or 'raise'")
    _ERROR_POLICY = policy


# ── contract ↔ store-row mapping (§19.1 nested vs §3.6 flat) ───────────────

def _to_row(event: EventContract) -> LumenEvent:
    """Map the §19.1 contract onto the §3.6 store row: nested subject is
    flattened to subject_type/subject_id; the contract's `classification` has
    no store column (§3.6) and is not persisted (the row is INTERNAL by §4.2)."""
    return LumenEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        event_version=event.event_version,
        actor_id=event.actor_id,
        subject_type=event.subject.type,
        subject_id=event.subject.id,
        payload=event.payload,
        trace_id=event.trace_id,
        occurred_at=event.occurred_at,
    )


# ── the single publish path ────────────────────────────────────────────────

def publish(session: Session, event: EventContract) -> EventContract:
    """The one publish path (§28 rule 6). Appends the immutable store row,
    then dispatches to subscribers in registration order (§19.2: store first,
    then the bus). Returns the published contract.

    `event` is a validated `EventContract` — validation (closed event type,
    required fields, classification vocabulary) already happened at
    construction; an invalid event cannot reach here."""
    # 1. store: append-only replay log (§19.2 / §21)
    repository.append(session, _to_row(event))

    # 2. bus: synchronous in-process dispatch, registration order
    for handler in _SUBSCRIBERS.get(event.event_type, []):
        try:
            handler(event)
        except Exception:                       # noqa: BLE001
            if _ERROR_POLICY == "raise":
                raise
            logger.exception(
                "bus subscriber failed for %s (%s)", event.event_type, event.event_id
            )
    logger.info("§19 published %s (%s)", event.event_type, event.event_id)
    return event
