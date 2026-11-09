"""Lab device catalog, session and enrollment routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response

from app.core.settings import get_settings
from app.identity.dependencies import PrincipalDep
from app.meter_pilot.dependencies import PilotServiceDep, PilotSessionDep, require_pilot
from app.meter_pilot.model.schema import (
    ConfirmEnrollmentRequest,
    DeviceCatalogResponse,
    DeviceResponse,
    EnrollmentResponse,
    PilotSessionResponse,
    StartEnrollmentRequest,
)

router = APIRouter(tags=["meter pilot"])
gated = APIRouter(dependencies=[Depends(require_pilot)])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", pattern=r"^[A-Za-z0-9_-]{22,128}$")]


@router.get("/device-catalog")
async def device_catalog() -> DeviceCatalogResponse:
    """Describe the candidate model and whether this lab can accept enrollment."""
    return DeviceCatalogResponse(
        devices=[DeviceResponse(status="available" if get_settings().meter_pilot_enabled else "planned")]
    )


@gated.get("/pilot/session")
async def get_pilot_session(assignment: PilotSessionDep, response: Response) -> PilotSessionResponse:
    """Verify an operator-issued access code and return its site and expiry."""
    response.headers["Cache-Control"] = "no-store"
    return PilotSessionResponse(site_id=assignment.site_id, expires_at=assignment.access_expires_at)


@gated.post("/sites/{site_id}/enrollments")
async def start_enrollment(
    site_id: UUID,
    request: StartEnrollmentRequest,
    principal: PrincipalDep,
    service: PilotServiceDep,
    idempotency_key: IdempotencyKey,
) -> EnrollmentResponse:
    """Start or recover the setup for the selected model and owned site."""
    return await service.start(site_id, principal, idempotency_key)


@gated.get("/enrollments/{enrollment_id}")
async def get_enrollment(enrollment_id: UUID, principal: PrincipalDep, service: PilotServiceDep) -> EnrollmentResponse:
    """Read server-side setup progress."""
    return await service.status(enrollment_id, principal)


@gated.post("/enrollments/{enrollment_id}/confirm")
async def confirm_enrollment(
    enrollment_id: UUID,
    request: ConfirmEnrollmentRequest,
    principal: PrincipalDep,
    service: PilotServiceDep,
    idempotency_key: IdempotencyKey,
) -> EnrollmentResponse:
    """Bind a meter with a valid reading to the named appliance."""
    return await service.confirm(enrollment_id, principal, idempotency_key, request.asset_name)


router.include_router(gated)
