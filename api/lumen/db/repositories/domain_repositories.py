"""
Domain-specific repositories for all LUMEN entities.

Each class wraps SQLAlchemyRepository[T] and adds domain-specific
query methods. This keeps routers and services free of ORM details.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from lumen.db.models.legacy_models import (
    AlertORM,
    AuditLogORM,
    CaseORM,
    CoordinationLogORM,
    DeviceForensicsORM,
    EvidenceORM,
    FieldReportORM,
    FIRORM,
    HotspotORM,
    IncidentORM,
    IntelligenceLeadORM,
    IntelligenceReportORM,
    InvestigationReportORM,
    InterviewORM,
    OfficerORM,
    OperatorORM,
    PersonnelORM,
    PersonnelRosterORM,
    SignalInterceptORM,
    DepartmentORM,
    SpecializedUnitORM,
    SuspectORM,
    WatchlistEntryORM,
    StateORM,
    PoliceRangeORM,
    CommissionerateORM,
    DistrictORM,
    UnitORM,
)
from lumen.db.repositories.sqlalchemy_repository import SQLAlchemyRepository


# ── Operator ──────────────────────────────────────────────────────────────────

class OperatorDBRepository(SQLAlchemyRepository[OperatorORM]):
    def __init__(self, session: Session):
        super().__init__(session, OperatorORM)

    def get_by_clearance_id(self, clearance_id: str) -> OperatorORM | None:
        return self.first_by(operator_id=clearance_id)

    def update_preferences(self, operator_id: str, prefs: dict) -> OperatorORM | None:
        op = self.get(operator_id)
        if op:
            op.preferences = prefs
            self.commit()
        return op


# ── Cases ─────────────────────────────────────────────────────────────────────

class CaseRepository(SQLAlchemyRepository[CaseORM]):
    def __init__(self, session: Session):
        super().__init__(session, CaseORM)

    def list_active(self) -> list[CaseORM]:
        return self.filter_by(status="ACTIVE")

    def list_closed(self) -> list[CaseORM]:
        return self.filter_by(status="CLOSED")

    def list_all_summary(self) -> list[dict]:
        """Returns the lightweight list shape the frontend expects."""
        rows = self.list()
        return [
            {
                "id": r.id,
                "label": r.label,
                "status": r.status,
                "updatedAt": r.updated_at,
                "evidenceCount": r.evidence_count,
            }
            for r in rows
        ]


class InvestigationReportRepository(SQLAlchemyRepository[InvestigationReportORM]):
    def __init__(self, session: Session):
        super().__init__(session, InvestigationReportORM)

    def get_by_case(self, case_id: str) -> list[InvestigationReportORM]:
        return self.filter_by(case_id=case_id)


# ── FIRs ──────────────────────────────────────────────────────────────────────

class FIRRepository(SQLAlchemyRepository[FIRORM]):
    def __init__(self, session: Session):
        super().__init__(session, FIRORM)

    def get_by_number(self, fir_number: str) -> FIRORM | None:
        return self.first_by(fir_number=fir_number)


# ── Suspects & Watchlist ──────────────────────────────────────────────────────

class SuspectRepository(SQLAlchemyRepository[SuspectORM]):
    def __init__(self, session: Session):
        super().__init__(session, SuspectORM)

    def get_by_linked_case(self, case_label: str) -> list[SuspectORM]:
        return self.filter_by(linked_case=case_label)


class WatchlistRepository(SQLAlchemyRepository[WatchlistEntryORM]):
    def __init__(self, session: Session):
        super().__init__(session, WatchlistEntryORM)


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceRepository(SQLAlchemyRepository[EvidenceORM]):
    def __init__(self, session: Session):
        super().__init__(session, EvidenceORM)

    def get_by_case(self, case_id: str) -> list[EvidenceORM]:
        return self.filter_by(case_id=case_id)

    def get_by_item_id(self, item_id: str) -> EvidenceORM | None:
        return self.first_by(item_id=item_id)


# ── Interviews & Forensics ────────────────────────────────────────────────────

class InterviewRepository(SQLAlchemyRepository[InterviewORM]):
    def __init__(self, session: Session):
        super().__init__(session, InterviewORM)


class DeviceForensicsRepository(SQLAlchemyRepository[DeviceForensicsORM]):
    def __init__(self, session: Session):
        super().__init__(session, DeviceForensicsORM)


# ── Field Reports ─────────────────────────────────────────────────────────────

class FieldReportRepository(SQLAlchemyRepository[FieldReportORM]):
    def __init__(self, session: Session):
        super().__init__(session, FieldReportORM)

    def get_by_case(self, case_id: str) -> list[FieldReportORM]:
        return self.filter_by(case_id=case_id)


# ── Signal Intercepts ─────────────────────────────────────────────────────────

class SignalRepository(SQLAlchemyRepository[SignalInterceptORM]):
    def __init__(self, session: Session):
        super().__init__(session, SignalInterceptORM)


# ── Hotspots ──────────────────────────────────────────────────────────────────

class HotspotRepository(SQLAlchemyRepository[HotspotORM]):
    def __init__(self, session: Session):
        super().__init__(session, HotspotORM)

    # ⚠️ TEMPORARY RBAC EXCEPTION (PHASE 10B.10.5.3) ⚠️
    # Hotspots currently have no deterministic jurisdictional ownership.
    # `x` and `y` are UI visualization coordinates (CSS percentages) and MUST NOT be interpreted as geographic coordinates.
    # Hotspots are intentionally excluded from jurisdictional RLS and remain globally visible to authorized roles.
    # This is an explicitly approved RBAC exception. Future jurisdictional RLS requires an authoritative ownership model.
    # DO NOT introduce ad-hoc district filtering or coordinate-based jurisdiction inference.

    def get_crime_hotspots(self) -> list[HotspotORM]:
        return self.filter_by(hotspot_type="crime")

    def get_theatre_hotspots(self) -> list[HotspotORM]:
        return self.filter_by(hotspot_type="theatre")


# ── Intelligence ──────────────────────────────────────────────────────────────

class IntelligenceLeadRepository(SQLAlchemyRepository[IntelligenceLeadORM]):
    def __init__(self, session: Session):
        super().__init__(session, IntelligenceLeadORM)


class IntelligenceReportRepository(SQLAlchemyRepository[IntelligenceReportORM]):
    def __init__(self, session: Session):
        super().__init__(session, IntelligenceReportORM)


# ── Incidents & Operations ────────────────────────────────────────────────────

class IncidentRepository(SQLAlchemyRepository[IncidentORM]):
    def __init__(self, session: Session):
        super().__init__(session, IncidentORM)

    def list_ordered(self) -> list[IncidentORM]:
        """Returns incidents ordered CRITICAL > HIGH > ROUTINE."""
        priority_order = {"CRITICAL": 0, "HIGH": 1, "ROUTINE": 2}
        rows = self.list()
        return sorted(rows, key=lambda r: priority_order.get(r.priority, 99))


class CoordinationLogRepository(SQLAlchemyRepository[CoordinationLogORM]):
    def __init__(self, session: Session):
        super().__init__(session, CoordinationLogORM)


# ── Officers & Personnel ──────────────────────────────────────────────────────

class OfficerRepository(SQLAlchemyRepository[OfficerORM]):
    def __init__(self, session: Session):
        super().__init__(session, OfficerORM)


class PersonnelRepository(SQLAlchemyRepository[PersonnelORM]):
    def __init__(self, session: Session):
        super().__init__(session, PersonnelORM)


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertRepository(SQLAlchemyRepository[AlertORM]):
    def __init__(self, session: Session):
        super().__init__(session, AlertORM)

    def get_recent(self, limit: int = 10) -> list[AlertORM]:
        return (
            self.session.query(AlertORM)
            .order_by(AlertORM.created_at.desc())
            .limit(limit)
            .all()
        )


# ── Audit Log ─────────────────────────────────────────────────────────────────

class AuditLogRepository(SQLAlchemyRepository[AuditLogORM]):
    def __init__(self, session: Session):
        super().__init__(session, AuditLogORM)

    def get_recent(self, limit: int = 20) -> list[AuditLogORM]:
        return (
            self.session.query(AuditLogORM)
            .order_by(AuditLogORM.created_at.desc())
            .limit(limit)
            .all()
        )


# ── Personnel Roster (Administration) ────────────────────────────────────────

class PersonnelRosterRepository(SQLAlchemyRepository[PersonnelRosterORM]):
    def __init__(self, session: Session):
        super().__init__(session, PersonnelRosterORM)


# ── Specialized Command (Phase 11) ──────────────────────────────────────────

class DepartmentRepository(SQLAlchemyRepository[DepartmentORM]):
    def __init__(self, session: Session):
        super().__init__(session, DepartmentORM)


class SpecializedUnitRepository(SQLAlchemyRepository[SpecializedUnitORM]):
    def __init__(self, session: Session):
        super().__init__(session, SpecializedUnitORM)


# ── Territorial Command (Phase 12) ─────────────────────────────────────────

class StateRepository(SQLAlchemyRepository[StateORM]):
    def __init__(self, session: Session):
        super().__init__(session, StateORM)

class PoliceRangeRepository(SQLAlchemyRepository[PoliceRangeORM]):
    def __init__(self, session: Session):
        super().__init__(session, PoliceRangeORM)

class CommissionerateRepository(SQLAlchemyRepository[CommissionerateORM]):
    def __init__(self, session: Session):
        super().__init__(session, CommissionerateORM)

class DistrictRepository(SQLAlchemyRepository[DistrictORM]):
    def __init__(self, session: Session):
        super().__init__(session, DistrictORM)

class UnitRepository(SQLAlchemyRepository[UnitORM]):
    def __init__(self, session: Session):
        super().__init__(session, UnitORM)
