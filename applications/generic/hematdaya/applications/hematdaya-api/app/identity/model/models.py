"""Principal domain model."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class PrincipalKind(StrEnum):
    """Who acts: an anonymous demo session or, from 036, a user."""

    DEMO = "demo"
    USER = "user"


class PrincipalModel(BaseModel):
    """The party that owns sites and makes requests.

    Attributes:
        id (UUID): Stable identifier.
        kind (PrincipalKind): Demo or user.
    """

    id: UUID
    kind: PrincipalKind
