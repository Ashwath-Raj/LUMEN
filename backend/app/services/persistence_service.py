from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import (
    AlertORM,
    AuditLogORM,
    CaseORM,
    EvidenceORM,
    FIRORM,
    IntelligenceReportORM,
    InvestigationORM,
    OfficerORM,
    OperationORM,
    OperatorORM,
    RoleORM,
    SuspectORM,
    VictimORM,
)
from app.repositories.sqlalchemy_repository import SQLAlchemyRepository


class PersistenceService:
    def __init__(self, session: Session):
        self.session = session
        self.operators = SQLAlchemyRepository(session, OperatorORM)
        self.roles = SQLAlchemyRepository(session, RoleORM)
        self.cases = SQLAlchemyRepository(session, CaseORM)
        self.firs = SQLAlchemyRepository(session, FIRORM)
        self.suspects = SQLAlchemyRepository(session, SuspectORM)
        self.victims = SQLAlchemyRepository(session, VictimORM)
        self.evidence = SQLAlchemyRepository(session, EvidenceORM)
        self.investigations = SQLAlchemyRepository(session, InvestigationORM)
        self.intelligence_reports = SQLAlchemyRepository(session, IntelligenceReportORM)
        self.officers = SQLAlchemyRepository(session, OfficerORM)
        self.operations = SQLAlchemyRepository(session, OperationORM)
        self.alerts = SQLAlchemyRepository(session, AlertORM)
        self.audit_logs = SQLAlchemyRepository(session, AuditLogORM)
