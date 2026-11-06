"""Demo requests and responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class DemoAccount(BaseModel):
    """One account in the demo picker."""

    key: str
    name: str
    persona: Literal["inovator", "mitra"]
    fixture: str
    label: str


class DemoSignInRequest(BaseModel):
    """Sign in as one demo account."""

    model_config = ConfigDict(extra="forbid")

    key: str


class DemoResetRequest(BaseModel):
    """Recreate the demo, optionally in a fixture state such as F01-GAP."""

    model_config = ConfigDict(extra="forbid")

    gap: bool = False
    scan: bool = False
    proposed_entity: bool = False


class DemoResetResponse(BaseModel):
    """What the reset recreated."""

    accounts: int
    inventions: int
