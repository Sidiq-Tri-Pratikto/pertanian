"""Demo requests and responses."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class DemoAccount(BaseModel):
    """One account in the demo picker."""

    key: str
    name: str
    persona: Literal["inovator", "mitra"]
    fixture: str
    summary: str
    label: str


class DemoSignInRequest(BaseModel):
    """Sign in as one demo account."""

    model_config = ConfigDict(extra="forbid")

    key: str


class DemoResetResponse(BaseModel):
    """What the reset recreated: the scenario's starting point."""

    accounts: int
    inventions: int
