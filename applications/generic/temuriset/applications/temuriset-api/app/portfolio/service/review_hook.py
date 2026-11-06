"""Where organization review (spec 033) plugs into publication. Until then every publication passes."""

from typing import Protocol
from uuid import UUID


class PublicationGate(Protocol):
    """Decides whether a publication takes effect now or waits for review."""

    async def decide(self, *, invention_id: UUID, managing_party_id: UUID, number: int) -> str:
        """Return ``PUBLISHED`` or ``PENDING_REVIEW``.

        Args:
            invention_id (UUID): The invention.
            managing_party_id (UUID): Its managing party.
            number (int): The version being published.
        """
        ...


class PassThroughGate:
    """No review: the publication takes effect at once."""

    async def decide(self, *, invention_id: UUID, managing_party_id: UUID, number: int) -> str:
        """Always publish.

        Args:
            invention_id (UUID): The invention.
            managing_party_id (UUID): Its managing party.
            number (int): The version being published.

        Returns:
            str: ``PUBLISHED``.
        """
        return "PUBLISHED"
