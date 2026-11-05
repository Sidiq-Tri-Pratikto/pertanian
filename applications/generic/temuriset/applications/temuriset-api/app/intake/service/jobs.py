"""Worker jobs: persist an opportunity's expiry. Registered on import by the worker."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.intake.service.service import EXPIRE_JOB, IntakeService
from app.worker.registry import registry


@registry.job(EXPIRE_JOB)
async def expire_opportunity(session: AsyncSession, job_input: dict[str, Any]) -> dict[str, Any]:
    """Expire an opportunity whose closing time has come. A job for a time that later moved does nothing.

    Args:
        session (AsyncSession): The worker's session.
        job_input (dict[str, Any]): ``opportunity_id``.

    Returns:
        dict[str, Any]: The opportunity.
    """
    await IntakeService(session).expire(UUID(job_input["opportunity_id"]))
    return {"type": "opportunity", "id": job_input["opportunity_id"]}
