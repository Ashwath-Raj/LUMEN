from sqlalchemy.orm import Session

class IntelligenceProfileService:
    def __init__(self, db: Session):
        self._db = db

    def enhance_suspect_profile(self, base_suspect: dict) -> dict:
        # Provide truthful empty state for unavailable intelligence metrics
        base_suspect.update({
            "aliases": [],
            "knownAssociates": [],
            "repeatOffences": 0,
            "linkedFIRs": [],
            "gangMembership": "Unavailable",
            "vehicles": [],
            "phoneNumbers": [],
            "operatingDistricts": [],
            "operatingPoliceStations": [],
            "knownModusOperandi": "Unavailable",
            "riskScore": 0,
            "repeatOffenderProbability": "N/A",
            "investigationHistory": []
        })
        return base_suspect
