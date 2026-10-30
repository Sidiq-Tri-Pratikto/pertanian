"""Application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_engine
from app.core.errors.database import handle_database_error
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers
from app.core.logging import setup_logging
from app.core.openapi import install_error_schema
from app.core.settings import get_settings
from app.health.router import router as health_router


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
    app = FastAPI(title="hematdaya-api", lifespan=lifespan)
    app.add_middleware(ErrorBoundaryMiddleware)
    if settings.cors_allowed_origins:
        # Added after the boundary so it wraps it: failure responses keep their CORS headers.
        app.add_middleware(
            CORSMiddleware, allow_origins=settings.cors_allowed_origins, allow_methods=["*"], allow_headers=["*"]
        )
    register_exception_handlers(app)
    app.add_exception_handler(SQLAlchemyError, handle_database_error)
    app.include_router(health_router)
    install_error_schema(app)
    return app


app = create_app()
