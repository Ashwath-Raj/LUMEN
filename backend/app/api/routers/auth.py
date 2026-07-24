"""
Auth router — maps to frontend authService.js:
  POST /api/auth/login   -> loginRequest
  POST /api/auth/logout  -> logoutRequest
  GET  /api/auth/me      -> fetchCurrentOperator
"""
from fastapi import APIRouter, Depends, Response, Request, status, HTTPException
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_operator, get_raw_token
from app.models.operator import Operator
from app.db.session import get_db
from app.db.models import TokenBlacklistORM, OperatorORM
from app.schemas.auth import LoginRequest
from app.services.auth_service import authenticate_operator, operator_to_public_dict
from app.core.exceptions.http import LumenHTTPException
from app.core.security import verify_refresh_token, create_access_token, verify_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        operator, access_token, refresh_token = authenticate_operator(db, body.clearance_id, body.passphrase)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60, # 7 days
        )
        return {
            "token": access_token,
            "token_type": "bearer",
            "operator": operator_to_public_dict(operator),
        }
    except LumenHTTPException as exc:
        raise exc


@router.post("/logout")
def logout(
    response: Response,
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db)
):
    # Add the current access token to the blacklist
    payload = verify_access_token(token)
    if payload and payload.get("jti"):
        blacklist_entry = TokenBlacklistORM(jti=payload.get("jti"))
        db.add(blacklist_entry)
        db.commit()

    response.delete_cookie("refresh_token")
    return {"detail": "Logged out."}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing.")

    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    jti = payload.get("jti")
    if jti and db.query(TokenBlacklistORM).filter(TokenBlacklistORM.jti == jti).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked.")

    operator_id = payload.get("sub")
    operator_orm = db.query(OperatorORM).filter(OperatorORM.id == operator_id).first()
    if not operator_orm or operator_orm.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operator inactive or not found.")

    access_token = create_access_token(subject=operator_orm.id, role=operator_orm.role)
    operator = Operator.model_validate(operator_orm, from_attributes=True)
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "operator": operator_to_public_dict(operator),
    }


@router.get("/me")
def me(operator: Operator = Depends(get_current_operator)):
    return operator_to_public_dict(operator)
