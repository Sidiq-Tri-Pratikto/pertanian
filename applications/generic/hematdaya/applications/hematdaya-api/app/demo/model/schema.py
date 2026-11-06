"""Demo request and response schemas."""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints


class ScenarioResponse(BaseModel):
    """A scenario clients can start."""

    id: str
    segment: str
    name: str
    description: str


class InitialPeriodResponse(BaseModel):
    """The period a scenario opens on."""

    preset: str
    start_date: date
    end_date: date


class CreateDemoSessionRequest(BaseModel):
    """The scenario to seed."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: Annotated[str, StringConstraints(min_length=1, max_length=40)]


class DemoWorkspaceResponse(BaseModel):
    """The demo workspace behind the current session."""

    site_id: UUID
    scenario_id: str
    expires_at: datetime
    initial_period: InitialPeriodResponse


class DemoSessionResponse(DemoWorkspaceResponse):
    """A new session, or the same session recovered by a valid replay. Keep the token secret."""

    token: str
