"""
Cache — LUMEN_MASTER_SPEC_V3 §26.1 row 9, §23 (Caching), §24.1.

§26.1 #9: "Cache — Overview, hotspots, ego graphs, district risk, AI answers —
TTLs in §23." §23 fixes the TTL per payload, verbatim:

    overview       60 s
    hotspots       5 min   (300 s)
    ego graphs     15 min  (900 s)
    district risk  1 h     (3600 s)
    AI answers     15 min  (900 s)

The DEPLOYED backend is Catalyst Cache (§26.1). Locally there is no Catalyst
runtime, so this module provides a deterministic in-process backend behind a
swappable `CacheBackend` interface — the ADR-001 / §16.1 pattern ("backend is
swappable; the API must not know which answered"). A Catalyst Cache adapter
slots in at deploy without any caller changing. Nothing here is a distributed
cache, external queue, or cloud service (§ scope: local + deterministic).

The clock is injected (a zero-arg callable → seconds), so TTL expiry is
reproducible in tests — no wall-clock is read. §24.1: cache unavailable →
bypass to store (a caller getting a miss simply recomputes); §24.2 L1/L2 model
the cache-cold path. This module implements the store; the degradation
behaviour lives in resilience/ (Session 18), consumed not duplicated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

# §23 TTLs (seconds) — spec-fixed, one per payload kind.
TTL_OVERVIEW_S = 60
TTL_HOTSPOTS_S = 300           # 5 min
TTL_EGO_GRAPH_S = 900          # 15 min
TTL_DISTRICT_RISK_S = 3600     # 1 h
TTL_AI_ANSWER_S = 900          # 15 min

TTLS: dict[str, int] = {
    "overview": TTL_OVERVIEW_S,
    "hotspots": TTL_HOTSPOTS_S,
    "ego_graph": TTL_EGO_GRAPH_S,
    "district_risk": TTL_DISTRICT_RISK_S,
    "ai_answer": TTL_AI_ANSWER_S,
}


def ttl_for(payload_kind: str) -> int:
    """The §23 TTL for a payload kind. Raises for an unknown kind — §23 fixes
    exactly these five; a kind outside them cannot be given a TTL without
    inventing one."""
    if payload_kind not in TTLS:
        raise KeyError(
            f"No §23 TTL defined for payload kind {payload_kind!r}; "
            f"known kinds: {sorted(TTLS)}."
        )
    return TTLS[payload_kind]


class CacheBackend(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, *, ttl_s: int) -> None: ...
    def invalidate(self, key: str) -> None: ...
    def clear(self) -> None: ...


@dataclass
class _Entry:
    value: Any
    expires_at: float


@dataclass
class InProcessCache:
    """The local deterministic backend. `clock` is injected (seconds); an
    entry is a miss once `clock() >= expires_at`."""

    clock: Any
    _store: dict[str, _Entry] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if self.clock() >= entry.expires_at:      # expired → miss (lazy evict)
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, *, ttl_s: int) -> None:
        self._store[key] = _Entry(value=value, expires_at=self.clock() + ttl_s)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


def cache_key(payload_kind: str, *parts: str) -> str:
    """Deterministic cache key: '<kind>:<part>:<part>'. §23 caches by payload."""
    return ":".join([payload_kind, *(str(p) for p in parts)])


def get_or_compute(backend: CacheBackend, payload_kind: str, key_parts,
                   compute):
    """The read-through pattern (§24.1: a miss falls through to the store /
    recompute). Uses the §23 TTL for the payload kind. `compute` is a zero-arg
    callable producing the value on a miss."""
    key = cache_key(payload_kind, *key_parts)
    cached = backend.get(key)
    if cached is not None:
        return cached, True                        # (value, hit)
    value = compute()
    backend.set(key, value, ttl_s=ttl_for(payload_kind))
    return value, False
