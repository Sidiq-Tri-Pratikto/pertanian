"""Application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.access.router import router as access_router
from app.capabilities.router import router as capabilities_router
from app.capabilities.service.configuration import validate_configuration
from app.capabilities.service.service import SOURCE_RELEASE
from app.core.database import get_engine
from app.core.errors.database import handle_database_error
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.core.logging import setup_logging
from app.core.openapi import install_error_schema
from app.core.security import OriginCheckMiddleware
from app.core.settings import get_settings
from app.dev.router import router as dev_router
from app.health.router import router as health_router
from app.identity.router import auth_router, me_router
from app.platform.router import router as platform_router
from app.platform.service.idempotency import IdempotentReplay, replay_response

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
    validate_configuration(settings)  # Unsafe or unsupported configuration must never serve traffic.
    app = FastAPI(title="temuriset-api", version=SOURCE_RELEASE, lifespan=lifespan)
    app.add_middleware(OriginCheckMiddleware)
    app.add_middleware(ErrorBoundaryMiddleware)
    if settings.cors_allowed_origins:
        # Added after the boundary so it wraps it: failure responses keep their CORS headers.
        app.add_middleware(
            CORSMiddleware, allow_origins=settings.cors_allowed_origins, allow_methods=["*"], allow_headers=["*"]
        )
    register_exception_handlers(app)
    app.add_exception_handler(SQLAlchemyError, handle_database_error)
    app.add_exception_handler(IdempotentReplay, replay_response)
    app.include_router(health_router)
    app.include_router(capabilities_router, prefix=API_PREFIX)
    app.include_router(platform_router, prefix=API_PREFIX)
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(me_router, prefix=API_PREFIX)
    app.include_router(access_router, prefix=API_PREFIX)
    if settings.environment == "development":
        app.include_router(dev_router, prefix=API_PREFIX)
    install_error_schema(app)
    return app


app = create_app()
