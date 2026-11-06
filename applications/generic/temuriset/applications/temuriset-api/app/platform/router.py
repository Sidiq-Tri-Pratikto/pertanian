"""Operation status for clients that never received their response."""

from uuid import UUID

from fastapi import APIRouter

from app.core.database import SessionDep
from app.core.errors.base import NotFoundError
from app.core.security import PrincipalDep
from app.platform.model.schema import OperationResponse, OperationResult, OperationStatus
from app.platform.repository.sqlalchemy.repository import SqlAlchemyPlatformRepository

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/{operation_id}", summary="Report on an operation")
async def get_operation(operation_id: UUID, session: SessionDep, principal: PrincipalDep) -> OperationResponse:
    """Tell the acting party whether its operation committed.

    Args:
        operation_id (UUID): From the response the client may have lost.
        session (SessionDep): Database session.
        principal (PrincipalDep): The account scope for private operations.

    Returns:
        OperationResponse: ``COMMITTED`` with a result reference, ``PENDING``, or ``UNKNOWN`` for an id the service
            has no record of.

    Raises:
        NotFoundError: When the operation belongs to another party.
    """
    record = await SqlAlchemyPlatformRepository(session).find_operation(operation_id)
    if record is None:
        return OperationResponse(operation_id=operation_id, status=OperationStatus.UNKNOWN)
    owner_party_id = (
        principal.personal_party_id if record.operation.startswith("private.") else principal.active_party_id
    )
    if record.actor_party_id != owner_party_id or (
        record.owner_account_id is not None and record.owner_account_id != principal.account_id
    ):
        raise NotFoundError()
    if record.status != "committed":
        return OperationResponse(operation_id=operation_id, status=OperationStatus.PENDING)
    result = OperationResult.model_validate(record.result) if record.result else None
    return OperationResponse(operation_id=operation_id, status=OperationStatus.COMMITTED, result=result)
