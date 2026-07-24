"""
Service registry — LUMEN_MASTER_SPEC_V3 §22.

`lumen_service_registry` "records every internal capability: name, capability,
version, endpoint, dependencies, health state, last check." This module is its
access layer: register / list / get, plus `seed_service_registry`, which
writes the §22 table (Service / Capability / Depends on) verbatim.

§22's table, reproduced exactly (the CATALOGUE constant below):

    identity     entity resolution          <- data store
    graph        projection + queries       <- data store, identity
    prediction   risk, anomaly, outcome     <- features, data store
    features     feature computation        <- data store, graph
    quality      rule evaluation            <- data store
    ai           orchestration              <- QuickML, retrieval, graph, features, KB
    kb           corpus + retrieval         <- QuickML, stratus
    policy       authorisation              <- authentication
    bus          event publication          <- signals

This makes §24's dependency table computable rather than hand-written (§22),
but §24 (resilience) is a later session — only the DATA it will consume is
populated here; no health probing, no failure logic.

Disclosed (cannot be determined from §22): §22 lists id/version/endpoint as
columns but gives no per-service values. `service_id = name`, `version = "v1"`,
and `endpoint` is the in-process module path (these are internal capabilities,
not external HTTP services — §22 "internal capability"). `health_state` seeds
to "unknown" and `last_check` to NULL (live probing is §24).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from lumen.db.models.registry import LumenServiceRegistry


@dataclass(frozen=True)
class ServiceSpec:
    name: str
    capability: str
    depends_on: tuple[str, ...]
    endpoint: str


# §22's Service / Capability / Depends-on table — verbatim, in table order.
CATALOGUE: tuple[ServiceSpec, ...] = (
    ServiceSpec("identity", "entity resolution",
                ("data store",), "lumen.identity"),
    ServiceSpec("graph", "projection + queries",
                ("data store", "identity"), "lumen.graph"),
    ServiceSpec("prediction", "risk, anomaly, outcome",
                ("features", "data store"), "lumen.intelligence"),
    ServiceSpec("features", "feature computation",
                ("data store", "graph"), "lumen.intelligence.features"),
    ServiceSpec("quality", "rule evaluation",
                ("data store",), "lumen.quality"),
    ServiceSpec("ai", "orchestration",
                ("QuickML", "retrieval", "graph", "features", "KB"), "lumen.ai"),
    ServiceSpec("kb", "corpus + retrieval",
                ("QuickML", "stratus"), "lumen.kb"),
    ServiceSpec("policy", "authorisation",
                ("authentication",), "lumen.policy"),
    ServiceSpec("bus", "event publication",
                ("signals",), "lumen.bus"),
)

DEFAULT_VERSION = "v1"
INITIAL_HEALTH = "unknown"        # §24 health probing is a later session


def register_service(session: Session, spec: ServiceSpec, *,
                     version: str = DEFAULT_VERSION,
                     health_state: str = INITIAL_HEALTH,
                     last_check: datetime | None = None) -> LumenServiceRegistry:
    """Register (or update) one internal capability."""
    row = session.get(LumenServiceRegistry, spec.name) or \
        LumenServiceRegistry(service_id=spec.name)
    row.name = spec.name
    row.capability = spec.capability
    row.version = version
    row.endpoint = spec.endpoint
    row.depends_on = list(spec.depends_on)
    row.health_state = health_state
    row.last_check = last_check
    session.add(row)
    session.flush()
    return row


def seed_service_registry(session: Session) -> int:
    """Write the §22 catalogue. Idempotent (upsert by service_id). Returns
    the number of services registered."""
    for spec in CATALOGUE:
        register_service(session, spec)
    return len(CATALOGUE)


def get_service(session: Session, service_id: str) -> LumenServiceRegistry | None:
    return session.get(LumenServiceRegistry, service_id)


def list_services(session: Session) -> list[LumenServiceRegistry]:
    """All registered services, ordered by service_id (deterministic)."""
    return (session.query(LumenServiceRegistry)
            .order_by(LumenServiceRegistry.service_id).all())


def as_dict(row: LumenServiceRegistry) -> dict:
    return {
        "service_id": row.service_id,
        "name": row.name,
        "capability": row.capability,
        "version": row.version,
        "endpoint": row.endpoint,
        "depends_on": row.depends_on,
        "health_state": row.health_state,
        "last_check": row.last_check.isoformat() if row.last_check else None,
    }
