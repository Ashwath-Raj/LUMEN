"""
LUMEN Crime Intelligence Platform — FastAPI application entry-point.

Startup sequence:
  1. Create all DB tables (idempotent — won't drop existing data).
  2. Seed the database with development data (idempotent).
  3. Register middleware, exception handlers, and all routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.administration import router as administration_router
from app.api.routers.analytics import router as analytics_router
from app.api.routers.auth import router as auth_router
from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.geospatial import router as geospatial_router
from app.api.routers.health import router as health_router
from app.api.routers.intelligence import router as intelligence_router
from app.api.routers.investigation import router as investigation_router
from app.api.routers.operations import router as operations_router
from app.core.config import settings
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging import logger
from app.core.middleware import LoggingMiddleware
from app.db.session import SessionLocal, engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Run DB setup on startup; nothing special on shutdown."""
    # Import models so Base.metadata knows about all tables
    import app.db.models  # noqa: F401
    from app.db.session import Base
    from app.db.seed import seed_database

    from app.services.graph_service import init_neo4j_driver, close_neo4j_driver
    logger.info("Initializing Neo4j Graph Driver…")
    init_neo4j_driver()

    if not settings.TESTING:
        logger.info("Creating database tables (if not exists)…")
        Base.metadata.create_all(bind=engine)

        logger.info("Seeding database…")
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()
    else:
        logger.info("Skipping real DB init (TESTING=True).")

    logger.info("LUMEN backend ready.")
    yield
    
    logger.info("Closing Neo4j Graph Driver…")
    close_neo4j_driver()


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
    allow_origins=settings.CORS_ORIGINS,
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
