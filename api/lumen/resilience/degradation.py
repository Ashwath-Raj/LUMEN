"""
Degradation ladder + dependency response matrix — LUMEN_MASTER_SPEC_V3 §24.2,
§24.1, §24.3 rules 5-6.

§24.2 ladder, verbatim:

    L0 FULL          all services healthy
    L1 CACHED        live queries fail → cached payloads, staleness shown
    L2 PRECOMPUTED   cache cold → precomputed tables only; no ad-hoc filtering
    L3 DETERMINISTIC LLM down → template insights from evidence
    L4 READ-ONLY     store degraded → last snapshot, writes rejected

§24.1's Dependency→Response matrix is reproduced as data (RESPONSES) so §24's
"user sees" and "response" columns are queryable rather than hand-written; it
also makes the §33 row-11 done-when computable ("Killing QuickML degrades to
L3").

Level resolution (§24.2): the current level is the WORST (highest) level
implied by any unhealthy dependency. The dependency→level mapping follows the
ladder's own text:
    store degraded            → L4 READ-ONLY
    graph/precompute-only     → L2 PRECOMPUTED
    QuickML LLM down          → L3 DETERMINISTIC
    cache down / live fail    → L1 CACHED
all healthy                   → L0 FULL

Note on ordering: §24.2 lists L3 above L4 numerically, and L4 (store) is the
most severe. Level SEVERITY therefore follows the ladder's own semantics
(read-only store loss is worst), while the NAME/number is the spec's. The
resolver returns the most severe applicable level; where two apply, store loss
(L4) dominates, then LLM (L3), then precomputed (L2), then cached (L1).

§24.3 rule 5 ("never fabricate to fill a gap"): `not_available` renders a
missing value as the literal marker, never zero, never interpolated.
§24.3 rule 6 ("every degradation ... is audited"): `audit_degradation` writes
a lumen_audit row. The bus EVENT half of rule 6 cannot be satisfied — the
closed §19.2 catalogue defines no degradation event type and Session 12
forbids inventing one; recorded as "Cannot determine from the specification".
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum

from sqlalchemy.orm import Session

from lumen.db.models.policy import LumenAudit
from lumen.policy import audit_repo

NOT_AVAILABLE = "not available"       # §24.3 rule 5 marker


class Level(IntEnum):
    L0 = 0    # FULL
    L1 = 1    # CACHED
    L2 = 2    # PRECOMPUTED
    L3 = 3    # DETERMINISTIC
    L4 = 4    # READ-ONLY


LEVEL_NAMES: dict[Level, str] = {
    Level.L0: "FULL",
    Level.L1: "CACHED",
    Level.L2: "PRECOMPUTED",
    Level.L3: "DETERMINISTIC",
    Level.L4: "READ-ONLY",
}


@dataclass(frozen=True)
class DependencyResponse:
    dependency: str
    failure_mode: str
    detection: str
    response: str
    user_sees: str


# §24.1 matrix — verbatim.
RESPONSES: dict[str, DependencyResponse] = {
    d.dependency: d for d in [
        DependencyResponse("data_store", "Unavailable / slow", "Health probe, timeout 3 s",
                           "Serve cached payloads; read-only mode",
                           "Banner: \"Serving cached data from HH:MM\""),
        DependencyResponse("cache", "Unavailable", "Timeout 200 ms",
                           "Bypass to store", "Nothing (slower)"),
        DependencyResponse("quickml_llm", "Unavailable / timeout",
                           "Timeout 15 s, circuit breaker at 3 failures/60 s",
                           "Deterministic fallback (§16.4)",
                           "\"AI narrative unavailable — showing evidence-based summary\""),
        DependencyResponse("quickml_rag", "Unavailable", "Timeout",
                           "Retrieval falls back to Data Store full-text",
                           "Limitation line added to the insight"),
        DependencyResponse("graph_backend", "Unavailable", "Health probe",
                           "Serve last projection from lumen_graph_edge / NoSQL snapshot",
                           "\"Network as of HH:MM\""),
        DependencyResponse("signals", "Delayed", "Lag metric",
                           "Precompute cron catches up; insights marked stale",
                           "Staleness timestamp on every card"),
        DependencyResponse("zia_automl", "Unavailable", "Timeout",
                           "Local scikit-learn model",
                           "lineage.method records the fallback"),
        DependencyResponse("stratus", "Unavailable", "Timeout",
                           "Evidence list renders metadata without thumbnails",
                           "\"Attachment temporarily unavailable\""),
        DependencyResponse("map_tiles", "Unavailable", "Tile error",
                           "Choropleth renders on cached GeoJSON without basemap",
                           "Basemap absent, data intact"),
    ]
}

# Dependency → the ladder level its failure implies (from §24.2's text).
_DEPENDENCY_LEVEL: dict[str, Level] = {
    "data_store": Level.L4,          # store degraded → read-only
    "quickml_llm": Level.L3,         # LLM down → deterministic
    "graph_backend": Level.L2,       # serve precomputed projection only
    "cache": Level.L1,               # cache down → cached/live-fail path
    "quickml_rag": Level.L3,         # generation-side degradation
    "zia_automl": Level.L2,          # local model / precomputed
    "signals": Level.L1,
    "stratus": Level.L0,             # cosmetic (thumbnails) — no ladder drop
    "map_tiles": Level.L0,           # cosmetic (basemap) — no ladder drop
}


def resolve_level(unhealthy: set[str]) -> Level:
    """§24.2: the current level is the most severe implied by any unhealthy
    dependency. All healthy → L0."""
    if not unhealthy:
        return Level.L0
    return max((_DEPENDENCY_LEVEL.get(dep, Level.L0) for dep in unhealthy),
               default=Level.L0)


def level_label(level: Level) -> str:
    """e.g. 'L3 — DETERMINISTIC'."""
    return f"L{int(level)} — {LEVEL_NAMES[level]}"


def not_available(value):
    """§24.3 rule 5: never fabricate. Returns the value if present, else the
    'not available' marker — never zero, never an interpolation."""
    return NOT_AVAILABLE if value is None else value


# ── health evaluation (§24.1 Detection → per-dependency state) ─────────────
# §24.1's "Detection" column is a health probe / timeout per dependency. The
# real probes target external Catalyst services not present in this
# environment; the mechanism is a per-dependency `probe` — a callable returning
# True (healthy) / False (unhealthy). Probes are injected (deterministic,
# local); a dependency with no probe is reported "unknown" and treated as
# healthy for level resolution (absence of a probe is not evidence of failure).
# Kept in degradation.py because health → level is one concern (§28 lists
# resilience/ as {breaker, timeouts, degradation} — no separate health module).

HEALTHY = "healthy"
UNHEALTHY = "unhealthy"
UNKNOWN = "unknown"


def evaluate_health(probes: dict[str, object]) -> dict[str, str]:
    """Run each dependency's probe → per-dependency state. A probe raising or
    returning False is `unhealthy`; True is `healthy`; a dependency in
    RESPONSES without a probe is `unknown`."""
    states: dict[str, str] = {}
    for dep in RESPONSES:
        probe = probes.get(dep)
        if probe is None:
            states[dep] = UNKNOWN
            continue
        try:
            states[dep] = HEALTHY if probe() else UNHEALTHY
        except Exception:                        # a failing probe is unhealthy
            states[dep] = UNHEALTHY
    return states


def health_report(probes: dict[str, object]) -> dict:
    """The §24.2 /system/health payload subset: per-dependency state + the
    current degradation level. (§25's rich metrics are observability — a
    later session — and are NOT included here.)"""
    states = evaluate_health(probes)
    unhealthy = {dep for dep, st in states.items() if st == UNHEALTHY}
    level = resolve_level(unhealthy)
    return {
        "degradation_level": int(level),
        "degradation_label": level_label(level),
        "dependencies": [
            {"dependency": dep, "state": states[dep],
             "response": RESPONSES[dep].response if dep in unhealthy else None,
             "user_sees": RESPONSES[dep].user_sees if dep in unhealthy else None}
            for dep in sorted(states)
        ],
    }


def audit_degradation(session: Session, *, from_level: Level, to_level: Level,
                      reason: str, user_id: str = "system",
                      now: datetime | None = None) -> None:
    """§24.3 rule 6 (audit half): record a degradation transition in
    lumen_audit. The bus-event half is unmet — the §19.2 catalogue has no
    degradation event type (disclosed)."""
    now = now or datetime.now(timezone.utc)
    audit_repo.append(session, LumenAudit(
        audit_id=str(uuid.uuid4()),
        user_id=user_id,
        action="degradation",
        resource=f"level:{level_label(to_level)}",
        decision=level_label(to_level),
        reason=f"{level_label(from_level)} → {level_label(to_level)}: {reason}"[:300],
        ip=None,
        occurred_at=now,
    ))
