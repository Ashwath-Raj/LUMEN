"""
EventContract v1 — LUMEN_MASTER_SPEC_V3 §7, §19.1.

Unlike the other cross-boundary contracts (Entity/Graph/Prediction), §19.1
gives `EventContract` a COMPLETE, explicit JSON shape — reproduced here field
for field, nothing added, nothing removed:

    { "event_id":"uuid", "event_type":"CaseRegistered", "event_version":"v1",
      "occurred_at":"iso8601", "actor_id":"user|system",
      "subject":{"type":"case","id":"12345"}, "payload":{},
      "trace_id":"uuid", "classification":"CONFIDENTIAL" }

`event_type` is constrained to the closed §19.2 catalogue (see bus/events.py)
so a contract cannot carry an event the catalogue does not define — §19.2 is a
fixed list ("Do not invent additional event types").

NOTE — contract vs. table shape. §19.1's contract nests `subject{type,id}` and
carries `classification`; §3.6's `lumen_event` table flattens the subject to
`subject_type`/`subject_id` and has NO `classification` column (9 columns vs
the contract's 10 fields, and no `event_version` mismatch: the table keeps
`event_version`). The mapping between the two lives in bus/signals.py; both
are represented exactly as the specification writes them, neither "improved".
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from lumen.bus.events import EventType

Classification = Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]


class Subject(BaseModel):
    """§19.1 `subject:{"type":"case","id":"12345"}` — the §2.1 entity the
    event is about."""
    type: str
    id: str


class EventContract(BaseModel):
    """§19.1 EventContract v1 — the only shape that crosses the bus boundary
    (§7 rule 4). Field set and names are §19.1 verbatim."""

    event_id: str                         # uuid
    event_type: EventType                 # closed §19.2 catalogue
    event_version: str = "v1"
    occurred_at: datetime                 # iso8601
    actor_id: str                         # "user|system"
    subject: Subject
    payload: dict = {}
    trace_id: str                         # uuid
    classification: Classification
