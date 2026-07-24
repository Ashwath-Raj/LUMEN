"""
District risk band — LUMEN_MASTER_SPEC_V3 §13 row 1.

    | District risk band | Classification | band + score + factor weights |
    | Path: Zia AutoML, scikit-learn fallback |

T1 implements the scikit-learn fallback §13 names (Zia AutoML is Catalyst
adoption, Session 23). A tree ensemble is used per §13's own rationale:
"Every model reports feature importances — that is where `factors` comes
from, and why tree ensembles beat deep learning here."

DISCLOSED (cannot be determined from the specification):
  * No ground-truth risk label exists anywhere in the spec or the canonical
    schema. The T1 stand-in trains against per-window case-volume tertiles
    (Low/Moderate/High) — the label definition is a stand-in pending the Zia
    AutoML path, not a spec value.
  * Band names High/Moderate/Low are not specified (mirrors §9's band names).
  * Features are computed inline from canonical columns because the §12
    feature store is T2 and not yet built ("models read features" cannot hold
    before the store exists).

P9: feature columns are declared in FEATURE_COLUMNS and pass through the §4.3
rule-6 guard on every run — no model consumes a P9 attribute (§13, enforced,
tested).

Batch-scores into `lumen_district_risk` (§3.6); the API reads (§13).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.contracts.insight import Factor
from lumen.contracts.prediction import PredictionContract
from lumen.db.models import canonical as m
from lumen.db.models.prediction import LumenDistrictRisk
from lumen.intelligence.guards import assert_no_denied_columns

MODEL_NAME = "district_risk"
MODEL_VERSION = "v1"
BANDS = ("Low", "Moderate", "High")          # names not spec-fixed; §9-style

# Every input column, declared for the P9 guard (§13: "No model consumes a
# P9 attribute (enforced, tested)").
FEATURE_COLUMNS: list[tuple[str, str]] = [
    ("CaseMaster", "CrimeRegisteredDate"),
    ("CaseMaster", "PoliceStationID"),
    ("CaseMaster", "GravityOffenceID"),
    ("ActSectionAssociation", "CaseMasterID"),
]
FEATURE_NAMES = ["case_count", "gravity_mean", "charge_count"]


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def score_district_risk(session: Session, *, now: datetime | None = None
                        ) -> list[PredictionContract]:
    """Train on all district-weeks, band each district's latest week.
    Persists lumen_district_risk (clear-first, idempotent)."""
    for table, column in FEATURE_COLUMNS:
        assert_no_denied_columns(table, [column])
    now = now or datetime.now(timezone.utc)

    units = {u.UnitID: u.DistrictID for u in session.query(m.Unit).all()}
    charges: dict[int, int] = {}
    for a in session.query(m.ActSectionAssociation).all():
        charges[a.CaseMasterID] = charges.get(a.CaseMasterID, 0) + 1

    # district-week feature rows
    rows: dict[tuple[int, date], dict] = {}
    for c in session.query(m.CaseMaster).all():
        district = units.get(c.PoliceStationID)
        if district is None or c.CrimeRegisteredDate is None:
            continue
        key = (district, _week_start(c.CrimeRegisteredDate))
        r = rows.setdefault(key, {"case_count": 0, "gravity_sum": 0, "charge_count": 0})
        r["case_count"] += 1
        r["gravity_sum"] += c.GravityOffenceID or 0
        r["charge_count"] += charges.get(c.CaseMasterID, 0)
    if not rows:
        return []

    keys = sorted(rows)
    X = [[rows[k]["case_count"],
          rows[k]["gravity_sum"] / rows[k]["case_count"],
          rows[k]["charge_count"]] for k in keys]

    # tertile band labels over case volume (disclosed stand-in target)
    counts = sorted(r["case_count"] for r in rows.values())
    lo = counts[len(counts) // 3]
    hi = counts[(2 * len(counts)) // 3]

    def band_of(count: int) -> str:
        if count > hi:
            return "High"
        if count > lo:
            return "Moderate"
        return "Low"

    y = [band_of(rows[k]["case_count"]) for k in keys]

    factors: list[Factor]
    if len(set(y)) >= 2:
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators=100, random_state=settings.SEED_RANDOM)
        clf.fit(X, y)
        factors = [Factor(label=n, weight=round(float(w), 4), detail=None)
                   for n, w in zip(FEATURE_NAMES, clf.feature_importances_)]

        def predict(x):
            return clf.predict([x])[0], float(max(clf.predict_proba([x])[0]))
    else:   # degenerate single-class data — band directly, no trained factors
        factors = [Factor(label="case_count", weight=1.0,
                          detail="degenerate: single band in window")]

        def predict(x):
            return band_of(int(x[0])), 1.0

    window_start = min(k[1] for k in keys)
    window_end = max(k[1] for k in keys) + timedelta(days=6)
    limitations = [
        f"Trained on window {window_start.isoformat()} to {window_end.isoformat()}.",
        "Not valid for districts with fewer than 50 records.",   # §11 forecast statement
    ]

    session.query(LumenDistrictRisk).delete()
    session.flush()

    contracts: list[PredictionContract] = []
    latest: dict[int, date] = {}
    for district, week in keys:
        latest[district] = max(latest.get(district, week), week)
    for district in sorted(latest):
        week = latest[district]
        r = rows[(district, week)]
        x = [r["case_count"], r["gravity_sum"] / r["case_count"], r["charge_count"]]
        band, score = predict(x)
        session.add(LumenDistrictRisk(
            district_id=district, window_start=week, band=band, score=score,
            factors=[f.model_dump() for f in factors], model_version=MODEL_VERSION,
        ))
        contracts.append(PredictionContract(
            model=MODEL_NAME, kind="Classification",
            subject_type="district", subject_id=str(district),
            output={"band": band, "score": score,
                    "factor_weights": {f.label: f.weight for f in factors}},
            factors=factors, limitations=limitations,
            model_version=MODEL_VERSION, computed_at=now,
        ))
    session.flush()
    return contracts
