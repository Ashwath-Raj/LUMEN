"""
Answer-correctness rubric — LUMEN_MASTER_SPEC_V3 §17.2.

§17.2 defines answer correctness as "Rubric-scored, sampled" with a ≥0.85
target, and §17.1 gives each golden question "an acceptable-answer rubric".
The RUBRIC SCORING ALGORITHM is not defined by the specification — no LLM
judge is named for evaluation, and inventing one would contradict the
deterministic-evaluation instruction. The T1 rubric is therefore a
deterministic keyword-coverage score: the fraction of the question's
acceptable-answer keywords present in the produced answer text (headline +
answer), case-insensitive.

This is disclosed configuration, not a spec value. A rubric with no keywords
scores 1.0 (nothing to satisfy). An unanswerable question is scored against
its rubric like any other — its acceptable answer is the abstention phrasing,
whose keywords ("does not support", "no", …) the rubric carries.
"""
from __future__ import annotations


def score_answer(answer_text: str, rubric: list[str]) -> float:
    """Fraction of rubric keywords present in the answer (0..1)."""
    if not rubric:
        return 1.0
    hay = answer_text.lower()
    hits = sum(1 for kw in rubric if kw.lower() in hay)
    return hits / len(rubric)
