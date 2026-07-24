from pydantic import BaseModel
from typing import Optional


class Operator(BaseModel):
    """Domain model for an authenticated operator (analogous to the DB row)."""
    id: str
    name: str
    role: str              # 'command' | 'analyst' | 'field'
    clearance: str         # 'TS/SCI' | 'SECRET' | 'CONFIDENTIAL'
    unit: str
    rank: str
    date_of_entry: str
    biometric_hash: str
    avatar_url: Optional[str] = None
    status: str = "ACTIVE"
    operator_id: Optional[str] = None
    assigned_unit: Optional[str] = None
    preferences: dict = {}


class OperatorPublic(BaseModel):
    """Safe subset returned to the frontend — no passwords or internal fields."""
    id: str
    name: str
    role: str
    clearance: str
    unit: str
    rank: str
    dateOfEntry: str
    biometricHash: str
    avatarUrl: Optional[str] = None
    operatorId: Optional[str] = None
    assignedUnit: Optional[str] = None
    status: str
    preferences: dict
