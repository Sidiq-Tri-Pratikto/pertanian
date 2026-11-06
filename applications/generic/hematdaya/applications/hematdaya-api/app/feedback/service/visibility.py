"""Feedback as the insights module reads it."""

from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.feedback.repository.base_repository import FeedbackRepository
from app.feedback.repository.sqlalchemy.repository import SqlAlchemyFeedbackRepository
from app.insights.service.visibility import FeedbackView


class FeedbackVisibility:
    """Implements the insights ``VisibilityReader`` port."""

    def __init__(self, repository: FeedbackRepository) -> None:
        """Bind to feedback storage.

        Args:
            repository (FeedbackRepository): Feedback storage.
        """
        self.repository = repository

    @classmethod
    def on(cls, session: AsyncSession) -> Self:
        """Build on a request session.

        Args:
            session (AsyncSession): The request's session.

        Returns:
            FeedbackVisibility: The reader.
        """
        return cls(SqlAlchemyFeedbackRepository(session))

    async def feedback(self, principal_id: UUID, insight_ids: list[UUID]) -> dict[UUID, list[FeedbackView]]:
        """Return the owner's feedback on every revision of these insights.

        Args:
            principal_id (UUID): The owner.
            insight_ids (list[UUID]): The insights.

        Returns:
            dict[UUID, list[FeedbackView]]: Feedback by insight.
        """
        views: dict[UUID, list[FeedbackView]] = {}
        for state in await self.repository.states(principal_id, insight_ids):
            views.setdefault(state.insight_id, []).append(
                FeedbackView(
                    revision=state.revision, rating=state.rating, visibility=state.visibility.value, until=state.until
                )
            )
        return views
