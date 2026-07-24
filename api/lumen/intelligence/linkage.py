"""
Case linkage — LUMEN_MASTER_SPEC_V3 §13 row 4.

    | Case linkage | Similarity | ranked linked cases | Local |

Similarity is read from the PRECOMPUTED §14 graph — the derived edges that
already encode case-to-case relatedness (SHARES_SIGNATURE with its jaccard,
PROXIMATE_TO, and shared resolved persons via ACCUSED_IN two-hop). The model
never recomputes those relationships from canonical data (§14.5: nothing runs
per request; §13: batch-score, the API reads).

DISCLOSED (cannot be determined from the specification): §13 does not define
how the similarity components combine into one rank. The rank key used is the
sum of the connecting edge weights (jaccard for signature edges, 1.0 per
proximity edge, shared-person count for person paths), with every component
reported separately in the output and as factors — no hidden weighting.

P9: none of the inputs are P9 columns (graph edges + case ids only); declared
for the guard on the columns the projection derives from.
Outputs surface as Insights (§8) — no dedicated §3.6 table for this model.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.contracts.insight import Factor
from lumen.contracts.prediction import PredictionContract
from lumen.db.models.graph import LumenGraphEdge
from lumen.intelligence.guards import assert_no_denied_columns

MODEL_NAME = "case_linkage"
MODEL_VERSION = "v1"

FEATURE_COLUMNS: list[tuple[str, str]] = [
    ("CaseMaster", "CaseMasterID"),
]


def score_case_linkage(session: Session, *, top_n: int = 10,
                       now: datetime | None = None) -> list[PredictionContract]:
    """For every case with graph-linked neighbours, the ranked linked cases."""
    for table, column in FEATURE_COLUMNS:
        assert_no_denied_columns(table, [column])
    now = now or datetime.now(timezone.utc)

    # component scores per (case, other_case)
    components: dict[tuple[str, str], dict[str, float]] = {}

    def bump(a: str, b: str, key: str, value: float) -> None:
        for pair in ((a, b), (b, a)):
            components.setdefault(pair, {}).setdefault(key, 0.0)
            components[pair][key] += value

    for e in session.query(LumenGraphEdge).filter(
            LumenGraphEdge.rel == "SHARES_SIGNATURE"):
        bump(e.src_id, e.dst_id, "signature_jaccard", float(e.weight or 0.0))
    for e in session.query(LumenGraphEdge).filter(
            LumenGraphEdge.rel == "PROXIMATE_TO"):
        bump(e.src_id, e.dst_id, "proximity", 1.0)

    # shared resolved persons: person→case ACCUSED_IN two-hop
    person_cases: dict[str, list[str]] = {}
    for e in session.query(LumenGraphEdge).filter(LumenGraphEdge.rel == "ACCUSED_IN"):
        person_cases.setdefault(e.src_id, []).append(e.dst_id)
    for cases in person_cases.values():
        cases = sorted(set(cases))
        for i in range(len(cases)):
            for j in range(i + 1, len(cases)):
                bump(cases[i], cases[j], "shared_persons", 1.0)

    by_case: dict[str, list[tuple[str, dict[str, float]]]] = {}
    for (a, b), comp in components.items():
        by_case.setdefault(a, []).append((b, comp))

    limitations = [
        "Ranked over the current precomputed graph projection window.",
        "Similarity reflects recorded charges, proximity and shared "
        "participants — not investigative confirmation of a link.",
    ]
    contracts: list[PredictionContract] = []
    for case_id in sorted(by_case, key=lambda c: (len(c), c)):
        ranked = sorted(
            by_case[case_id],
            key=lambda item: (-sum(item[1].values()), item[0]),
        )[:top_n]
        contracts.append(PredictionContract(
            model=MODEL_NAME, kind="Similarity",
            subject_type="case", subject_id=case_id,
            output={"ranked_linked_cases": [
                {"case_id": other, "similarity": round(sum(comp.values()), 4),
                 "components": {k: round(v, 4) for k, v in sorted(comp.items())}}
                for other, comp in ranked
            ]},
            factors=[Factor(label=key, weight=round(value, 4), detail=None)
                     for other, comp in ranked[:1]
                     for key, value in sorted(comp.items())],
            limitations=limitations, model_version=MODEL_VERSION, computed_at=now,
        ))
    return contracts
