"""
Domain event catalogue — LUMEN_MASTER_SPEC_V3 §19.2.

The closed set of domain event types. §19.2 is a fixed table; the instruction
is explicit: "Do not invent additional event types." `EventType` is therefore
a Literal over exactly the event names §19.2 lists — no more, no fewer.

§19.2 has 18 table rows, but the row
`InsightVerified / InsightApproved / InsightExpired` names three distinct
event types (three separate lifecycle transitions), so the catalogue is
twenty event types in total. Each is enumerated separately below.
"""
from __future__ import annotations

from typing import Literal, get_args

# §19.2 catalogue — verbatim, in table order.
EventType = Literal[
    "CaseRegistered",
    "CaseUpdated",
    "ArrestRecorded",
    "CaseChargesheeted",
    "PersonResolved",
    "PersonMatchDisputed",
    "GraphProjected",
    "RiskUpdated",
    "AnomalyDetected",
    "HotspotsUpdated",
    "InsightGenerated",
    "InsightVerified",
    "InsightApproved",
    "InsightExpired",
    "RecommendationGenerated",
    "QualityFindingRaised",
    "EvidenceUploaded",
    "AIQueryExecuted",
    "InsightFeedbackGiven",
    "PolicyDenied",
]

# The event names as a runtime-checkable set.
EVENT_TYPES: frozenset[str] = frozenset(get_args(EventType))


def is_known_event_type(event_type: str) -> bool:
    """True iff `event_type` is one of the §19.2 catalogue names."""
    return event_type in EVENT_TYPES
