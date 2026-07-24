"""
Auth router — Catalyst Authentication (LUMEN_MASTER_SPEC_V3 §20.2, §26.1 —
"replaces bespoke JWT entirely").

Login itself is NOT an endpoint this app implements: the frontend redirects
the browser directly to Catalyst's hosted login page
(`/__catalyst/auth/login`, configured via `client-package.json`), and
Catalyst's own infrastructure handles credential collection, social
providers, and session-token issuance. Sign-out is likewise a client-side
call to the Catalyst Web SDK (`window.catalyst.auth.signOut(...)`), not an
API call to this backend.

The only piece this backend implements is `GET /me`: verifying the
Catalyst-issued session on an incoming request and returning the current
user's details, via the `zcatalyst-sdk` Python package. Per the SDK's
actual source (`zcatalyst_sdk/_util.py::parse_headers_from_request`),
`zcatalyst_sdk.initialize(req=request)` only requires `request.headers` to
exist and be dict-convertible — this works with FastAPI's `Request` object
directly; no framework-specific adapter is needed.

The legacy custom-JWT implementation (identity/security.py, hashing.py,
auth_service.py, dependencies.py) and its supporting contracts
(contracts/auth.py, contracts/operator.py) were deleted in an earlier
cleanup pass and are not reintroduced here.
"""
import zcatalyst_sdk
from zcatalyst_sdk.exceptions import CatalystError
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/auth", tags=["Authentication"])

_NOT_APPLICABLE = (
    "Handled by Catalyst's hosted login page (/__catalyst/auth/login), not this API. "
    "See LUMEN_MASTER_SPEC_V3 §20.2."
)


@router.post("/login")
def login():
    raise HTTPException(status_code=501, detail=_NOT_APPLICABLE)


@router.post("/logout")
def logout():
    raise HTTPException(status_code=501, detail=_NOT_APPLICABLE)


@router.post("/refresh")
def refresh():
    raise HTTPException(status_code=501, detail=_NOT_APPLICABLE)


@router.get("/me")
def me(request: Request):
    try:
        app = zcatalyst_sdk.initialize(req=request)
        user = app.authentication().get_current_user()
    except CatalystError:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
