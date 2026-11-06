"""Demo session storage interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.demo.model.models import CreateOperationModel, DemoSessionModel


class DemoRepository(ABC):
    """Stores demo sessions and creation operations."""

    @abstractmethod
    async def lock_admission(self) -> None:
        """Take the shared admission lock until the transaction ends, across instances."""

    @abstractmethod
    async def get_operation(self, operation_id: str) -> CreateOperationModel | None:
        """Return a creation operation."""

    @abstractmethod
    async def add_operation(self, operation: CreateOperationModel) -> None:
        """Store a creation operation."""

    @abstractmethod
    async def get_session(self, session_id: UUID) -> DemoSessionModel | None:
        """Return a session by ID."""

    @abstractmethod
    async def session_for_principal(self, principal_id: UUID) -> DemoSessionModel | None:
        """Return the session of a demo principal."""

    @abstractmethod
    async def session_for_token(self, token_hash: bytes) -> DemoSessionModel | None:
        """Return the session whose token digest matches."""

    @abstractmethod
    async def add_session(self, session: DemoSessionModel, token_hash: bytes) -> None:
        """Store a session with its token digest."""

    @abstractmethod
    async def expired_sessions(self, now: datetime) -> list[DemoSessionModel]:
        """Return sessions whose expiry has passed."""

    @abstractmethod
    async def delete_operations_retained_until(self, now: datetime) -> None:
        """Delete operation records past their retention."""

    @abstractmethod
    async def count_active(self, now: datetime) -> int:
        """Count sessions that have not expired."""

    @abstractmethod
    async def count_created_since(self, since: datetime) -> int:
        """Count creation operations admitted since an instant, ended sessions included."""
