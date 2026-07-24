# ADR-005 — QuickML as the primary LLM provider

**Status:** Accepted (architecture frozen at v3, §37).

## Context

LUMEN must be Catalyst-native (P6): where Catalyst provides a managed service
for a capability, that service is used, and exceptions are registered in §26.3.
The organisers map *Text LLMs / RAG / knowledge bases* to **Catalyst QuickML
(LLM Serving, RAG)** (§16.1). A third-party LLM (Gemini, OpenAI) is an available
alternative to a Catalyst service, and is therefore the clearest single point
of disqualification: "Building the demo on Gemini is the most likely single
point of disqualification in this project" (§16.1).

## Decision

**QuickML is the primary LLM provider.** There is **one call site** in
`ai/provider.py` (§28 rule 5). Any other provider sits behind the same
interface as a **development fallback** and is declared in §26.3.

## Alternatives Considered

- **Gemini** — third-party LLM.
- **OpenAI** — third-party LLM.

## Consequences

- The organisers require Catalyst services where equivalents exist; a
  third-party LLM is the clearest substitution risk in the build.
- `ai/provider.py` is the only file that calls an LLM (§28 rule 5); the
  QuickML client and any dev-fallback provider share one interface.
- A non-Catalyst LLM is registered in the §26.3 P6 exception register as
  "Local development only. Never the deployed path."
- When generation is unavailable, the pipeline degrades to the deterministic
  fallback (§16.4, §24.1), not to a different provider.

## Specification references

§16.1 (provider decision), §16.4 (deterministic fallback), §26.3 (P6 exception
register), §28 structural rule 5, P6, §35 ADR-005.
