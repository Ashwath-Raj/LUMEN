"""
Health reporting — LUMEN_MASTER_SPEC_V3 §25 / §24.2.

§25's `/system/health` (per-dependency state + degradation level) is the SAME
surface §24.2 defines and Session 18 already built in
`resilience/degradation.py` (`health_report`), served at
`GET /api/system/health`. This module does NOT duplicate that logic — it
delegates to it, so the health payload has a single source of truth (§28: one
computation point).
"""
from __future__ import annotations

from lumen.resilience.degradation import health_report


def system_health(probes: dict[str, object] | None = None) -> dict:
    """§25 / §24.2 health: per-dependency state + current degradation level.
    Delegates to the Session-18 resilience computation."""
    return health_report(probes or {})
