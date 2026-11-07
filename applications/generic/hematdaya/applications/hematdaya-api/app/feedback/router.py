"""Feedback endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header

from app.feedback.dependencies import FeedbackServiceDep
from app.feedback.model.schema import FeedbackRequest, FeedbackResponse
from app.identity.dependencies import PrincipalDep

router = APIRouter(tags=["feedback"])


@router.post("/insights/{insight_id}/feedback", summary="Give feedback on an evidence revision")
async def give_feedback(
    insight_id: UUID,
    request: FeedbackRequest,
    principal: PrincipalDep,
    service: FeedbackServiceDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", pattern=r"^[A-Za-z0-9_-]{22,128}$")],
) -> FeedbackResponse:
    """Mark useful or not relevant, snooze until the next local midnight, hide or restore one revision.

    Feedback changes no measurement, asset, source or device. Retry an unknown outcome with the same key; a new
    action needs a new key.

    Args:
        insight_id (UUID): The insight.
        request (FeedbackRequest): Action and revision.
        principal (PrincipalModel): The acting principal.
        service (FeedbackService): Feedback rules.
        idempotency_key (str): At least 128 random bits, base64url.

    Returns:
        FeedbackResponse: The confirmed state of that revision.
    """
    return await service.apply(insight_id, principal, request.revision, request.action, idempotency_key)
