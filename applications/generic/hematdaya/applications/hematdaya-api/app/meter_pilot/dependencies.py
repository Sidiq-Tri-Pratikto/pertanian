"""Pilot service construction and operator-issued owner access."""

import re
from hashlib import sha256
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.assets.dependencies import get_asset_service
from app.core.clock import wall_now
from app.core.database import SessionDep
from app.core.errors.base import NotFoundError, UnauthorizedError
from app.core.settings import get_settings
from app.identity.dependencies import bearer_token
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.measurements.dependencies import build_ingest_service
from app.meter_pilot.model.models import MeterAssignment
from app.meter_pilot.repository.sqlalchemy.repository import SqlAlchemyPilotRepository
from app.meter_pilot.service.service import MeterPilotService
from app.sites.dependencies import get_site_service

ACCESS_PREFIX = "hdpilot_"
_ACCESS = re.compile(r"hdpilot_[A-Za-z0-9_-]{43}")


def require_pilot() -> None:
    """Keep lab operations unavailable unless explicitly enabled."""
    if not get_settings().meter_pilot_enabled:
        raise NotFoundError()


def access_digest(token: str) -> str:
    """Hash a random, high-entropy access code before storing or looking it up."""
    return sha256(token.encode("ascii")).hexdigest()


async def _authenticated_assignment(token: str, session: AsyncSession) -> MeterAssignment:
    if not _ACCESS.fullmatch(token):
        raise UnauthorizedError()
    assignment = await SqlAlchemyPilotRepository(session).authenticate(access_digest(token), wall_now())
    if assignment is None:
        raise UnauthorizedError()
    return assignment


async def resolve_pilot_principal(token: str, session: AsyncSession) -> PrincipalModel | None:
    """Resolve a valid lab code as the standard site's user principal."""
    if not token.startswith(ACCESS_PREFIX) or not get_settings().meter_pilot_enabled:
        return None
    assignment = await _authenticated_assignment(token, session)
    return PrincipalModel(id=assignment.owner_id, kind=PrincipalKind.USER)


async def pilot_session(request: Request, session: SessionDep) -> MeterAssignment:
    """Return the active access grant for this lab code only."""
    require_pilot()
    token = bearer_token(request)
    if token is None:
        raise UnauthorizedError()
    return await _authenticated_assignment(token, session)


def build_pilot_service(session: AsyncSession) -> MeterPilotService:
    """Share the session across enrollment, binding and measurement writes."""
    sites = get_site_service(session)
    return MeterPilotService(
        SqlAlchemyPilotRepository(session), sites, get_asset_service(session, sites), build_ingest_service(session)
    )


def get_pilot_service(session: SessionDep) -> MeterPilotService:
    """Build the owner-scoped enrollment service for a request."""
    return build_pilot_service(session)


PilotServiceDep = Annotated[MeterPilotService, Depends(get_pilot_service)]
PilotSessionDep = Annotated[MeterAssignment, Depends(pilot_session)]
