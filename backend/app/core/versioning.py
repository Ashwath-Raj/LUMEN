from fastapi import APIRouter


def versioned_router(prefix: str, version: str = "v1") -> APIRouter:
    router = APIRouter(prefix=f"/{version}{prefix}", tags=[version])
    return router
