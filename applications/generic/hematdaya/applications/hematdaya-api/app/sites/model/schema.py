"""Site request and response schemas."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.core.types import Timezone
from app.sites.model.models import SiteContext, SiteKind

SiteName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class UpdateSiteRequest(BaseModel):
    """Fields an owner may change. Stored UTC instants keep their values when the timezone changes."""

    model_config = ConfigDict(extra="forbid")

    name: SiteName | None = None
    context: SiteContext | None = None
    timezone: Timezone | None = None


class SiteResponse(BaseModel):
    """A site as clients see it, with the product time it runs on."""

    id: UUID
    name: str
    kind: SiteKind
    context: SiteContext
    timezone: str
    currency: str
    now: datetime
