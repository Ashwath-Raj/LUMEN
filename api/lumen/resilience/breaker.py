"""
Circuit breaker — LUMEN_MASTER_SPEC_V3 §24.3 rule 2.

Rule 2, verbatim: "Circuit breakers on QuickML and the graph backend: 3
failures in 60 s opens for 120 s, then half-open."

The three constants are therefore spec-fixed, not tunable:
    FAILURE_THRESHOLD = 3       failures ...
    FAILURE_WINDOW_S  = 60      ... in 60 s → open
    OPEN_DURATION_S   = 120     open for 120 s, then half-open

State machine (deterministic, local; the clock is injected so behaviour is
reproducible and no wall-clock is read):

    CLOSED    normal. Failures within the rolling 60 s window are counted;
              reaching 3 opens the breaker. A success clears the window.
    OPEN      calls are rejected immediately (CircuitOpen) for 120 s from the
              trip; after that the next call is allowed as a probe (HALF_OPEN).
    HALF_OPEN one probe call is allowed. Success → CLOSED (window reset);
              failure → OPEN again for another 120 s.

§24.1 pairs the breaker with the QuickML deterministic fallback and the graph
"serve last projection" response — this module reports OPEN so those callers
degrade; it does not itself perform the fallback (that lives in ai/§16.4 and
the graph backend, consumed not duplicated).

"how many successes re-close from half-open" is not stated by §24.3 → a single
probe success closes it (disclosed).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# §24.3 rule 2 — spec-fixed.
FAILURE_THRESHOLD = 3
FAILURE_WINDOW_S = 60.0
OPEN_DURATION_S = 120.0


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpen(Exception):
    """The breaker is open; the call is rejected without being attempted."""


@dataclass
class CircuitBreaker:
    """A single breaker (one per protected dependency, e.g. 'quickml',
    'graph_backend'). `clock` is a zero-arg callable returning a
    monotonically increasing float (seconds) — injected for determinism."""

    name: str
    clock: object
    _failure_times: list[float] = field(default_factory=list)
    _opened_at: float | None = None
    _state: BreakerState = BreakerState.CLOSED

    # ── state, honouring the 120 s open→half-open transition on read ──────
    def state(self) -> BreakerState:
        if self._state is BreakerState.OPEN and self._opened_at is not None:
            if self.clock() - self._opened_at >= OPEN_DURATION_S:
                self._state = BreakerState.HALF_OPEN
        return self._state

    def allows(self) -> bool:
        """Whether a call may proceed now."""
        return self.state() is not BreakerState.OPEN

    # ── outcome recording ─────────────────────────────────────────────────
    def record_success(self) -> None:
        # Any success closes a half-open breaker and clears the window.
        self._failure_times.clear()
        self._opened_at = None
        self._state = BreakerState.CLOSED

    def record_failure(self) -> None:
        now = self.clock()
        st = self.state()
        if st is BreakerState.HALF_OPEN:
            self._trip(now)                      # probe failed → open again
            return
        # CLOSED: count failures within the rolling 60 s window.
        self._failure_times.append(now)
        self._failure_times = [t for t in self._failure_times
                               if now - t < FAILURE_WINDOW_S]
        if len(self._failure_times) >= FAILURE_THRESHOLD:
            self._trip(now)

    def _trip(self, now: float) -> None:
        self._state = BreakerState.OPEN
        self._opened_at = now
        self._failure_times.clear()

    # ── guarded call ──────────────────────────────────────────────────────
    def call(self, func, *args, **kwargs):
        """Run `func` under the breaker. Raises CircuitOpen if open; on an
        exception from `func`, records the failure and re-raises."""
        if not self.allows():
            raise CircuitOpen(f"circuit '{self.name}' is open (§24.3 rule 2)")
        try:
            result = func(*args, **kwargs)
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result


class BreakerRegistry:
    """Holds one breaker per protected dependency. §24.3 rule 2 names QuickML
    and the graph backend; both are pre-registered."""

    def __init__(self, clock):
        self._clock = clock
        self._breakers: dict[str, CircuitBreaker] = {
            "quickml": CircuitBreaker("quickml", clock),
            "graph_backend": CircuitBreaker("graph_backend", clock),
        }

    def get(self, name: str) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name, self._clock)
        return self._breakers[name]

    def states(self) -> dict[str, str]:
        return {name: b.state().value for name, b in self._breakers.items()}
