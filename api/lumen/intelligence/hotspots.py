"""
Hotspot clusters — LUMEN_MASTER_SPEC_V3 §13 row 2.

    | Hotspot clusters | Unsupervised | clusters + weights |
    | Path: DBSCAN (haversine); QuickML pipeline at T2 |

DBSCAN over incident coordinates with the haversine metric — §34's demo line:
"DBSCAN over incident coordinates, not a bounding box." The QuickML pipeline
is T2 (Session 23) and not touched here.

DISCLOSED (cannot be determined from the specification — exposed as
configuration per instruction):
  * `eps_km` and `min_samples` are not specified. Defaults (0.5 km, 5) are
    configuration values documented here, sized so §32 guarantee 1's
    "visually obvious hotspot" (≥10 cases within a few hundred metres) is
    detectable; both are caller-overridable.
  * Cluster `weight` is not defined beyond "clusters + weights" — the case
    count of the cluster is used.
  * The scoring window is not specified; a rolling window (default 90 days,
    §12's `crime_density_km2` precedent) ending at the latest registered
    date is used, caller-overridable.

P9: coordinates and dates only — declared for the guard.

Batch-scores into `lumen_hotspot` (§3.6); the API reads (§13).
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from lumen.config import settings
from lumen.contracts.insight import Factor
from lumen.contracts.prediction import PredictionContract
from lumen.db.models import canonical as m
from lumen.db.models.prediction import LumenHotspot
from lumen.intelligence.guards import assert_no_denied_columns

MODEL_NAME = "hotspots"
MODEL_VERSION = "v1"
EARTH_RADIUS_KM = 6371.0088

FEATURE_COLUMNS: list[tuple[str, str]] = [
    ("CaseMaster", "latitude"),
    ("CaseMaster", "longitude"),
    ("CaseMaster", "CrimeRegisteredDate"),
    ("CaseMaster", "PoliceStationID"),
    ("CaseMaster", "CrimeMajorHeadID"),
]


def _haversine_km(a, b) -> float:
    p1, l1, p2, l2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def score_hotspots(session: Session, *, eps_km: float = 0.5, min_samples: int = 5,
                   window_days: int = 90, now: datetime | None = None
                   ) -> list[PredictionContract]:
    """DBSCAN (haversine) over in-window case coordinates. Persists
    lumen_hotspot (clear-first, idempotent)."""
    for table, column in FEATURE_COLUMNS:
        assert_no_denied_columns(table, [column])
    now = now or datetime.now(timezone.utc)

    import numpy as np
    from sklearn.cluster import DBSCAN

    units = {u.UnitID: u.DistrictID for u in session.query(m.Unit).all()}
    dated = [c for c in session.query(m.CaseMaster).all()
             if c.latitude is not None and c.longitude is not None
             and c.CrimeRegisteredDate is not None]
    session.query(LumenHotspot).delete()
    session.flush()
    if not dated:
        return []

    window_end: date = max(c.CrimeRegisteredDate for c in dated)
    window_start = window_end - timedelta(days=window_days)
    cases = sorted((c for c in dated if c.CrimeRegisteredDate >= window_start),
                   key=lambda c: c.CaseMasterID)
    if not cases:
        return []

    coords = np.radians([[float(c.latitude), float(c.longitude)] for c in cases])
    labels = DBSCAN(eps=eps_km / EARTH_RADIUS_KM, min_samples=min_samples,
                    metric="haversine").fit_predict(coords)

    clusters: dict[int, list] = {}
    for case, label in zip(cases, labels):
        if label >= 0:
            clusters.setdefault(int(label), []).append(case)

    contracts: list[PredictionContract] = []
    limitations = [
        f"Scoring window {window_start.isoformat()} to {window_end.isoformat()}.",
        "Clusters reflect reported incident coordinates; unreported or "
        "ungeocoded incidents are invisible to this model.",
    ]
    # deterministic ids ordered by centroid
    ordered = sorted(clusters.values(),
                     key=lambda cs: (min(float(c.latitude) for c in cs),
                                     min(float(c.longitude) for c in cs)))
    for cluster_id, members in enumerate(ordered, start=1):
        lat = sum(float(c.latitude) for c in members) / len(members)
        lng = sum(float(c.longitude) for c in members) / len(members)
        radius_m = max(_haversine_km((lat, lng), (float(c.latitude), float(c.longitude)))
                       for c in members) * 1000.0
        districts = [units.get(c.PoliceStationID) for c in members]
        district = max(set(d for d in districts if d is not None),
                       key=districts.count, default=None)
        heads = [c.CrimeMajorHeadID for c in members if c.CrimeMajorHeadID is not None]
        head = max(set(heads), key=heads.count, default=None)
        session.add(LumenHotspot(
            cluster_id=cluster_id, centroid_lat=lat, centroid_lng=lng,
            radius_m=radius_m, weight=float(len(members)), district_id=district,
            crime_head_id=head, window_start=window_start, window_end=window_end,
            method="dbscan_haversine",
        ))
        contracts.append(PredictionContract(
            model=MODEL_NAME, kind="Unsupervised",
            subject_type="district", subject_id=str(district),
            output={"cluster_id": cluster_id, "centroid": [lat, lng],
                    "radius_m": round(radius_m, 1), "weight": len(members),
                    "case_ids": [c.CaseMasterID for c in members]},
            factors=[Factor(label="clustered case count", weight=float(len(members)),
                            detail=f"eps={eps_km}km min_samples={min_samples}")],
            limitations=limitations, model_version=MODEL_VERSION, computed_at=now,
        ))
    session.flush()
    return contracts
