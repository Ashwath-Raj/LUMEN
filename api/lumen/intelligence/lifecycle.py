"""
Intelligence lifecycle — LUMEN_MASTER_SPEC_V3 §10 — and Insight persistence.

    Generated → Verified → Approved → Operational → Expired → Archived → Deleted

| State         | Entered when                                            |
|---------------|---------------------------------------------------------|
| `generated`   | Producer emits it (visible to nobody — internal)        |
| `verified`    | Passes schema, evidence resolution, P9 guard, confidence floor |
| `approved`    | A District SP or State Analyst approves (T2)            |
| `operational` | Referenced in a recommendation or alert                 |
| `expired`     | Past `expires_at` or inputs changed                     |
| `archived`    | Retention window reached                                |
| `deleted`     | Governance-driven purge (deletion itself is audited)    |

§10 rules implemented here:
  * An insight NEVER skips `verified`.
  * Anything below the confidence floor (0.35) stays `generated` and never
    surfaces.
  * Approval is recorded with approver and timestamp (`approved_by`,
    `approved_at` on `lumen_insight`).
  * Inputs changing emits `InsightExpired` and triggers regeneration — the
    §19 event bus is Session 12; until it lands the transition itself is
    recorded here and the emission wires up in that session (same deferral
    the Session 7 dispute took for `PersonMatchDisputed`).

Transition legality: successors follow the §10 chain. `expired` is reachable
from `verified`, `approved`, and `operational` — §10 defines expiry by
condition ("past `expires_at` or inputs changed"), which can occur in any
surfaced state; forcing a verified-but-never-approved insight through a
fabricated approval to expire it would falsify the approval record. All other
jumps (skipping `verified`, moving backwards, deleting before `archived`) are
rejected.

The §10 `verified` gate is `verify_insight`, which enforces the DB-dependent
§8 CI invariants (3, 5, 6), the P9 factor guard (4), and the confidence floor.
Invariants 2 and 7 are already unrepresentable at the contract level
(`contracts/insight.py`); invariant 1 is enforced by the CI suite against the
API surface.

Persistence follows §3.6's `lumen_insight` verbatim. Per §28 structural rule
4, `intelligence/` is the only producer of `Insight` — this module is where
contract ↔ row conversion lives.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.contracts.insight import (
    ConfidenceBreakdown,
    Evidence,
    Factor,
    Insight,
    Lineage,
    LifecycleState,
)
from lumen.db.models.intelligence import LumenInsight
from lumen.intelligence.confidence import CONFIDENCE_FLOOR
from lumen.intelligence.explain import (
    assert_factors_clean,
    classification_satisfied,
    model_version_registered,
    unresolved_evidence,
)

# §10 chain order.
STATES: tuple[LifecycleState, ...] = (
    "generated", "verified", "approved", "operational",
    "expired", "archived", "deleted",
)

# Legal transitions (see module docstring for the expiry rationale).
LEGAL_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("generated", "verified"),
        ("verified", "approved"),
        ("approved", "operational"),
        ("verified", "expired"),
        ("approved", "expired"),
        ("operational", "expired"),
        ("expired", "archived"),
        ("archived", "deleted"),
    }
)


class IllegalTransitionError(Exception):
    """A lifecycle move outside §10's chain (e.g. skipping `verified`)."""


class VerificationFailedError(Exception):
    """The §10 `verified` gate rejected the insight; the reason names the
    failed check."""


def assert_transition(current: LifecycleState, target: LifecycleState) -> None:
    if (current, target) not in LEGAL_TRANSITIONS:
        raise IllegalTransitionError(
            f"§10: illegal lifecycle transition {current!r} → {target!r}. "
            "An insight never skips `verified`, never moves backwards, and is "
            "deleted only from `archived` by governance-driven purge."
        )


# ── The §10 `verified` gate ────────────────────────────────────────────────

def verify_insight(session: Session, insight: Insight) -> None:
    """Run the `verified` entry checks: schema (already passed — the contract
    validated on construction), evidence resolution (§8 inv 3), P9 guard
    (§8 inv 4), model registry (§8 inv 5), classification inheritance
    (§8 inv 6), and the §10 confidence floor. Raises VerificationFailedError
    naming the first failed check."""
    bad = unresolved_evidence(session, insight)
    if bad:
        raise VerificationFailedError(
            "§8 invariant 3: evidence does not resolve to a real record: "
            + ", ".join(f"{e.entity}:{e.id}" for e in bad)
        )

    assert_factors_clean(insight.factors)   # §8 invariant 4 (P9ViolationError)

    if not model_version_registered(session, insight.lineage.model_version):
        raise VerificationFailedError(
            f"§8 invariant 5: lineage.model_version "
            f"{insight.lineage.model_version!r} does not exist in "
            "lumen_model_registry."
        )

    if not classification_satisfied(insight):
        raise VerificationFailedError(
            "§8 invariant 6: insight classification "
            f"{insight.classification!r} is below the highest classification "
            "of its evidence."
        )

    if insight.confidence < CONFIDENCE_FLOOR:
        raise VerificationFailedError(
            f"§10: confidence {insight.confidence:.3f} is below the floor "
            f"({CONFIDENCE_FLOOR}); the insight stays `generated` and never "
            "surfaces."
        )


# ── Persistence (§3.6 lumen_insight, verbatim) ─────────────────────────────

def save_insight(session: Session, insight: Insight) -> LumenInsight:
    """Insert or update the §3.6 row for this insight."""
    row = session.get(LumenInsight, insight.id) or LumenInsight(insight_id=insight.id)
    row.kind = insight.kind
    row.subject_type = insight.subject_type
    row.subject_id = insight.subject_id
    row.headline = insight.headline
    row.score = insight.score
    row.confidence = insight.confidence
    row.confidence_components = insight.confidence_breakdown.model_dump()
    row.factors = [f.model_dump() for f in insight.factors]
    row.counterfactuals = list(insight.counterfactuals)
    row.evidence = [e.model_dump() for e in insight.evidence]
    row.limitations = list(insight.limitations)
    row.lineage = insight.lineage.model_dump(mode="json")
    row.contract_version = insight.contract_version
    row.lifecycle_state = insight.lifecycle_state
    row.generated_at = insight.generated_at
    row.expires_at = insight.expires_at
    session.add(row)
    session.flush()
    return row


def load_insight(session: Session, insight_id: str, *,
                 classification: str) -> Insight:
    """Rehydrate the InsightContract from its §3.6 row.

    `classification` must be supplied by the caller: §3.6's `lumen_insight`
    DDL carries no classification column (the §8 model does) — the register
    row for `lumen_insight` says it "inherits the classification of its
    subject" (§4.2), and invariant 6 re-validates it against the evidence."""
    row = session.get(LumenInsight, insight_id)
    if row is None:
        raise KeyError(f"No lumen_insight row {insight_id!r}")
    return Insight(
        id=row.insight_id,
        contract_version=row.contract_version,
        kind=row.kind,
        subject_type=row.subject_type,
        subject_id=row.subject_id,
        headline=row.headline,
        score=row.score,
        confidence=row.confidence,
        confidence_breakdown=ConfidenceBreakdown(**row.confidence_components),
        factors=[Factor(**f) for f in row.factors],
        counterfactuals=list(row.counterfactuals or []),
        evidence=[Evidence(**e) for e in row.evidence],
        limitations=list(row.limitations),
        lineage=Lineage(**row.lineage),
        lifecycle_state=row.lifecycle_state,
        classification=classification,
        generated_at=row.generated_at,
        expires_at=row.expires_at,
    )


# ── Transitions ────────────────────────────────────────────────────────────

def _move(session: Session, insight: Insight, target: LifecycleState) -> Insight:
    assert_transition(insight.lifecycle_state, target)
    updated = insight.model_copy(update={"lifecycle_state": target})
    row = session.get(LumenInsight, insight.id)
    if row is not None:
        row.lifecycle_state = target
        session.flush()
    return updated


def to_verified(session: Session, insight: Insight) -> Insight:
    """generated → verified, gated by `verify_insight` (§10: never skipped)."""
    assert_transition(insight.lifecycle_state, "verified")
    verify_insight(session, insight)
    return _move(session, insight, "verified")


def to_approved(session: Session, insight: Insight, *, approver: str,
                when: datetime | None = None) -> Insight:
    """verified → approved. §10: 'Approval is recorded with approver and
    timestamp.'"""
    updated = _move(session, insight, "approved")
    row = session.get(LumenInsight, insight.id)
    if row is not None:
        row.approved_by = approver
        row.approved_at = when or datetime.now(timezone.utc)
        session.flush()
    return updated


def to_operational(session: Session, insight: Insight) -> Insight:
    """approved → operational (entered when referenced in a recommendation
    or alert)."""
    return _move(session, insight, "operational")


def to_expired(session: Session, insight: Insight) -> Insight:
    """→ expired: past `expires_at` or inputs changed. §10 also emits
    `InsightExpired` and triggers regeneration — wired when the §19 bus lands
    (Session 12)."""
    return _move(session, insight, "expired")


def to_archived(session: Session, insight: Insight) -> Insight:
    """expired → archived (retention window reached — 180 days per §4.2)."""
    return _move(session, insight, "archived")


def to_deleted(session: Session, insight: Insight) -> Insight:
    """archived → deleted (governance-driven purge; §10: the deletion itself
    is audited — the §21 audit surface is Session 22)."""
    return _move(session, insight, "deleted")
