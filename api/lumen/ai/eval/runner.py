"""
Golden-set + adversarial eval runner — LUMEN_MASTER_SPEC_V3 §17.

Runs every §17.1 golden question and every §17.3 adversarial case through the
Session-14 orchestrator (`ai.orchestrator.ask` — consumed, never duplicated),
computes the §17.2 metrics, writes one `lumen_ai_eval` row per golden
question, and returns a `Scorecard` (which `scripts/eval.py` prints — §17.4's
"make eval prints a scorecard", the done-when).

Execution model (disclosed, per the confirmed scope decision): the suite runs
IN-PROCESS against the orchestrator function, not over HTTP against a deployed
API — no deployment exists in this environment, and §16.4's fallback path
(QuickML absent) is the code path the demo itself runs on. The metrics are
computed from the §14 `AskOutcome`'s additive run metadata (intent,
bundle_ids, cited_ids, dropped_ids, method) — nothing re-runs the pipeline.

§17.2 metrics, computed exactly per their definitions:
  groundedness       cited IDs present in the retrieved bundle ÷ IDs cited
                     (1.0 when nothing was cited — no citation, no violation)
  hallucinated_ids   IDs dropped by step 9 (the pre-filter model-quality
                     signal); reported per-question and summed per 100 Q
  retrieval_coverage expected IDs retrieved ÷ expected (1.0 when a question
                     declares no expected IDs)
  intent_accuracy    correct intent classifications ÷ classified questions
  abstention_rate    unanswerable questions correctly declined/abstained ÷
                     unanswerable questions
  answer_correctness mean rubric score (§17.2 "rubric-scored")
  p95_latency_ms     95th percentile end-to-end latency
  fallback_rate      deterministic_fallback invocations ÷ questions

Determinism: with a fixed provider (QuickML absent → fallback, or an injected
scripted provider) and the fixed seed, every metric is reproducible. `run_id`
and timestamps are injected by the caller so the store rows are deterministic
in tests.
"""
from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from lumen.ai import orchestrator
from lumen.ai.eval.adversarial import ADVERSARIAL_CASES, AdversarialCase
from lumen.ai.eval.rubric import score_answer
from lumen.db.models.eval import LumenAiEval

GOLDEN_PATH = (Path(__file__).resolve().parents[4] / "data" / "eval" / "golden.yaml")

# §17.2 targets — reproduced verbatim for the scorecard's pass/fail column.
TARGETS = {
    "groundedness": 1.00,
    "retrieval_coverage": 0.85,
    "intent_accuracy": 0.90,
    "abstention_rate": 0.90,
    "answer_correctness": 0.85,
    "p95_latency_ms": 6000.0,        # ≤ 6 s
}


@dataclass
class QuestionResult:
    question_id: str
    category: str
    intent_ok: bool
    groundedness: float
    coverage: float
    correctness: float
    hallucinated_ids: int
    latency_ms: float
    method: str
    abstained: bool


@dataclass
class AdversarialResult:
    case_id: str
    failure_mode: str
    passed: bool
    detail: str


@dataclass
class Scorecard:
    run_id: str
    question_count: int
    groundedness: float
    hallucinated_ids_per_100: float
    retrieval_coverage: float
    intent_accuracy: float
    abstention_rate: float
    answer_correctness: float
    p95_latency_ms: float
    fallback_rate: float
    adversarial_passed: int
    adversarial_total: int
    per_question: list[QuestionResult] = field(default_factory=list)
    adversarial: list[AdversarialResult] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def load_golden(path: Path = GOLDEN_PATH) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("questions", []))


def _answer_text(outcome) -> str:
    return f"{outcome.insight.headline}"


def _abstained(outcome) -> bool:
    """A question is 'declined/abstained' when the pipeline declined it, or the
    fallback abstained (no grounded answer) — §17.1 unanswerable correctness."""
    if outcome.method == "declined":
        return True
    return any("does not support" in l.lower() for l in outcome.insight.limitations) \
        or "does not support" in outcome.insight.headline.lower()


def evaluate_golden(session: Session, questions: list[dict]) -> list[QuestionResult]:
    results: list[QuestionResult] = []
    for q in questions:
        outcome = orchestrator.ask(session, q["question"],
                                   district_scope=q.get("district_scope"))
        cited = outcome.cited_ids
        bundle = set(outcome.bundle_ids)
        # groundedness: cited present in bundle ÷ cited (step 9 guarantees 1.0)
        groundedness = 1.0 if not cited else \
            sum(1 for c in cited if c in bundle) / len(cited)
        # retrieval coverage: expected retrieved ÷ expected
        expected = q.get("expected_entity_ids") or []
        coverage = 1.0 if not expected else \
            sum(1 for e in expected if e in bundle) / len(expected)
        intent_ok = (outcome.intent == q.get("expected_intent")) \
            if outcome.intent is not None else False
        correctness = score_answer(_answer_text(outcome), q.get("rubric") or [])
        results.append(QuestionResult(
            question_id=q["id"], category=q["category"], intent_ok=intent_ok,
            groundedness=groundedness, coverage=coverage, correctness=correctness,
            hallucinated_ids=len(outcome.dropped_ids), latency_ms=outcome.latency_ms,
            method=outcome.method, abstained=_abstained(outcome)))
    return results


def evaluate_adversarial(session: Session,
                         cases: tuple[AdversarialCase, ...] = ADVERSARIAL_CASES
                         ) -> list[AdversarialResult]:
    out: list[AdversarialResult] = []
    for case in cases:
        outcome = orchestrator.ask(session, case.question,
                                   district_scope=case.district_scope)
        cited = {e.id for e in outcome.insight.evidence}
        ok = True
        detail = "ok"
        if case.must_decline and outcome.method != "declined":
            ok, detail = False, f"not declined (method={outcome.method})"
        for forbidden in case.must_not_cite:
            if forbidden in cited:
                ok, detail = False, f"leaked forbidden id {forbidden}"
        out.append(AdversarialResult(case_id=case.id,
                                     failure_mode=case.failure_mode,
                                     passed=ok, detail=detail))
    return out


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))
    return ordered[idx]


def run_eval(session: Session, *, run_id: str,
             now: datetime | None = None,
             golden_path: Path = GOLDEN_PATH) -> Scorecard:
    """Run the full §17 suite, persist lumen_ai_eval, return the scorecard."""
    now = now or datetime.now(timezone.utc)
    questions = load_golden(golden_path)
    per_q = evaluate_golden(session, questions)
    adversarial = evaluate_adversarial(session)

    n = len(per_q)
    unanswerable = [q for q in questions if q.get("unanswerable")]
    unanswerable_ids = {q["id"] for q in unanswerable}
    correct_abstentions = sum(
        1 for r in per_q if r.question_id in unanswerable_ids and r.abstained)

    scorecard = Scorecard(
        run_id=run_id,
        question_count=n,
        groundedness=statistics.mean([r.groundedness for r in per_q]) if n else 1.0,
        hallucinated_ids_per_100=(sum(r.hallucinated_ids for r in per_q) / n * 100) if n else 0.0,
        retrieval_coverage=statistics.mean([r.coverage for r in per_q]) if n else 1.0,
        intent_accuracy=(sum(1 for r in per_q if r.intent_ok) / n) if n else 0.0,
        abstention_rate=(correct_abstentions / len(unanswerable)) if unanswerable else 1.0,
        answer_correctness=statistics.mean([r.correctness for r in per_q]) if n else 1.0,
        p95_latency_ms=_p95([r.latency_ms for r in per_q]),
        fallback_rate=(sum(1 for r in per_q if r.method == "deterministic_fallback") / n) if n else 0.0,
        adversarial_passed=sum(1 for a in adversarial if a.passed),
        adversarial_total=len(adversarial),
        per_question=per_q,
        adversarial=adversarial,
    )

    # §17.4: write lumen_ai_eval — one row per golden question per run.
    for r in per_q:
        session.merge(LumenAiEval(
            eval_id=f"{run_id}:{r.question_id}", run_id=run_id,
            question_id=r.question_id, groundedness=r.groundedness,
            correctness=r.correctness, hallucinated_ids=r.hallucinated_ids,
            latency_ms=r.latency_ms, prompt_version=orchestrator.PROMPT_VERSION,
            evaluated_at=now))
    session.commit()
    return scorecard


def format_scorecard(scorecard: Scorecard) -> str:
    """The printable §17.4 scorecard (the done-when output)."""
    def line(name, value, target=None, higher_better=True, fmt="{:.3f}"):
        val = fmt.format(value)
        if target is None:
            return f"  {name:<22} {val}"
        ok = value >= target if higher_better else value <= target
        return f"  {name:<22} {val:<10} target {target}  [{'PASS' if ok else 'FAIL'}]"

    lines = [
        "=" * 60,
        f"LUMEN AI evaluation scorecard — run {scorecard.run_id}",
        f"golden questions: {scorecard.question_count}",
        "-" * 60,
        line("groundedness", scorecard.groundedness, TARGETS["groundedness"]),
        line("retrieval_coverage", scorecard.retrieval_coverage, TARGETS["retrieval_coverage"]),
        line("intent_accuracy", scorecard.intent_accuracy, TARGETS["intent_accuracy"]),
        line("abstention_rate", scorecard.abstention_rate, TARGETS["abstention_rate"]),
        line("answer_correctness", scorecard.answer_correctness, TARGETS["answer_correctness"]),
        line("p95_latency_ms", scorecard.p95_latency_ms, TARGETS["p95_latency_ms"],
             higher_better=False, fmt="{:.1f}"),
        line("hallucinated_ids/100Q", scorecard.hallucinated_ids_per_100, fmt="{:.1f}"),
        line("fallback_rate", scorecard.fallback_rate),
        "-" * 60,
        f"  adversarial            {scorecard.adversarial_passed}/{scorecard.adversarial_total} passed",
    ]
    for a in scorecard.adversarial:
        mark = "PASS" if a.passed else "FAIL"
        lines.append(f"    [{mark}] {a.failure_mode}: {a.detail}")
    lines.append("=" * 60)
    return "\n".join(lines)
