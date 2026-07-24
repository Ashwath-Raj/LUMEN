"""
NOTE: Tests ModuleService (lumen.services.module_service), which is no
longer imported by any router and still depends internally on the
deleted legacy DB models. Expected to fail import/collection until the
canonical DB schema and service layer are rebuilt in a later
LUMEN_MASTER_SPEC_V3 session (Session 2). Left as-is (not deleted, not
patched) per the sanitation-pass scope.
"""
import pytest
from lumen.services.module_service import ModuleService
from lumen.db.session import SessionLocal

def test_module_service_returns_expected_shapes(setup_test_db):
    from tests.conftest import TestingSession
    db = TestingSession()
    try:
        from lumen.db.models.legacy_models import OperatorORM
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
