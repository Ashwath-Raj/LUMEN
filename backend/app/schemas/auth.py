"""
Schemas (Pydantic request/response models) for the auth domain.
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    clearance_id: str
    passphrase: str


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    operator: dict
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
