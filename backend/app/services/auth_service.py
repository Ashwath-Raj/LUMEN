from app.core.hashing import verify_password
from app.core.security import create_access_token, create_refresh_token
from app.db.models import OperatorORM
from app.models.operator import Operator
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def authenticate_operator(db: Session, clearance_id: str, passphrase: str) -> tuple[Operator, str, str]:
    """
    Verify clearance_id + passphrase against the database.
    Returns (operator, access_token, refresh_token) or raises 401.
    """
    from sqlalchemy import or_
    operator_orm = db.query(OperatorORM).filter(
        or_(OperatorORM.operator_id == clearance_id, OperatorORM.id == clearance_id)
    ).first()
    if not operator_orm or operator_orm.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not verify_password(passphrase, operator_orm.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    access_token = create_access_token(subject=operator_orm.id, role=operator_orm.role)
    refresh_token = create_refresh_token(subject=operator_orm.id, role=operator_orm.role)

    operator = Operator.model_validate(operator_orm, from_attributes=True)
    return operator, access_token, refresh_token


def operator_to_public_dict(op: Operator) -> dict:
    """Map the Operator domain model to the shape the frontend expects."""
    return {
        "id": op.id,
        "name": op.name,
        "role": op.role,
        "clearance": op.clearance,
        "unit": op.unit,
        "rank": op.rank,
        "dateOfEntry": op.date_of_entry,
        "biometricHash": op.biometric_hash,
        "avatarUrl": op.avatar_url,
        "operatorId": op.operator_id,
        "assignedUnit": op.assigned_unit,
        "status": op.status,
        "preferences": op.preferences,
    }
