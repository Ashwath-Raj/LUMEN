"""
LUMEN Crime Intelligence Platform — FastAPI application entry-point.

NOTE: The legacy prototype's DB models, JWT auth, and Gemini AI integration
have been deliberately removed ahead of LUMEN_MASTER_SPEC_V3's canonical
rebuild of these subsystems under lumen/{db,identity,ai}/ (Sessions 2, 3,
and 14 respectively). The app boots with NO external dependencies: no DB
connection attempt, no AI provider, no Neo4j driver. Endpoints that relied
on the deleted subsystems return HTTP 501 until their session lands.

Startup sequence:
  1. Register middleware, exception handlers, and all routers.
  2. That's it — no DB table creation, no seeding, no graph driver.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lumen.api.routers.administration import router as administration_router
from lumen.api.routers.audit import router as audit_router
from lumen.api.routers.ai import router as ai_router
from lumen.api.routers.analytics import router as analytics_router
from lumen.api.routers.auth import router as auth_router
from lumen.api.routers.dashboard import router as dashboard_router
from lumen.api.routers.geospatial import router as geospatial_router
from lumen.api.routers.health import router as health_router
from lumen.api.routers.intelligence import router as intelligence_router
from lumen.api.routers.investigation import router as investigation_router
from lumen.api.routers.operations import router as operations_router
from lumen.api.routers.persons import router as persons_router
from lumen.api.routers.quality import router as quality_router
from lumen.api.routers.system import router as system_router
from lumen.config import settings
from lumen.api.exception_handlers import register_exception_handlers
from lumen.observability.logging import logger
from lumen.observability.middleware import LoggingMiddleware


@asynccontextmanager
async def lifespan(application: FastAPI):
    """No-op startup/shutdown — the app requires no external services to boot.

    DB schema creation/seeding and the Neo4j driver are deferred to later
    LUMEN_MASTER_SPEC_V3 sessions (Session 2 for the canonical DB schema).
    """
    logger.info("LUMEN backend ready (legacy DB/auth/AI subsystems removed; endpoints stubbed pending later sessions).")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)
app.include_router(geospatial_router, prefix=settings.API_PREFIX)
app.include_router(investigation_router, prefix=settings.API_PREFIX)
app.include_router(intelligence_router, prefix=settings.API_PREFIX)
app.include_router(operations_router, prefix=settings.API_PREFIX)
app.include_router(administration_router, prefix=settings.API_PREFIX)
app.include_router(quality_router, prefix=settings.API_PREFIX)
app.include_router(persons_router, prefix=settings.API_PREFIX)
app.include_router(ai_router, prefix=settings.API_PREFIX)
app.include_router(system_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
