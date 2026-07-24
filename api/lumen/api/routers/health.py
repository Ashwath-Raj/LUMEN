from fastapi import APIRouter

from lumen.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
