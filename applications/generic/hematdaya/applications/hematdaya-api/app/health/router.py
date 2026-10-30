"""Liveness and readiness endpoints."""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, str]:
    """Report that the process is serving.

    Returns:
        dict[str, str]: The status.
    """
    return {"status": "ok"}


@router.get("/ready", summary="Readiness check")
async def ready(session: SessionDep) -> dict[str, str]:
    """Report that dependencies are reachable.

    Args:
        session (SessionDep): Database session.

    Returns:
        dict[str, str]: The status.
    """
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
