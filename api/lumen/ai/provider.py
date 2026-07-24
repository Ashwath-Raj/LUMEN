"""
The ONLY LLM call site — LUMEN_MASTER_SPEC_V3 §16.1, §28 rule 5, ADR-005.

§16.1: "Primary provider is QuickML. One call site in ai/provider.py; any
other provider sits behind the same interface as a development fallback and
is declared in §26.3." §28 rule 5: "ai/provider.py is the only file that
calls an LLM."

`generate(prompt)` is that single call site. The active provider sits behind
one interface:

  * `QuickMLProvider` — the named primary (Catalyst QuickML LLM Serving).
    The specification does not document QuickML's transport/API shape, so
    the provider takes an injected `transport` callable (configured at
    deployment); unconfigured it raises `ProviderUnavailable`, which sends
    the orchestrator to §16.4's deterministic fallback — exactly the
    degradation §24 describes ("QuickML LLM down → template insights").
  * `set_provider(...)` swaps in a development fallback behind the SAME
    interface (§16.1 / §26.3) — used by tests; the prior Gemini client under
    ai/providers/ remains carried-over reference material, NOT wired here.

Nothing else in the codebase may call a model. No reasoning chains, agents,
or memory — one prompt in, one text out (§16.6: multi-agent is documented,
not built).
"""
from __future__ import annotations

from typing import Callable, Protocol


class ProviderUnavailable(Exception):
    """Generation cannot run — the orchestrator falls back (§16.4)."""


class Provider(Protocol):
    name: str

    def generate(self, prompt: str) -> str: ...


class QuickMLProvider:
    """The §16.1 primary. `transport` is the deployment-injected callable
    that performs the actual QuickML LLM-serving request (its API shape is
    not defined by the specification); without it the provider is
    unavailable and the pipeline degrades deterministically."""

    name = "quickml"

    def __init__(self, transport: Callable[[str], str] | None = None):
        self._transport = transport

    def generate(self, prompt: str) -> str:
        if self._transport is None:
            raise ProviderUnavailable(
                "QuickML LLM serving is not configured in this environment."
            )
        return self._transport(prompt)


_active: Provider = QuickMLProvider()


def set_provider(provider: Provider) -> None:
    """Swap the active provider (dev fallback behind the same interface —
    §16.1/§26.3; also the test seam)."""
    global _active
    _active = provider


def active_provider() -> Provider:
    return _active


def generate(prompt: str) -> str:
    """THE one LLM call in LUMEN (§28 rule 5)."""
    return _active.generate(prompt)
