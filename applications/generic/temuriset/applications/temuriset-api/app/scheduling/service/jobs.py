"""Worker job: persist a proposal's expiry. Registered on import by the worker."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.scheduling.service.service import EXPIRE_JOB, SchedulingService
from app.worker.registry import registry


@registry.job(EXPIRE_JOB)
async def expire_proposal(session: AsyncSession, job_input: dict[str, Any]) -> dict[str, Any]:
    """Expire a proposal whose time came; one accepted or replaced meanwhile is left alone.

    Args:
        session (AsyncSession): The worker's session.
        job_input (dict[str, Any]): ``proposal_id``.

    Returns:
        dict[str, Any]: The proposal.
    """
    await SchedulingService(session).expire(UUID(job_input["proposal_id"]))
    return {"type": "schedule_proposal", "id": job_input["proposal_id"]}
