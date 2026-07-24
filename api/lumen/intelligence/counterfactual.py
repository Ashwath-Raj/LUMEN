"""
Counterfactual generation — LUMEN_MASTER_SPEC_V3 §8 field, §33 row 10
done-when, §30.4/§30.8 surfaces.

Everything the specification says about counterfactuals:
  * §8:   `counterfactuals: list[str]` on Insight — plain strings.
  * §3.6: `counterfactuals JSON` on lumen_insight (exists since Session 8).
  * §28:  this module is their designated home.
  * §30.4/§30.8: shown under Risk insights and Forecast rows.
  * §33 row 10: "Insights carry factors, counterfactuals, limitations."

The specification defines NO generation algorithm, no wording, no trigger
rule, no validation, and no dedicated contract or table ("Cannot determine
from the specification" — recorded in the Session 11 report). Per
instruction, everything undefined is exposed as configuration:

  * `DEFAULT_KINDS` — which insight kinds receive counterfactuals. Default
    ("risk", "forecast"): the two kinds whose UI surfaces mandate them
    (§30.4, §30.8).
  * `DEFAULT_TOP_K` — how many factors ground sentences (top by |weight|,
    the natural reading of feature importance; the one ordering assumption).
  * `DEFAULT_TEMPLATE` — the sentence wording. Authored text: the spec
    mandates presence, not phrasing (the Session 9 precedent for mandated-
    but-unworded lines). The default is deliberately model-relative and
    non-causal — it states what the model's support rests on, never a
    real-world intervention (P3/§11: never present an inference as fact,
    no autonomous prescriptions).

Guarantees enforced here (CI-tested):
  * Deterministic: same factors → same sentences, always.
  * Non-blank: a generated counterfactual is never an empty string.
  * P9: generated text derives from factor labels, so the §4.3 rule-6 guard
    is applied to it — a P9-referencing factor label fails generation
    rather than leaking into display text (mirrors §8 invariant 4).

No causal model, no recommendation or intervention logic, no optimisation,
no ranking beyond the disclosed |weight| ordering.
"""
from __future__ import annotations

from lumen.contracts.insight import Factor
from lumen.intelligence.explain import factor_references_p9
from lumen.intelligence.guards import P9ViolationError

# ── configuration (all spec-undefined; see module docstring) ───────────────
DEFAULT_KINDS: tuple[str, ...] = ("risk", "forecast")   # §30.4 + §30.8 surfaces
DEFAULT_TOP_K: int = 3
DEFAULT_TEMPLATE: str = (
    "Without the contribution of {label} (weight {weight}), the model's "
    "support for this finding would weaken."
)


def eligible(kind: str, *, kinds: tuple[str, ...] = DEFAULT_KINDS) -> bool:
    """Whether an insight kind receives generated counterfactuals."""
    return kind in kinds


def generate_counterfactuals(
    factors: list[Factor],
    *,
    top_k: int = DEFAULT_TOP_K,
    template: str = DEFAULT_TEMPLATE,
) -> list[str]:
    """One plain sentence per top factor (by |weight|, descending; ties by
    label for determinism). Empty factors → empty list — §8 places no
    never-empty invariant on counterfactuals (unlike limitations)."""
    ranked = sorted(factors, key=lambda f: (-abs(f.weight), f.label))
    sentences: list[str] = []
    for factor in ranked[:top_k]:
        term = factor_references_p9(factor)
        if term is not None:
            raise P9ViolationError(
                f"Counterfactual generation refused: factor label "
                f"{factor.label!r} references the P9-protected attribute "
                f"{term!r} (P9, §4.3 rule 6 — protected attributes never "
                "reach display text)."
            )
        sentence = template.format(label=factor.label, weight=round(factor.weight, 4))
        if not sentence.strip():
            raise ValueError("Counterfactual template produced a blank sentence.")
        sentences.append(sentence)
    return sentences


def counterfactuals_for(kind: str, factors: list[Factor], *,
                        kinds: tuple[str, ...] = DEFAULT_KINDS,
                        top_k: int = DEFAULT_TOP_K,
                        template: str = DEFAULT_TEMPLATE) -> list[str]:
    """The engine-facing entry point: generated sentences for eligible
    kinds, an empty list otherwise."""
    if not eligible(kind, kinds=kinds):
        return []
    return generate_counterfactuals(factors, top_k=top_k, template=template)
