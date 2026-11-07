"""Feedback service wiring for routers."""

from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.feedback.repository.sqlalchemy.repository import SqlAlchemyFeedbackRepository
from app.feedback.service.service import FeedbackService
from app.insights.dependencies import InsightServiceDep


def get_feedback_service(session: SessionDep, insights: InsightServiceDep) -> FeedbackService:
    """Build the feedback service on the request session.

    Args:
        session (AsyncSession): The request's session.
        insights (InsightService): Ownership and revision membership.

    Returns:
        FeedbackService: The service.
    """
    return FeedbackService(SqlAlchemyFeedbackRepository(session), insights=insights)


FeedbackServiceDep = Annotated[FeedbackService, Depends(get_feedback_service)]
