"""Feedback repository over SQLAlchemy."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.feedback.model.models import FeedbackAction, FeedbackOperationModel, FeedbackStateModel
from app.feedback.repository.base_repository import FeedbackRepository
from app.feedback.repository.sqlalchemy.models import FeedbackOperationRecord, InsightFeedbackRecord


class SqlAlchemyFeedbackRepository(FeedbackRepository):
    """Feedback in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def claim(
        self, principal_id: UUID, key: str, insight_id: UUID, revision: int, action: FeedbackAction
    ) -> bool:
        """Reserve a key. A concurrent claim of the same key waits for this transaction, then sees it.

        Args:
            principal_id (UUID): The owner.
            key (str): The client's ``Idempotency-Key``.
            insight_id (UUID): The insight.
            revision (int): The revision.
            action (FeedbackAction): The action.

        Returns:
            bool: True when this request owns the key.
        """
        claimed = await self.session.scalar(
            insert(FeedbackOperationRecord)
            .values(principal_id=principal_id, key=key, insight_id=insight_id, revision=revision, action=action.value)
            .on_conflict_do_nothing(index_elements=["principal_id", "key"])
            .returning(FeedbackOperationRecord.key)
        )
        return claimed is not None

    async def operation(self, principal_id: UUID, key: str) -> FeedbackOperationModel:
        """Return a claimed operation.

        Args:
            principal_id (UUID): The owner.
            key (str): The key.

        Returns:
            FeedbackOperationModel: The operation.
        """
        record = await self.session.get(FeedbackOperationRecord, (principal_id, key), populate_existing=True)
        assert record is not None  # Only called after a claim lost to a committed one.
        return FeedbackOperationModel.model_validate(record, from_attributes=True)

    async def complete(self, principal_id: UUID, key: str, response: dict[str, Any]) -> None:
        """Store the outcome in the same transaction as the effect.

        Args:
            principal_id (UUID): The owner.
            key (str): The key.
            response (dict[str, Any]): The JSON response.
        """
        await self.session.execute(
            update(FeedbackOperationRecord)
            .where(FeedbackOperationRecord.principal_id == principal_id, FeedbackOperationRecord.key == key)
            .values(response=response)
        )

    async def states(self, principal_id: UUID, insight_ids: list[UUID]) -> list[FeedbackStateModel]:
        """Return the owner's feedback on every revision of these insights.

        Args:
            principal_id (UUID): The owner.
            insight_ids (list[UUID]): The insights.

        Returns:
            list[FeedbackStateModel]: One row per revision with feedback.
        """
        if not insight_ids:
            return []
        records = await self.session.scalars(
            select(InsightFeedbackRecord)
            .where(
                InsightFeedbackRecord.principal_id == principal_id, InsightFeedbackRecord.insight_id.in_(insight_ids)
            )
            .execution_options(populate_existing=True)
        )
        return [FeedbackStateModel.model_validate(record, from_attributes=True) for record in records]

    async def save(self, principal_id: UUID, state: FeedbackStateModel) -> None:
        """Insert or replace the owner's feedback on one revision.

        Args:
            principal_id (UUID): The owner.
            state (FeedbackStateModel): The new state.
        """
        values = state.model_dump(mode="python") | {"principal_id": principal_id, "visibility": state.visibility.value}
        statement = insert(InsightFeedbackRecord).values(**values)
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=["insight_id", "revision", "principal_id"],
                set_={
                    "rating": statement.excluded.rating,
                    "visibility": statement.excluded.visibility,
                    "until": statement.excluded.until,
                    "updated_at": func.now(),
                },
            )
        )
