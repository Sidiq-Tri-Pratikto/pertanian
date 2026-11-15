"""Worker side of investor subscriptions: direct alerts on publication, and the self-renewing weekly digest."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.subscriptions.service.service import DIGEST_JOB, SubscriptionService, ensure_digest_scheduled
from app.worker.registry import registry

CONSUMER = "subscriptions.alerts"


async def _alert(session: AsyncSession, payload: dict[str, Any]) -> None:
    await SubscriptionService(session).alert(UUID(payload["invention_id"]))


registry.consumer("invention.published", CONSUMER)(_alert)
registry.consumer("invention.digest_enabled", CONSUMER)(_alert)


@registry.job(DIGEST_JOB)
async def weekly_digest(session: AsyncSession, job_input: dict[str, Any]) -> dict[str, Any]:
    """Send this week's digests, then queue next week's (FR-006).

    Args:
        session (AsyncSession): The worker's session.
        job_input (dict[str, Any]): ``at``, the scheduled instant.

    Returns:
        dict[str, Any]: How many digests went out.
    """
    sent = await SubscriptionService(session).digest()
    await ensure_digest_scheduled(session)
    return {"type": "weekly_digest", "id": job_input.get("at", ""), "sent": sent}
