import pytest
from app.services.repositories.module_service import ModuleService
from app.db.session import SessionLocal

def test_module_service_returns_expected_shapes(setup_test_db):
    from tests.conftest import TestingSession
    db = TestingSession()
    try:
        from app.db.models import OperatorORM
        op = OperatorORM(id="mock-op", role="command")
        service = ModuleService(db=db, operator=op)
        assert service.get_dashboard_summary()
        assert service.get_analytics_statistics()
        assert service.get_geospatial_hotspots()
        assert service.get_investigation_cases()
        assert service.get_investigation_fir_intelligence()
        assert service.get_intelligence_workbench()
        assert service.get_operations_tactical_overview()
        assert service.get_administration_security_posture()
    finally:
        db.close()
