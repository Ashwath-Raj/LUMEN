"""
Intent classification — LUMEN_MASTER_SPEC_V3 §16.2 step 1.

The intent vocabulary is fixed by §16.2:
    case | person | district | comparison | forecast | legal | network

The CLASSIFICATION RULE is not defined by the specification ("Cannot
determine") — implemented as a deterministic, ordered keyword table
(disclosed below), the T1 approach consistent with the deterministic-
fallback ethos (P12: demos fail on network, not on logic). The table is
module-level configuration; an LLM-based classifier would live behind the
provider seam in a later tier.

Priority order matters and is deliberate: comparison outranks district
("compare district A and B" is a comparison), network outranks person
("who connects A and B" is a network question), legal outranks case
("what does section 302 cover" is legal even though it mentions a section
that appears in cases). Default (nothing matches): "case" — the §2.1 spine.
"""
from __future__ import annotations

from typing import Literal

Intent = Literal["case", "person", "district", "comparison",
                 "forecast", "legal", "network"]

# Ordered (intent, keywords) table — first match wins. Configuration.
_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("comparison", ("compare", "versus", " vs ", "difference between")),
    ("network", ("connect", "network", "link between", "associat",
                 "intermediary", "who knows", "co-accused with")),
    ("legal", ("what does", "section", "act ", "ipc", "cover", "law",
               "legal", "statute", "provision")),
    ("forecast", ("forecast", "predict", "risk band", "will ", "next month",
                  "outcome probability", "likely")),
    ("comparison", ()),   # placeholder keeps table shape stable
    ("person", ("who is", "person", "history of", "dossier", "offender")),
    ("district", ("district", "jurisdiction", "statewide", "hotspot")),
    ("case", ("case", "fir", "crimeno", "crime no", "brief")),
)


def classify(question: str) -> Intent:
    """Deterministic first-match keyword classification (step 1)."""
    q = f" {question.lower().strip()} "
    for intent, keywords in _RULES:
        for kw in keywords:
            if kw in q:
                return intent  # type: ignore[return-value]
    return "case"
