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


class TeaserPhoto(BaseModel):
    """The published photo, served without metadata from ``url``, with its size to reserve the space."""

    url: str
    alt: str
    width: int
    height: int
    orientation: int = 1


class TeaserUpdate(BaseModel):
    """A published public update (052)."""

    id: UUID
    title: str
    body: str
    content_locale: Literal["id", "en"]
    published_at: datetime


class TeaserResponse(BaseModel):
    """What anyone may see of an invention whose managing party published its page or included it in alerts."""

    id: UUID
    title: str
    summary: str
    sector: str
    stage: Stage | None
    tkt_level: int | None = None
    keywords: list[str]
    inventor_name: str
    published_at: datetime | None
    follow_enabled: bool = Field(
        default=False, description="Whether the public page is on (051); following arrives in 053."
    )
    field_test_summary: str | None = None
    photo: TeaserPhoto | None = None
    content_locale: Literal["id", "en"] = "id"
    latest_updates: list[TeaserUpdate] = Field(
        default_factory=list, description="Up to three published updates, newest first; only with the public page."
    )


class FollowRequest(BaseModel):
    """Follow one invention's public updates with only an email (053)."""

    model_config = ConfigDict(extra="forbid")

    invention_id: UUID
    email: Email
    locale: Literal["id", "en"] = "id"


class FollowLanguageRequest(TokenRequest):
    """The language of future update emails, through a manage link."""

    locale: Literal["id", "en"]


class FollowResponse(BaseModel):
    """What a follow link shows. The email is partly masked."""

    invention_id: UUID
    invention_title: str
    email: str
    status: Literal["PENDING", "ACTIVE", "UNSUBSCRIBED"]
    locale: Literal["id", "en"]
    confirmed_at: datetime | None
    manage_token: str | None = Field(
        default=None, description="A fresh manage link token, returned once after confirmation."
    )
