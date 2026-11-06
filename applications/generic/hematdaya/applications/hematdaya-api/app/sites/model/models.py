"""Site domain model."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SiteKind(StrEnum):
    """Demo sites run on a virtual clock; standard sites on the wall clock."""

    DEMO = "demo"
    STANDARD = "standard"


class SiteContext(StrEnum):
    """Neutral by default. Context changes examples only, never calculations."""

    HOUSEHOLD = "household"
    BUSINESS = "business"
    INDUSTRY = "industry"
    UNSPECIFIED = "unspecified"


class SiteModel(BaseModel):
    """A monitored location. A site is a domain location, never a tenant.

    Attributes:
        id (UUID): Stable identifier.
        owner_principal_id (UUID): The owner.
        kind (SiteKind): Demo or standard.
        name (str): Display name.
        context (SiteContext): Usage context.
        timezone (str): IANA timezone used for every local period.
        currency (str): ISO currency code.
        virtual_now (datetime | None): The demo clock; None for standard sites.
    """

    id: UUID
    owner_principal_id: UUID
    kind: SiteKind
    name: str
    context: SiteContext
    timezone: str
    currency: str
    virtual_now: datetime | None
