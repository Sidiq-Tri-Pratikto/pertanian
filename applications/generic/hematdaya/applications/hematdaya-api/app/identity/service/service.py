"""Principal lifecycle."""

from uuid import UUID

from app.identity.model.models import PrincipalKind, PrincipalModel
from app.identity.repository.base_repository import PrincipalRepository


class PrincipalService:
    """Creates and removes principals for the modules that own their lifecycle."""

    def __init__(self, repository: PrincipalRepository) -> None:
        """Bind to storage.

        Args:
            repository (PrincipalRepository): Principal storage.
        """
        self.repository = repository

    async def create(self, kind: PrincipalKind) -> PrincipalModel:
        """Create a principal.

        Args:
            kind (PrincipalKind): Demo or user.

        Returns:
            PrincipalModel: The new principal.
        """
        return await self.repository.add(kind)

    async def delete(self, principal_ids: list[UUID]) -> None:
        """Delete principals whose sites are already gone.

        Args:
            principal_ids (list[UUID]): Principals to remove.
        """
        await self.repository.delete(principal_ids)
