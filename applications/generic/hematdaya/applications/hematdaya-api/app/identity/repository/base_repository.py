"""Principal storage interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.identity.model.models import PrincipalKind, PrincipalModel


class PrincipalRepository(ABC):
    """Stores principals."""

    @abstractmethod
    async def add(self, kind: PrincipalKind) -> PrincipalModel:
        """Create a principal."""

    @abstractmethod
    async def delete(self, principal_ids: list[UUID]) -> None:
        """Delete principals that own nothing any more."""
