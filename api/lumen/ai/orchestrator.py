"""
AI orchestrator — LUMEN_MASTER_SPEC_V3 §16.2: the twelve-step pipeline.

    1 intent → 2 entity resolution → 3 scope filter → 4 tool selection
    → 5 retrieval → 6 prompt assembly → 7 generation → 8 schema validation
    → 9 evidence verify (DROP any ID not in the bundle — hard filter)
    → 10 confidence → 11 P9 guard → 12 audit → Insight(kind="summary")

Step boundaries map to the §28 module layout: 1 intent.py · 2/3/5
retriever.py · 4 toolsel.py · 6/8/9 envelope.py · 7 provider.py (the only
LLM call site) · 10 §9 confidence · 11 §4.3 r6 guard · 12 the §19 bus
(`AIQueryExecuted`; the `lumen_audit` table itself is §21/Session 22 — the
event store is the audit path available now, disclosed).

§16.4 deterministic fallback: when generation is unavailable or twice fails
schema validation (step 8 allows exactly one retry), the answer is
template-assembled from the retrieved bundle and persisted insights, marked
`method: "deterministic_fallback"` in lineage — built exactly as P12 asks.

§16.5: the token budget is applied when rendering the bundle. Gateway rate
limiting and the 15-minute answer Cache are Catalyst infrastructure
(Session 21) — not implemented here, disclosed.

§16.6: one orchestrator with tool selection. No agents, no supervisor, no
memory — documented as the scaling path, not built.

The multi-step prior-generation facade under ai/services/ remains carried-
over reference material; this pipeline replaces nothing that was live.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.ai import envelope, provider, retriever, toolsel
from lumen.ai.intent import classify
from lumen.bus import signals
from lumen.contracts.event import EventContract, Subject
from lumen.contracts.insight import Evidence, Factor, Insight, Lineage
from lumen.db.models.intelligence import LumenModelRegistry
from lumen.governance.classification import CLASSIFICATION_ORDER
from lumen.intelligence import confidence as C
from lumen.intelligence.explain import classification_of_evidence, factor_references_p9
from lumen.intelligence.lifecycle import save_insight

_NS = uuid.UUID("a1b20000-0000-4000-8000-000000000016")

PROMPT_NAME = "ask_summary"
PROMPT_VERSION = "v1"
METHOD_NAME = "ai_orchestrator"
MODEL_VERSION = "v1"

# §11 / §17.3: requests for protected attributes or individual-criminality
# prediction are declined.
DECLINE_P9 = ("This question involves protected attributes (caste, religion, "
              "blood group, disability status), which LUMEN never analyses.")
DECLINE_INDIVIDUAL = ("LUMEN does not predict individual criminality or rank "
                      "individuals by likelihood of offending.")
BASE_LIMITATION = "AI-assembled answer; verify against the cited source records."
LEGAL_BASIS_LIMITATION = "Answer rests on legal text rather than case evidence."
FALLBACK_LIMITATION = ("Deterministic fallback: generation was unavailable; this "
                       "answer is template-assembled from retrieved evidence.")
NO_EVIDENCE_LIMITATION = "The retrieved data does not support a grounded answer."

_INDIVIDUAL_PREDICTION_MARKERS = ("will he commit", "will she commit",
                                  "will they commit", "likely to offend",
                                  "predict whether", "future criminality",
                                  "commit a crime again")


@dataclass
class AskOutcome:
    insight: Insight
    method: str                     # "quickml" | "deterministic_fallback" | "declined"
    dropped_ids: list[str]          # §16.2 step 9 casualties (§17.2 signal)
    latency_ms: float


def _text_references_p9(text: str) -> str | None:
    """Step 11 helper — reuse the §8 invariant-4 checker on arbitrary text."""
    return factor_references_p9(Factor(label=text, weight=0.0, detail=None))


def _chips(session: Session, bundle: retriever.Bundle, kept: set[str]) -> list[Evidence]:
    chips: list[Evidence] = []
    for cid in bundle.case_ids:
        if cid in kept:
            chips.append(Evidence(entity="case", id=cid, label=f"Case {cid}",
                                  url=f"/cases/{cid}"))
    for pid in bundle.person_ids:
        if pid in kept:
            chips.append(Evidence(entity="person", id=pid, label=pid,
                                  url=f"/persons/{pid}"))
    for did in bundle.kb_doc_ids:
        if did in kept and not any(c.id == did for c in chips):
            chips.append(Evidence(entity="kb_document", id=did, label=did,
                                  url=f"/kb/{did}"))
    return chips


def ask(session: Session, question: str, *,
        district_scope: list[int] | None = None,
        actor_id: str = "user",
        token_budget: int = retriever.DEFAULT_TOKEN_BUDGET,
        now: datetime | None = None) -> AskOutcome:
    """The §16.2 pipeline. Returns the Insight plus run metadata (the router
    serialises only the insight — §16.2's stated output)."""
    now = now or datetime.now(timezone.utc)
    started = time.perf_counter()

    # step 11 (question side, checked first): P9 requests are declined —
    # protected attributes never even reach retrieval as query intent (§17.3).
    p9_term = _text_references_p9(question)
    lowered = question.lower()
    individual = any(marker in lowered for marker in _INDIVIDUAL_PREDICTION_MARKERS)
    if p9_term is not None or individual:
        reason = DECLINE_P9 if p9_term is not None else DECLINE_INDIVIDUAL
        insight = _build_insight(session, question, headline=reason,
                                 chips=[], kb_classifications=[],
                                 bundle=None, method="declined",
                                 limitations=[reason, BASE_LIMITATION],
                                 abstained=True, now=now)
        return _finish(session, insight, "declined", [], started,
                       question, actor_id, now)

    # 1 intent · 4 tools
    intent = classify(question)
    tools = toolsel.select(intent)

    # 2 entities · 3 scope · 5 retrieval (scope applied BEFORE retrieval)
    bundle = retriever.build_bundle(session, question, tools,
                                    district_scope=district_scope)

    # 6 prompt assembly (§16.3 registry — idempotent, kept out of app startup
    # to preserve the boots-without-DB guarantee; disclosed)
    envelope.register_prompts(session, now=now)
    prompt = envelope.assemble(PROMPT_NAME, PROMPT_VERSION, question=question,
                               evidence=bundle.text(token_budget=token_budget))

    # 7 generation · 8 schema validation (one retry) · §16.4 fallback
    generation = None
    method = "quickml"
    try:
        for attempt in (1, 2):                      # one retry, then fallback
            try:
                generation = envelope.parse_generation(provider.generate(prompt))
                break
            except ValueError:
                if attempt == 2:
                    generation = None
    except provider.ProviderUnavailable:
        generation = None
    if generation is None:
        method = "deterministic_fallback"
        generation = _fallback_generation(question, bundle)

    # 9 evidence verify — THE hard filter: drop every ID not in the bundle
    kept, dropped = envelope.verify_cited_ids(generation.cited_ids, bundle.ids)

    # 11 P9 guard over output text
    if _text_references_p9(generation.headline + " " + generation.answer):
        generation = envelope.Generation(
            headline=DECLINE_P9, answer=DECLINE_P9, cited_ids=[], abstained=True)
        kept, dropped = [], dropped
        method = "declined"

    limitations = [BASE_LIMITATION]
    if generation.abstained or (not kept and method != "declined"):
        limitations.append(NO_EVIDENCE_LIMITATION)
    if method == "deterministic_fallback":
        limitations.append(FALLBACK_LIMITATION)
    if bundle.kb_doc_ids and not bundle.case_ids and any(
            not d.startswith("case_brief:") for d in bundle.kb_doc_ids):
        limitations.append(LEGAL_BASIS_LIMITATION)       # §15.2 rule 5

    chips = _chips(session, bundle, set(kept))
    insight = _build_insight(session, question,
                             headline=generation.headline, chips=chips,
                             kb_classifications=bundle.kb_classifications,
                             bundle=bundle, method=method,
                             limitations=limitations,
                             abstained=generation.abstained, now=now,
                             kept=kept, tools=tools)
    return _finish(session, insight, method, dropped, started,
                   question, actor_id, now)


def _fallback_generation(question: str, bundle: retriever.Bundle) -> envelope.Generation:
    """§16.4: template-assembled from retrieved evidence + existing insights."""
    if not bundle.lines:
        return envelope.Generation(
            headline="The data does not support an answer to this question.",
            answer="No in-scope evidence was retrieved for this question.",
            cited_ids=[], abstained=True)
    top = bundle.lines[:5]
    return envelope.Generation(
        headline=f"Evidence-based summary for: {question}",
        answer=" ".join(top),
        cited_ids=sorted(bundle.ids)[:10],
        abstained=False)


def _build_insight(session, question, *, headline, chips, kb_classifications,
                   bundle, method, limitations, abstained, now,
                   kept: list[str] | None = None,
                   tools=None) -> Insight:
    session.merge(LumenModelRegistry(
        model_id=f"{METHOD_NAME}@{MODEL_VERSION}", name=METHOD_NAME, kind="ai",
        version=MODEL_VERSION, params={}, metrics={}, trained_at=now, active=True))

    retrieved = len(bundle.lines) if bundle is not None else 0
    expected = bundle.expected if bundle is not None else 1
    scope = ("state", "karnataka")
    breakdown = C.compose(
        evidence_quality=C.evidence_quality(retrieved, expected),
        data_completeness=C.data_completeness(session, *scope),
        identity_confidence=C.identity_confidence(session, chips),
    )
    classification = "INTERNAL"
    if chips:
        classification = max((classification_of_evidence(e) for e in chips),
                             key=lambda c: CLASSIFICATION_ORDER[c])
    subject_type, subject_id = "state", "karnataka"
    if bundle is not None and bundle.case_ids:
        subject_type, subject_id = "case", bundle.case_ids[0]
    elif bundle is not None and bundle.person_ids:
        subject_type, subject_id = "person", bundle.person_ids[0]

    return Insight(
        id=str(uuid.uuid5(_NS, f"ask:{question}:{subject_type}:{subject_id}")),
        kind="summary",                       # §16.2's output kind
        subject_type=subject_type, subject_id=subject_id,
        headline=headline[:400],
        score=None,
        confidence=breakdown.composite,
        confidence_breakdown=breakdown,
        factors=[],
        counterfactuals=[],
        evidence=chips,
        limitations=limitations,
        lineage=Lineage(
            method=METHOD_NAME if method == "quickml" else method,
            model_version=MODEL_VERSION,
            prompt_version=PROMPT_VERSION,     # §16.3: every AI insight records it
            features_used=[],
            query_ids=list(tools.graph_queries) if tools is not None else [],
            source_row_count=retrieved,
            quality_score=C.data_completeness(session, *scope),
            computed_at=now,
        ),
        lifecycle_state="generated",
        classification=classification,
        generated_at=now,
    )


def _finish(session, insight, method, dropped, started, question,
            actor_id, now) -> AskOutcome:
    save_insight(session, insight)
    latency_ms = (time.perf_counter() - started) * 1000.0

    # 12 audit: AIQueryExecuted on the §19 bus + append-only store. The
    # lumen_audit table is §21 (Session 22); the event is the audit path now.
    signals.publish(session, EventContract(
        event_id=str(uuid.uuid4()),           # an occurrence, not a derivation
        event_type="AIQueryExecuted",
        occurred_at=now,
        actor_id=actor_id,
        subject=Subject(type=insight.subject_type, id=insight.subject_id),
        payload={"question": question, "prompt_version": PROMPT_VERSION,
                 "evidence_ids": [e.id for e in insight.evidence],
                 "dropped_id_count": len(dropped),   # §17.2 pre-filter signal
                 "method": method, "latency_ms": round(latency_ms, 1)},
        trace_id=str(uuid.uuid4()),
        classification="INTERNAL",
    ))
    session.commit()
    return AskOutcome(insight=insight, method=method, dropped_ids=dropped,
                      latency_ms=latency_ms)
