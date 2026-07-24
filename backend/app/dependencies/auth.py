from app.core.security import verify_access_token
from app.models.operator import Operator
from app.db.models import OperatorORM, TokenBlacklistORM
from app.db.session import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

bearer_scheme = HTTPBearer(auto_error=False)


def get_raw_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Extract raw token string."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def get_current_operator(
    token: str = Depends(get_raw_token),
    db: Session = Depends(get_db),
) -> Operator:
    """
    Extract and validate the Bearer JWT from the Authorization header.
    Returns the matching Operator or raises 401.
    """
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_access_token(token)
    if not payload:
        raise exc

    jti = payload.get("jti")
    if jti and db.query(TokenBlacklistORM).filter(TokenBlacklistORM.jti == jti).first():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    operator_id = payload.get("sub")
    operator_orm = db.query(OperatorORM).filter(OperatorORM.id == operator_id).first()
    if not operator_orm or operator_orm.status != "ACTIVE":
        raise exc

    return Operator.model_validate(operator_orm, from_attributes=True)


def require_role(*allowed_roles: str):
    """Dependency factory that restricts access to specific operator roles."""

    def _check(operator: Operator = Depends(get_current_operator)) -> Operator:
        if operator.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient clearance for this resource.",
            )
        return operator

    return _check
