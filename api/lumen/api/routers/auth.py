"""
Auth router — maps to frontend authService.js:
  POST /api/auth/login   -> loginRequest
  POST /api/auth/logout  -> logoutRequest
  POST /api/auth/refresh -> refreshRequest
  GET  /api/auth/me      -> fetchCurrentOperator

NOTE: The legacy custom-JWT auth implementation (identity/security.py,
hashing.py, auth_service.py, dependencies.py) and its supporting contracts
(contracts/auth.py, contracts/operator.py) have been deleted. Catalyst
Authentication will be rebuilt properly in a future session
(LUMEN_MASTER_SPEC_V3 Session 3). Until then every endpoint here returns
501 rather than pretending to authenticate anyone.
"""
from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter(prefix="/auth", tags=["Authentication"])

_NOT_IMPLEMENTED = "Not yet implemented — pending Session 3 (Catalyst Authentication) of LUMEN_MASTER_SPEC_V3.md"


@router.post("/login")
def login(body: dict, response: Response):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/logout")
def logout(response: Response):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.post("/refresh")
def refresh(request: Request, response: Response):
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)


@router.get("/me")
def me():
    raise HTTPException(status_code=501, detail=_NOT_IMPLEMENTED)
