"""
Detection models — LUMEN_MASTER_SPEC_V3 §13 rows 3 and 6.

    | Volume anomaly | Detection | spike + baseline + σ |
    | Path: IsolationForest AND z-score, both reported |

    | Reporting-delay outlier | Detection | units with anomalous delay |
    | Path: Local |

Volume anomaly works on district-week case counts — the granularity §32
guarantee 6 fixes ("A district-week ≥3σ above baseline"). Both detectors are
reported per §13: the z-score against the district's own baseline AND the
IsolationForest decision on the same series.

The reporting-delay outlier lives in this module because §28's intelligence/
file list has no dedicated module for it (engine/risk/hotspots/anomaly/
linkage/outcome only) — both are §13 Detection rows; placement disclosed.

DISCLOSED (cannot be determined from the specification — exposed as
configuration): the spike threshold (default σ=3.0, anchored on §32 g6's
"≥3σ"), and the delay-outlier threshold (default z≥3.0 mirroring it). Delay
is `InfoReceivedPSDate − IncidentFromDate` (§12's `report_delay_hours`
definition).

P9: dates, station, and district inputs only — declared for the guard.
Outputs surface as Insights (§8) — no dedicated §3.6 table exists for these
two models.
"""
from __future__ import annotations

import statistics
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.contracts.insight import Factor
from lumen.contracts.prediction import PredictionContract
from lumen.db.models import canonical as m
from lumen.intelligence.guards import assert_no_denied_columns

VOLUME_MODEL = "volume_anomaly"
DELAY_MODEL = "reporting_delay"
MODEL_VERSION = "v1"

FEATURE_COLUMNS: list[tuple[str, str]] = [
    ("CaseMaster", "CrimeRegisteredDate"),
    ("CaseMaster", "PoliceStationID"),
    ("CaseMaster", "InfoReceivedPSDate"),
    ("CaseMaster", "IncidentFromDate"),
]


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def score_volume_anomaly(session: Session, *, sigma: float = 3.0,
                         now: datetime | None = None) -> list[PredictionContract]:
    """District-weeks whose count is ≥ sigma above the district's own
    baseline; IsolationForest is run on the same series and both results are
    reported (§13)."""
    for table, column in FEATURE_COLUMNS:
        assert_no_denied_columns(table, [column])
    now = now or datetime.now(timezone.utc)

    units = {u.UnitID: u.DistrictID for u in session.query(m.Unit).all()}
    weekly: dict[int, dict[date, int]] = {}
    for c in session.query(m.CaseMaster).all():
        district = units.get(c.PoliceStationID)
        if district is None or c.CrimeRegisteredDate is None:
            continue
        wk = _week_start(c.CrimeRegisteredDate)
        weekly.setdefault(district, {})[wk] = weekly.get(district, {}).get(wk, 0) + 1
    if not weekly:
        return []

    # IsolationForest over every district-week count (both detectors reported)
    from sklearn.ensemble import IsolationForest
    all_rows = [(d, wk, n) for d, series in sorted(weekly.items())
                for wk, n in sorted(series.items())]
    iso = IsolationForest(random_state=settings.SEED_RANDOM)
    iso_flags = iso.fit_predict([[n] for _, _, n in all_rows])
    iso_scores = iso.score_samples([[n] for _, _, n in all_rows])
    iso_by_key = {(d, wk): (int(flag), float(score))
                  for (d, wk, _), flag, score in zip(all_rows, iso_flags, iso_scores)}

    window_start = min(wk for _, wk, _ in all_rows)
    window_end = max(wk for _, wk, _ in all_rows) + timedelta(days=6)
    limitations = [
        f"Baseline window {window_start.isoformat()} to {window_end.isoformat()}.",
        "Weekly counts reflect registration dates, not incident dates.",
    ]

    contracts: list[PredictionContract] = []
    for district, series in sorted(weekly.items()):
        for wk, count in sorted(series.items()):
            baseline = [n for w, n in series.items() if w != wk]
            if len(baseline) < 2:
                continue
            mean = statistics.mean(baseline)
            stdev = statistics.pstdev(baseline)
            z = (count - mean) / stdev if stdev > 0 else 0.0
            if z < sigma:
                continue
            flag, score = iso_by_key[(district, wk)]
            contracts.append(PredictionContract(
                model=VOLUME_MODEL, kind="Detection",
                subject_type="district", subject_id=str(district),
                output={"spike_week": wk.isoformat(), "count": count,
                        "baseline_mean": round(mean, 3), "sigma": round(z, 3),
                        "zscore_flag": True,
                        "isolation_forest_flag": flag == -1,
                        "isolation_forest_score": round(score, 4)},
                factors=[Factor(label="weekly case volume", weight=round(z, 3),
                                detail=f"{count} vs baseline {mean:.1f}")],
                limitations=limitations, model_version=MODEL_VERSION, computed_at=now,
            ))
    return contracts


def score_reporting_delay(session: Session, *, sigma: float = 3.0,
                          now: datetime | None = None) -> list[PredictionContract]:
    """Units whose mean report delay (info received − incident, hours) is an
    outlier (z ≥ sigma) against all units."""
    for table, column in FEATURE_COLUMNS:
        assert_no_denied_columns(table, [column])
    now = now or datetime.now(timezone.utc)

    delays: dict[int, list[float]] = {}
    for c in session.query(m.CaseMaster).all():
        if (c.PoliceStationID is None or c.InfoReceivedPSDate is None
                or c.IncidentFromDate is None):
            continue
        hours = (c.InfoReceivedPSDate - c.IncidentFromDate).total_seconds() / 3600.0
        delays.setdefault(c.PoliceStationID, []).append(hours)
    means = {u: statistics.mean(v) for u, v in delays.items()}
    if len(means) < 3:
        return []
    overall = statistics.mean(means.values())
    spread = statistics.pstdev(means.values())
    if spread == 0:
        return []

    window = sorted(means)
    limitations = [
        f"Computed over the full recorded window across {len(means)} units.",
        "Delay is measured from IncidentFromDate to InfoReceivedPSDate; "
        "cases missing either timestamp are excluded.",
    ]
    contracts: list[PredictionContract] = []
    for unit_id in window:
        z = (means[unit_id] - overall) / spread
        if z < sigma:
            continue
        contracts.append(PredictionContract(
            model=DELAY_MODEL, kind="Detection",
            subject_type="unit", subject_id=str(unit_id),
            output={"mean_delay_hours": round(means[unit_id], 2),
                    "overall_mean_hours": round(overall, 2), "zscore": round(z, 3),
                    "cases_measured": len(delays[unit_id])},
            factors=[Factor(label="mean report delay hours",
                            weight=round(z, 3), detail=None)],
            limitations=limitations, model_version=MODEL_VERSION, computed_at=now,
        ))
    return contracts
