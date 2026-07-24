"""
Per-dependency timeout policy — LUMEN_MASTER_SPEC_V3 §24.1, §24.3 rule 1.

§24.3 rule 1: "Every outbound call has a timeout. No unbounded waits."
§24.1's Detection column fixes the per-dependency timeouts, reproduced here
verbatim (seconds):

    Data Store        3 s      (health probe, timeout 3 s)
    Catalyst Cache    0.2 s    (timeout 200 ms)
    QuickML LLM       15 s     (timeout 15 s)
    QuickML RAG       — (Timeout; no value stated → Cannot determine; uses
                        the KB/retrieval default below)
    Graph backend     — (Health probe; no explicit timeout value stated)
    Zia AutoML        — (Timeout; no value stated)
    Stratus           — (Timeout; no value stated)

Only the three dependencies §24.1 gives an explicit value for carry a
spec-fixed timeout; the rest use a disclosed default and are recorded in the
Session deliverables as "Cannot determine from the specification".

`call_with_timeout` is the local, deterministic wrapper enforcing rule 1: it
runs the callable under a wall-clock deadline. In this environment there is no
live outbound service, so the mechanism is what matters — a call exceeding its
budget raises `DependencyTimeout`, which the caller (breaker / degradation
ladder) treats as a failure. No threads/async runtime is spun up for external
Catalyst services (that is Catalyst runtime — a later concern); the wrapper is
a pure guard usable by any caller that can measure its own elapsed time.
"""
from __future__ import annotations

from dataclasses import dataclass

# §24.1 explicit timeouts (seconds). Only these three are spec-fixed.
DATA_STORE_TIMEOUT_S = 3.0
CACHE_TIMEOUT_S = 0.2                # 200 ms
QUICKML_LLM_TIMEOUT_S = 15.0

# Disclosed default for dependencies §24.1 lists with "Timeout"/"Health probe"
# but no numeric value (QuickML RAG, Graph backend, Zia AutoML, Stratus).
DEFAULT_TIMEOUT_S = 3.0

TIMEOUTS_S: dict[str, float] = {
    "data_store": DATA_STORE_TIMEOUT_S,
    "cache": CACHE_TIMEOUT_S,
    "quickml_llm": QUICKML_LLM_TIMEOUT_S,
    # No spec-fixed value — default, disclosed:
    "quickml_rag": DEFAULT_TIMEOUT_S,
    "graph_backend": DEFAULT_TIMEOUT_S,
    "zia_automl": DEFAULT_TIMEOUT_S,
    "stratus": DEFAULT_TIMEOUT_S,
    "map_tiles": DEFAULT_TIMEOUT_S,
    "signals": DEFAULT_TIMEOUT_S,
}


class DependencyTimeout(Exception):
    """An outbound call exceeded its §24.1 timeout budget."""


def timeout_for(dependency: str) -> float:
    """The §24.1 timeout for a dependency (default for those §24.1 leaves
    unspecified)."""
    return TIMEOUTS_S.get(dependency, DEFAULT_TIMEOUT_S)


@dataclass
class TimedResult:
    value: object
    elapsed_s: float


def call_with_timeout(dependency: str, func, *, clock, args=(), kwargs=None):
    """§24.3 rule 1 guard. Runs `func` and enforces the §24.1 budget using an
    injected `clock` (a zero-arg callable returning a monotonically increasing
    float). Deterministic and local — the clock is supplied by the caller/test,
    so no real wall-clock or event loop is required.

    Raises `DependencyTimeout` if the measured elapsed time exceeds the
    dependency's budget; otherwise returns a `TimedResult`."""
    kwargs = kwargs or {}
    budget = timeout_for(dependency)
    start = clock()
    value = func(*args, **kwargs)
    elapsed = clock() - start
    if elapsed > budget:
        raise DependencyTimeout(
            f"{dependency} call took {elapsed:.3f}s, over its {budget}s budget "
            "(§24.1 / §24.3 rule 1)."
        )
    return TimedResult(value=value, elapsed_s=elapsed)


# ── §24.3 rule 3: retry policy ─────────────────────────────────────────────
# "Retries only on idempotent reads: 2 attempts, exponential backoff with
# jitter. Never retry generation blindly — it doubles cost and latency."
#
# "2 attempts" is spec-fixed. The backoff BASE delay and the jitter BOUNDS are
# not stated by §24.3 → disclosed configuration (base 0.1 s, jitter ±50%),
# recorded in the Session deliverables as "Cannot determine from the
# specification". Retry lives here (a call-guarding concern) rather than a new
# module, keeping resilience/ to §28's {breaker, timeouts, degradation} files.

RETRY_ATTEMPTS = 2               # §24.3 rule 3 — spec-fixed
RETRY_BASE_DELAY_S = 0.1        # disclosed default (base not stated by §24.3)
RETRY_JITTER_FRACTION = 0.5     # disclosed default (jitter bounds not stated)


class NonIdempotentRetryError(Exception):
    """Raised when retry is attempted on a non-idempotent operation
    (§24.3 rule 3: generation is never retried blindly)."""


def backoff_delay(attempt: int, *, jitter: float = 0.0) -> float:
    """Exponential backoff for `attempt` (1-indexed) with a caller-supplied
    jitter fraction in [-1, 1] applied to the base. Deterministic: the jitter
    is injected, not randomly sampled (§24: local + deterministic)."""
    base = RETRY_BASE_DELAY_S * (2 ** (attempt - 1))
    return base * (1.0 + RETRY_JITTER_FRACTION * jitter)


def retry_read(func, *, idempotent: bool, args=(), kwargs=None,
               attempts: int = RETRY_ATTEMPTS, on_retry=None):
    """§24.3 rule 3. Retries ONLY when `idempotent` is True (idempotent reads);
    a non-idempotent call is never retried — it runs once, and a failure
    propagates. `on_retry(attempt, delay)` is an optional deterministic hook
    (a test/observer sink), never a sleep — this module performs no real
    waits, keeping behaviour reproducible and local."""
    kwargs = kwargs or {}
    if not idempotent:
        # Never retry generation/writes blindly. Run once.
        return func(*args, **kwargs)
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:                 # noqa: BLE001
            last_exc = exc
            if attempt < attempts and on_retry is not None:
                on_retry(attempt, backoff_delay(attempt))
    raise last_exc  # type: ignore[misc]
