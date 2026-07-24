"""
Quality scoring — LUMEN_MASTER_SPEC_V3 §5.2.

Verbatim from §5.2: "Six dimensions — completeness, validity, consistency,
integrity, uniqueness, timeliness — scored 0–1 per scope (state, district,
unit) as `1 − weighted_findings / records_in_scope`, weighted by severity
(Critical 4, High 2, Medium 1, Low 0.5)."

For a given scope and dimension:
    score = 1 − (Σ severity_weight over findings in that scope+dimension)
                / records_in_scope
clamped to [0, 1] (a scope with very poor data could otherwise go negative;
0 is the floor a 0–1 score can take). A scope with zero records has no
denominator; §5.2 does not define a score for an empty scope, so it is
omitted rather than assigned a guessed value.
"""
from __future__ import annotations

from dataclasses import dataclass

from lumen.quality.engine import EngineResult
from lumen.quality.rules import DIMENSIONS, SEVERITY_WEIGHT


@dataclass(frozen=True)
class ScopeScore:
    scope_type: str          # "state" | "district" | "unit"
    scope_id: str
    dimension: str
    score: float             # 0..1


def _score_one(weighted_findings: float, records_in_scope: int) -> float:
    if records_in_scope <= 0:
        raise ValueError("records_in_scope must be positive")
    raw = 1.0 - (weighted_findings / records_in_scope)
    return max(0.0, min(1.0, raw))


def compute_scores(result: EngineResult) -> list[ScopeScore]:
    """Produce a ScopeScore per (scope, dimension) with a positive record
    count. State scope is the whole dataset; district and unit scopes come
    from the engine's per-scope record counts."""
    # weighted findings per (scope_type, scope_id, dimension)
    weighted: dict[tuple[str, str, str], float] = {}

    def add(scope_type: str, scope_id: str, dimension: str, weight: float) -> None:
        weighted[(scope_type, scope_id, dimension)] = weighted.get((scope_type, scope_id, dimension), 0.0) + weight

    for f in result.findings:
        w = SEVERITY_WEIGHT[f.severity]
        # State scope always accrues every finding.
        add("state", "karnataka", f.dimension, w)
        # District/unit scopes accrue findings for cases they contain.
        # Only CaseMaster-attributable findings map cleanly to a scope; a
        # finding whose entity is a case-child still carries the case id in
        # its detail, but §5.2's denominator is "records_in_scope" (cases),
        # so we attribute via the CaseMaster the finding is about when the
        # entity itself is a CaseMaster, and via detail's case id otherwise.
        case_id = _finding_case_id(f)
        if case_id is not None:
            did = result.case_district.get(case_id)
            uid = result.case_unit.get(case_id)
            if did is not None:
                add("district", str(did), f.dimension, w)
            if uid is not None:
                add("unit", str(uid), f.dimension, w)

    scores: list[ScopeScore] = []

    # State scope
    for dim in DIMENSIONS:
        wf = weighted.get(("state", "karnataka", dim), 0.0)
        scores.append(ScopeScore("state", "karnataka", dim, _score_one(wf, result.state_records)))

    # District scope
    for district_id, records in result.district_records.items():
        for dim in DIMENSIONS:
            wf = weighted.get(("district", str(district_id), dim), 0.0)
            scores.append(ScopeScore("district", str(district_id), dim, _score_one(wf, records)))

    # Unit scope
    for unit_id, records in result.unit_records.items():
        for dim in DIMENSIONS:
            wf = weighted.get(("unit", str(unit_id), dim), 0.0)
            scores.append(ScopeScore("unit", str(unit_id), dim, _score_one(wf, records)))

    return scores


def _finding_case_id(f) -> int | None:
    """Best-effort case attribution: the finding's entity_id if it is a
    CaseMaster, otherwise a case id carried in its detail."""
    if f.entity_type == "CaseMaster":
        try:
            return int(f.entity_id)
        except (TypeError, ValueError):
            return None
    for key in ("orphan_case_master_id", "case_master_id", "duplicate_of"):
        if key in f.detail and f.detail[key] is not None:
            try:
                return int(f.detail[key])
            except (TypeError, ValueError):
                return None
    # Findings on case-children (Q07 chargesheet, Q08 arrest, Q13 on a
    # victim, Q17 association) carry the child id, not the case id, in
    # entity_id. Their state-scope contribution is still counted; district/
    # unit attribution for these is not derivable from the finding alone
    # without a second lookup, which §5.2 does not require for the score
    # denominator (cases). They contribute to state scope only.
    return None
