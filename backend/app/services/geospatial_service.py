from sqlalchemy.orm import Session
from app.db.models import HotspotORM

class GeospatialIntelligenceService:
    def __init__(self, db: Session):
        self._db = db

    def compute_hotspot_analytics(self) -> list:
        # ⚠️ TEMPORARY RBAC EXCEPTION (PHASE 10B.10.5.3) ⚠️
        # Hotspots currently have no deterministic jurisdictional ownership.
        # `x` and `y` are UI visualization coordinates (CSS percentages) and MUST NOT be interpreted as geographic coordinates.
        # Hotspots are intentionally excluded from jurisdictional RLS and remain globally visible to authorized roles.
        # This is an explicitly approved RBAC exception. Future jurisdictional RLS requires an authoritative ownership model.
        # DO NOT introduce ad-hoc district filtering or coordinate-based jurisdiction inference.
        hotspots = self._db.query(HotspotORM).all()
        results = []
        for i, h in enumerate(hotspots):
            results.append({
                "id": h.id,
                "label": h.label,
                "x": h.x,  # Note: These are static SVG coordinates per API contract
                "y": h.y,
                "intensity": h.intensity,
                "probability": h.probability,
                "incidents": h.incidents,
                "windowHours": h.window_hours,
                # Derived/Honest metrics
                "crimeGrowth": "N/A", 
                "nightCrimePercentage": "N/A",
                "weekendCrimePercentage": "N/A",
                "patrolRecommendation": "Monitor Area",
                "suggestedDeploymentZones": ["Primary Sector"]
            })
        return results
