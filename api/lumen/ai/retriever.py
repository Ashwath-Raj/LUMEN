"""
Evidence retrieval — LUMEN_MASTER_SPEC_V3 §16.2 steps 2, 3, 5.

Step 2 — entity resolution: surface names → canonical IDs (§6's resolved
persons; numeric case references). Step 3 — the caller's scope is applied
BEFORE retrieval (§20 scope, same district-set model as §15 retrieval).
Step 5 — the bundle: canonical rows + persisted Insights + KB chunks,
ranked, token-capped (§16.5's per-request token budget; no tokenizer is
specified, so the budget counts whitespace words — the Session 13
disclosure).

The bundle records every retrievable ID — the step-9 filter's ground truth:
anything the model cites outside `bundle.ids` is dropped.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from lumen.ai.toolsel import ToolSelection
from lumen.db.models import canonical as m
from lumen.db.models.identity import LumenPerson
from lumen.db.models.intelligence import LumenInsight
from lumen.db.models.prediction import LumenDistrictRisk
from lumen.kb.retrieve import retrieve as kb_retrieve

DEFAULT_TOKEN_BUDGET = 1200      # §16.5 token budget per request (config)


@dataclass
class Bundle:
    """The retrieved evidence bundle (step 5)."""
    ids: set[str] = field(default_factory=set)        # every citable ID
    lines: list[str] = field(default_factory=list)    # rendered evidence text
    kb_doc_ids: list[str] = field(default_factory=list)
    kb_classifications: list[str] = field(default_factory=list)
    insight_ids: list[str] = field(default_factory=list)
    case_ids: list[str] = field(default_factory=list)
    person_ids: list[str] = field(default_factory=list)
    expected: int = 0                                  # for §9 evidence_quality

    def text(self, *, token_budget: int = DEFAULT_TOKEN_BUDGET) -> str:
        """Token-capped rendering (§16.5): lines are included in rank order
        until the word budget is exhausted."""
        out: list[str] = []
        used = 0
        for line in self.lines:
            words = len(line.split())
            if out and used + words > token_budget:
                break
            out.append(line)
            used += words
        return "\n".join(out)


def resolve_entities(session: Session, question: str) -> tuple[list[str], list[int]]:
    """Step 2: surface names → canonical IDs. Person names match resolved
    `lumen_person.canonical_name` (§6); case references match numeric
    CaseMasterIDs present in the question."""
    q = question.lower()
    person_ids = [p.person_id for p in session.query(LumenPerson)
                  .order_by(LumenPerson.person_id)
                  if p.canonical_name and p.canonical_name.lower() in q]
    case_ids = []
    for token in re.findall(r"\b\d{3,}\b", question):
        if session.get(m.CaseMaster, int(token)) is not None:
            case_ids.append(int(token))
    return person_ids, case_ids


def build_bundle(session: Session, question: str, tools: ToolSelection, *,
                 district_scope: list[int] | None = None,
                 k: int = 5) -> Bundle:
    """Steps 3+5: scope-filtered retrieval into one ranked, cappable bundle."""
    bundle = Bundle()
    person_ids, case_ids = resolve_entities(session, question)

    # canonical rows for explicitly referenced entities
    for pid in person_ids:
        person = session.get(LumenPerson, pid)
        bundle.ids.add(pid)
        bundle.person_ids.append(pid)
        bundle.lines.append(
            f"[person {pid}] {person.canonical_name} — associated with "
            f"{person.case_count or 0} case record(s), resolution confidence "
            f"{person.resolution_confidence}.")
    for cid in case_ids:
        case = session.get(m.CaseMaster, cid)
        sid = str(cid)
        bundle.ids.add(sid)
        bundle.case_ids.append(sid)
        brief = (case.BriefFacts or "").strip()
        bundle.lines.append(f"[case {sid}] CrimeNo {case.CrimeNo}: {brief}")

    # KB chunks per selected index — §15 scope filtering applies inside
    for index in tools.kb_indexes:
        result = kb_retrieve(session, question, index=index,
                             district_scope=district_scope, k=k)
        for chunk in result.chunks:
            bundle.ids.add(chunk.doc_id)
            bundle.kb_doc_ids.append(chunk.doc_id)
            bundle.kb_classifications.append(chunk.classification)
            bundle.lines.append(f"[kb {chunk.doc_id}] {chunk.text}")

    # persisted insights (verified or generated) for referenced subjects
    if tools.include_insights:
        rows = (session.query(LumenInsight)
                .order_by(LumenInsight.insight_id).limit(50).all())
        wanted_subjects = set(bundle.case_ids) | set(bundle.person_ids)
        for row in rows:
            if wanted_subjects and row.subject_id not in wanted_subjects:
                continue
            if not wanted_subjects and row.kind not in ("risk", "anomaly"):
                continue
            bundle.ids.add(row.insight_id)
            bundle.insight_ids.append(row.insight_id)
            bundle.lines.append(f"[insight {row.insight_id}] {row.headline}")

    # prediction tables per tool selection
    if "district_risk" in tools.prediction_sources:
        for r in session.query(LumenDistrictRisk).order_by(LumenDistrictRisk.district_id):
            if district_scope is not None and r.district_id not in district_scope:
                continue          # step 3: scope before retrieval output
            rid = f"district_risk:{r.district_id}"
            bundle.ids.add(rid)
            bundle.lines.append(
                f"[{rid}] District {r.district_id} risk band {r.band} "
                f"(score {r.score:.2f}, window {r.window_start}).")

    bundle.expected = max(1, k * max(1, len(tools.kb_indexes))
                          + len(person_ids) + len(case_ids))
    return bundle
