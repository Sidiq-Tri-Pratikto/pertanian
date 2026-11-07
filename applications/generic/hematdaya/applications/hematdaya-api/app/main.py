"""Application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.assets.router import router as assets_router
from app.baseline.router import router as baseline_router
from app.capabilities.router import router as capabilities_router
from app.capabilities.service.service import SOURCE_RELEASE, build_manifest
from app.core.database import get_engine
from app.core.errors.database import handle_database_error
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.core.logging import setup_logging
from app.core.openapi import install_error_schema
from app.core.settings import get_settings
from app.demo.dependencies import resolve_demo_principal
from app.demo.router import router as demo_router
from app.energy.router import router as energy_router
from app.feedback.router import router as feedback_router
from app.health.router import router as health_router
from app.identity.dependencies import register_principal_resolver
from app.imports.router import router as imports_router
from app.insights.router import router as insights_router
from app.sites.router import router as sites_router

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Release shared resources on shutdown."""
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    """Build the application.

    Returns:
        FastAPI: The configured application.
    """
    settings = get_settings()
    setup_logging(settings.log_level)
    build_manifest(settings.composition)  # An unsupported composition must stop startup.
    app = FastAPI(title="hematdaya-api", version=SOURCE_RELEASE, lifespan=lifespan)
    app.add_middleware(ErrorBoundaryMiddleware)
    if settings.cors_allowed_origins:
        # Added after the boundary so it wraps it: failure responses keep their CORS headers.
        app.add_middleware(
            CORSMiddleware, allow_origins=settings.cors_allowed_origins, allow_methods=["*"], allow_headers=["*"]
        )
    register_exception_handlers(app)
    app.add_exception_handler(SQLAlchemyError, handle_database_error)
    app.include_router(health_router)
    app.include_router(capabilities_router, prefix=API_PREFIX)
    app.include_router(sites_router, prefix=API_PREFIX)
    app.include_router(assets_router, prefix=API_PREFIX)
    app.include_router(demo_router, prefix=API_PREFIX)
    app.include_router(energy_router, prefix=API_PREFIX)
    app.include_router(baseline_router, prefix=API_PREFIX)
    app.include_router(insights_router, prefix=API_PREFIX)
    app.include_router(imports_router, prefix=API_PREFIX)
    app.include_router(feedback_router, prefix=API_PREFIX)
    register_principal_resolver(resolve_demo_principal)
    install_error_schema(app)
    return app


app = create_app()
