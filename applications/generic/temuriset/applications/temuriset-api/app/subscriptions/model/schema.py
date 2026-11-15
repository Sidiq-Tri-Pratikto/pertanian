"""Investor subscription requests and responses."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.identity.model.schema import Email
from app.portfolio.model.schema import Stage

Keyword = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
Sector = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Token = Annotated[str, StringConstraints(min_length=20, max_length=200)]


class Topics(BaseModel):
    """What the investor wants to hear about. At least one group must be filled in."""

    model_config = ConfigDict(extra="forbid")

    sectors: Annotated[list[Sector], Field(max_length=10)] = []
    stages: Annotated[list[Stage], Field(max_length=5)] = []
    keywords: Annotated[list[Keyword], Field(max_length=5)] = []


class SubscribeRequest(BaseModel):
    """A quick subscription: only an email and topics."""

    model_config = ConfigDict(extra="forbid")

    email: Email
    topics: Topics
    locale: Literal["id", "en"] = "id"


class SubscribeResponse(BaseModel):
    """The same answer for every email, so nobody learns whether one is registered."""

    status: Literal["check_email"] = "check_email"


class TokenRequest(BaseModel):
    """A link token from an email."""

    model_config = ConfigDict(extra="forbid")

    token: Token


class UpdateTopicsRequest(TokenRequest):
    """New topics, through a manage link."""

    topics: Topics


class SubscriptionResponse(BaseModel):
    """What a manage link shows. The email is partly masked."""

    email: str
    topics: Topics
    status: Literal["PENDING", "ACTIVE", "UNSUBSCRIBED"]
    confirmed_at: datetime | None
    manage_token: str | None = Field(
        default=None, description="A fresh manage link token, returned once after confirmation."
    )


class TeaserResponse(BaseModel):
    """What anyone may see of an invention its managing party included in investor alerts."""

    id: UUID
    title: str
    summary: str
    sector: str
    stage: Stage | None
    keywords: list[str]
    inventor_name: str
    published_at: datetime | None
