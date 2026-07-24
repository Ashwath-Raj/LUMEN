"""
Case outcome — LUMEN_MASTER_SPEC_V3 §13 row 5.

    | Case outcome | Classification | P(cstype ∈ A/B/C) + factors | Zia AutoML |

§13 names only Zia AutoML for this row; Zia is Catalyst adoption (T2,
Session 23) and excluded from this session. DISCLOSED: no local path is
specified — the scikit-learn tree-ensemble fallback §13 names for the risk
row is mirrored here (same rationale: tree ensembles → feature importances →
`factors`), pending the Zia AutoML path. This is an interpolation, recorded
as such, not a spec value.

Training data: cases with a `ChargesheetDetails.cstype` label — 'A'
chargesheet / 'B' false / 'C' undetected (§3.2 fact 6; §32 guarantee 10 seeds
a realistic distribution "for the outcome model"). Scored: cases without a
chargesheet (the open cases whose outcome is being predicted). Output is the
full class-probability dict over A/B/C.

Features (inline at T1 — the §12 store is T2): report delay hours, charge
count, gravity ordinal. All non-P9, declared for the guard.
Outputs surface as Insights (§8) — no dedicated §3.6 table for this model.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.contracts.insight import Factor
from lumen.contracts.prediction import PredictionContract
from lumen.db.models import canonical as m
from lumen.intelligence.guards import assert_no_denied_columns

MODEL_NAME = "case_outcome"
MODEL_VERSION = "v1"
CLASSES = ("A", "B", "C")

FEATURE_COLUMNS: list[tuple[str, str]] = [
    ("CaseMaster", "InfoReceivedPSDate"),
    ("CaseMaster", "IncidentFromDate"),
    ("CaseMaster", "GravityOffenceID"),
    ("ActSectionAssociation", "CaseMasterID"),
    ("ChargesheetDetails", "cstype"),
]
FEATURE_NAMES = ["report_delay_hours", "charge_count", "gravity_ordinal"]


def _features(case: m.CaseMaster, charges: dict[int, int]) -> list[float]:
    delay = 0.0
    if case.InfoReceivedPSDate is not None and case.IncidentFromDate is not None:
        delay = (case.InfoReceivedPSDate - case.IncidentFromDate).total_seconds() / 3600.0
    return [delay, float(charges.get(case.CaseMasterID, 0)),
            float(case.GravityOffenceID or 0)]


def score_case_outcome(session: Session, *, now: datetime | None = None
                       ) -> list[PredictionContract]:
    """Train on chargesheeted cases (cstype label), predict P(A/B/C) for
    cases without a chargesheet."""
    for table, column in FEATURE_COLUMNS:
        assert_no_denied_columns(table, [column])
    now = now or datetime.now(timezone.utc)

    charges: dict[int, int] = {}
    for a in session.query(m.ActSectionAssociation).all():
        charges[a.CaseMasterID] = charges.get(a.CaseMasterID, 0) + 1
    labels: dict[int, str] = {}
    cs_dates = []
    for cs in session.query(m.ChargesheetDetails).all():
        if cs.cstype in CLASSES and cs.CaseMasterID is not None:
            labels[cs.CaseMasterID] = cs.cstype
            if cs.csdate is not None:
                cs_dates.append(cs.csdate)
    cases = {c.CaseMasterID: c for c in session.query(m.CaseMaster).all()}

    train = [(cid, lab) for cid, lab in sorted(labels.items()) if cid in cases]
    if len(train) < 2 or len({lab for _, lab in train}) < 2:
        return []          # degenerate label set — nothing trainable (disclosed)

    from sklearn.ensemble import RandomForestClassifier
    X = [_features(cases[cid], charges) for cid, _ in train]
    y = [lab for _, lab in train]
    clf = RandomForestClassifier(n_estimators=100, random_state=settings.SEED_RANDOM)
    clf.fit(X, y)
    factors = [Factor(label=n, weight=round(float(w), 4), detail=None)
               for n, w in zip(FEATURE_NAMES, clf.feature_importances_)]

    window = (min(cs_dates).date().isoformat(), max(cs_dates).date().isoformat()) \
        if cs_dates else ("n/a", "n/a")
    limitations = [
        f"Trained on {len(train)} chargesheeted cases in window {window[0]} to {window[1]}.",
        "Probabilities reflect historical charging patterns, not the merits "
        "of any individual case.",
    ]

    contracts: list[PredictionContract] = []
    open_cases = sorted(cid for cid in cases if cid not in labels)
    for cid in open_cases:
        proba = clf.predict_proba([_features(cases[cid], charges)])[0]
        by_class = {cls: 0.0 for cls in CLASSES}
        for cls, p in zip(clf.classes_, proba):
            by_class[str(cls)] = round(float(p), 4)
        contracts.append(PredictionContract(
            model=MODEL_NAME, kind="Classification",
            subject_type="case", subject_id=str(cid),
            output={"probabilities": by_class},
            factors=factors, limitations=limitations,
            model_version=MODEL_VERSION, computed_at=now,
        ))
    return contracts
