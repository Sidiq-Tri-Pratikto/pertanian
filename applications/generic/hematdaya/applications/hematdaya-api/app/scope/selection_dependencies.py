"""Wire confirmed membership without loading the scope proposal evaluator."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.scope.repository.sqlalchemy.repository import SqlAlchemyAggregationSelectionRepository
from app.scope.service.selection import SelectionService


def build_selection_service(session: AsyncSession) -> SelectionService:
    """Bind membership operations to an existing transaction."""
    return SelectionService(SqlAlchemyAggregationSelectionRepository(session))


def get_selection_service(session: SessionDep) -> SelectionService:
    """Share one membership service across request dependencies."""
    return build_selection_service(session)


SelectionServiceDep = Annotated[SelectionService, Depends(get_selection_service)]
