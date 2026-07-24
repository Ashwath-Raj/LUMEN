"""
Event catalogue registry — LUMEN_MASTER_SPEC_V3 §19.2.

§19.2's table reproduced as data: for each event type, the "Emitted when"
condition and the declared subscriber names, verbatim. This is a REGISTRY,
not a wiring: it records what §19.2 says. The subscriber names are the
subsystems of other sessions (Resolution, graph, quality, insight, cache,
notify, …); Session 12 does not instantiate them as live handlers (that
would re-run Sessions 6–10 engines). `bus/signals.py` lets real handlers
register at runtime; this catalogue is the declared intent §19.2 fixes and
the reference a later integration step wires against.
"""
from __future__ import annotations

from dataclasses import dataclass

from lumen.bus.events import EVENT_TYPES, EventType


@dataclass(frozen=True)
class CatalogEntry:
    event_type: str
    emitted_when: str
    subscribers: tuple[str, ...]


# §19.2 — verbatim "Emitted when" / "Subscribers" per row. The three-in-one
# lifecycle row is split into its three event types with the shared cell.
CATALOGUE: dict[str, CatalogEntry] = {
    e.event_type: e for e in [
        CatalogEntry("CaseRegistered", "New CaseMaster row",
                     ("Resolution", "graph", "quality", "cache", "insight", "notify")),
        CatalogEntry("CaseUpdated", "Case fields change",
                     ("Insight regeneration", "cache")),
        CatalogEntry("ArrestRecorded", "New ArrestSurrender",
                     ("Graph", "timeline", "insight")),
        CatalogEntry("CaseChargesheeted", "New ChargesheetDetails",
                     ("Outcome model", "timeline", "insight")),
        CatalogEntry("PersonResolved", "Resolution links or splits a cluster",
                     ("Graph", "feature store", "insight")),
        CatalogEntry("PersonMatchDisputed", "Officer reports a bad match",
                     ("Resolution review queue", "audit")),
        CatalogEntry("GraphProjected", "Projection completes",
                     ("Cache warm", "insight", "metrics")),
        CatalogEntry("RiskUpdated", "District risk recomputed",
                     ("Insight", "notify", "cache")),
        CatalogEntry("AnomalyDetected", "Anomaly crosses threshold",
                     ("Insight", "Mail", "Push", "command centre")),
        CatalogEntry("HotspotsUpdated", "Clustering completes",
                     ("Cache", "geo surface")),
        CatalogEntry("InsightGenerated", "Any producer emits",
                     ("Lifecycle", "audit")),
        CatalogEntry("InsightVerified", "Lifecycle transitions",
                     ("UI", "audit", "regeneration")),
        CatalogEntry("InsightApproved", "Lifecycle transitions",
                     ("UI", "audit", "regeneration")),
        CatalogEntry("InsightExpired", "Lifecycle transitions",
                     ("UI", "audit", "regeneration")),
        CatalogEntry("RecommendationGenerated", "Decision support runs",
                     ("UI", "audit")),
        CatalogEntry("QualityFindingRaised", "Quality rule fires",
                     ("Quality surface", "insight", "confidence")),
        CatalogEntry("EvidenceUploaded", "Asset stored in Stratus",
                     ("Case workspace", "audit")),
        CatalogEntry("AIQueryExecuted", "/ai/ask completes",
                     ("Audit", "evaluation", "metrics")),
        CatalogEntry("InsightFeedbackGiven", "Officer rates an insight",
                     ("Evaluation", "audit")),
        CatalogEntry("PolicyDenied", "Authorisation denies a request",
                     ("Audit", "security metrics")),
    ]
}

# Sanity: the catalogue registry covers exactly the closed event set.
assert set(CATALOGUE) == set(EVENT_TYPES), "catalogue/event-type set mismatch"


def entry(event_type: EventType) -> CatalogEntry:
    return CATALOGUE[event_type]


def declared_subscribers(event_type: EventType) -> tuple[str, ...]:
    """The §19.2 declared subscriber names for an event type (reference only)."""
    return CATALOGUE[event_type].subscribers
