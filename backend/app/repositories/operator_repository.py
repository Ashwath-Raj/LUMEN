from app.data.operators import OPERATORS_DB, CREDENTIALS_DB
from app.models.operator import Operator


class OperatorRepository:
    def get(self, identifier: str) -> Operator | None:
        return OPERATORS_DB.get(identifier)

    def list(self) -> list[Operator]:
        return list(OPERATORS_DB.values())

    def get_credentials(self, clearance_id: str) -> tuple[str, str] | None:
        return CREDENTIALS_DB.get(clearance_id)

    def get_default_credentials(self) -> tuple[str, str] | None:
        return CREDENTIALS_DB.get("__any__")
