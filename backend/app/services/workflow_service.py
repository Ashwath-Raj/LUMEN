from sqlalchemy.orm import Session

class WorkflowService:
    def __init__(self, db: Session):
        self._db = db

    def compute_investigation_workflow(self, case_id: str) -> list:
        # Schema does not natively track BNSS procedural workflows yet.
        return []
