"""Sign-in and account requests and responses."""

from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AfterValidator, BaseModel, Field, StringConstraints


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _iana_zone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("unknown time zone") from error
    return value


Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    AfterValidator(_normalize_email),
]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Locale = Literal["id", "en"]
TimeZone = Annotated[str, StringConstraints(max_length=64), AfterValidator(_iana_zone)]
Persona = Literal["inovator", "mitra"]


class CodeRequest(BaseModel):
    """Ask for a sign-in code. Sign-up also carries the profile, applied only when the code is verified."""

    email: Email
    purpose: Literal["sign_up", "sign_in"]
    display_name: DisplayName | None = None
    locale: Locale = "id"
    time_zone: TimeZone = "Asia/Jakarta"
    persona: Persona = "inovator"


class CodeSentResponse(BaseModel):
    """Always the same answer, so it never reveals whether an account exists."""

    sent: Literal[True] = True


class VerifyRequest(BaseModel):
    """Prove control of the email."""

    email: Email
    code: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]


class AccountResponse(BaseModel):
    """The signed-in account. A verified email proves control of the address, nothing more."""

    id: UUID
    display_name: str
    email: str
    email_verified: bool
    locale: str
    time_zone: str
    persona: str
    kind: str
    version: int


class MembershipResponse(BaseModel):
    """One organization the account belongs to, and what it may do there."""

    organization_id: UUID
    party_id: UUID
    name: str
    capabilities: list[str]


class MeResponse(BaseModel):
    """Who is signed in and as whom they act."""

    account: AccountResponse
    personal_party_id: UUID
    active_party_id: UUID
    capabilities: list[str] = Field(default_factory=list)
    organizations: list[MembershipResponse] = Field(default_factory=list)


class UpdateMeRequest(BaseModel):
    """Change account preferences."""

    display_name: DisplayName | None = None
    locale: Locale | None = None
    time_zone: TimeZone | None = None
    persona: Persona | None = None
    expected_version: int


class MailboxMessageResponse(BaseModel):
    """One development mailbox message."""

    to_email: str
    subject: str
    body: str
