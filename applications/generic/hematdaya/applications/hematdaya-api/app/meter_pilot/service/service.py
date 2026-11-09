"""Owner-scoped setup and authenticated counter ingestion in one transaction."""

from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from app.assets.model.models import MeasurementKind, ScopeKind, SourceModel, SourceOrigin, TransportStatus
from app.assets.model.schema import CreateAssetRequest, CreateBindingRequest
from app.assets.service.service import AssetService
from app.core.clock import wall_now
from app.core.errors.base import ConflictError, NotFoundError, RequestInvalidError
from app.identity.model.models import PrincipalKind, PrincipalModel
from app.measurements.model.models import ReadingInput
from app.measurements.service.service import IngestService
from app.meter_pilot.model.models import Enrollment, MeterAssignment
from app.meter_pilot.model.schema import CADENCE_SECONDS, METER_MODEL_NAME, EnrollmentResponse
from app.meter_pilot.repository.base_repository import PilotRepository
from app.sites.model.models import SiteKind, SiteModel
from app.sites.service.service import SiteService

ENROLLMENT_TTL = timedelta(minutes=15)


def progress(enrollment: Enrollment, now: datetime) -> EnrollmentResponse:
    """Read the server-side state without treating a staged reading as connected."""
    status: Literal["waiting", "ready", "connected", "expired"]
    if enrollment.asset_id:
        status = "connected"
    elif enrollment.expires_at <= now:
        status = "expired"
    elif enrollment.first_measured_at:
        status = "ready"
    else:
        status = "waiting"
    return EnrollmentResponse(
        id=enrollment.id,
        status=status,
        expires_at=enrollment.expires_at,
        first_measured_at=enrollment.first_measured_at,
        asset_id=enrollment.asset_id,
    )


class MeterPilotService:
    """Serialize enrollment, revocation and ingestion on the site's existing write lock."""

    def __init__(
        self, repository: PilotRepository, sites: SiteService, assets: AssetService, ingest: IngestService
    ) -> None:
        self.repository = repository
        self.sites = sites
        self.assets = assets
        self.ingest = ingest

    async def start(self, site_id: UUID, principal: PrincipalModel, key: str) -> EnrollmentResponse:
        """Start or recover the current setup, retaining the identity of each accepted retry."""
        site = await self.sites.lock_owned(site_id, principal)
        await self._owned_assignment(site.id, principal)
        now = wall_now()
        stored = await self.repository.for_start_key(site.id, key)
        if stored is not None:
            return progress(stored, now)
        latest = await self.repository.latest(site.id)
        if latest is None or progress(latest, now).status == "expired":
            latest = await self.repository.add_enrollment(site.id, now, now + ENROLLMENT_TTL)
        await self.repository.remember_start(site.id, key, latest.id)
        return progress(latest, now)

    async def status(self, enrollment_id: UUID, principal: PrincipalModel) -> EnrollmentResponse:
        """Read progress for a verified owner."""
        enrollment = await self._enrollment(enrollment_id)
        await self.sites.get_owned(enrollment.site_id, principal, for_share=True)
        await self._owned_assignment(enrollment.site_id, principal)
        return progress(await self._enrollment(enrollment_id), wall_now())

    async def confirm(
        self, enrollment_id: UUID, principal: PrincipalModel, key: str, asset_name: str
    ) -> EnrollmentResponse:
        """Create the monitored appliance and ingest its anchor once, atomically."""
        candidate = await self._enrollment(enrollment_id)
        site = await self.sites.lock_owned(candidate.site_id, principal)
        assignment = await self._owned_assignment(site.id, principal)
        enrollment = await self._enrollment(enrollment_id)
        now = wall_now()
        state = progress(enrollment, now)
        if state.status == "connected":
            if enrollment.confirm_key == key and enrollment.asset_name == asset_name:
                return state
            raise ConflictError()
        if state.status != "ready" or assignment.source_id is not None:
            raise ConflictError()
        assert enrollment.first_measured_at is not None
        assert enrollment.first_received_at is not None
        assert enrollment.first_energy_wh is not None
        asset = await self.assets.create_asset(
            site.id, principal, CreateAssetRequest(name=asset_name, scope_kind=ScopeKind.DEVICE)
        )
        source = await self.assets.create_source(
            site,
            label=METER_MODEL_NAME,
            origin=SourceOrigin.LIVE,
            measurement_kind=MeasurementKind.COUNTER,
            cadence_seconds=CADENCE_SECONDS,
            transport_status=TransportStatus.LIVE,
        )
        await self.assets.bind_source(
            asset.id, principal, CreateBindingRequest(source_id=source.id, effective_from=enrollment.first_measured_at)
        )
        await self._ingest(
            site,
            source,
            ReadingInput(value=enrollment.first_energy_wh, unit="Wh", measured_at=enrollment.first_measured_at),
            enrollment.first_received_at,
        )
        await self.repository.update_assignment(assignment.meter_id, source_id=source.id)
        connected = await self.repository.update_enrollment(
            enrollment_id, asset_id=asset.id, confirm_key=key, asset_name=asset_name
        )
        return progress(connected, now)

    async def receive(self, meter_id: UUID, reading: ReadingInput, received_at: datetime) -> None:
        """Stage a reading during setup or ingest it into the confirmed source."""
        assignment = await self.repository.assigned_meter(meter_id)
        if assignment is None:
            raise NotFoundError()
        site = await self.sites.lock(assignment.site_id)
        assignment = await self.repository.assigned_meter(meter_id)
        if assignment is None or assignment.meter_revoked_at or site.kind is not SiteKind.STANDARD:
            raise NotFoundError()
        enrollment = await self.repository.latest(site.id)
        if enrollment is None or reading.measured_at is None:
            return
        if assignment.source_id is not None:
            assert enrollment.first_measured_at is not None
            if reading.measured_at >= enrollment.first_measured_at:
                source = await self.assets.source_for_site(site, assignment.source_id)
                await self._ingest(site, source, reading, received_at)
            return
        now = wall_now()
        if progress(enrollment, now).status != "waiting":
            return
        if not enrollment.started_at <= reading.measured_at <= received_at:
            return
        if received_at - reading.measured_at > timedelta(seconds=2 * CADENCE_SECONDS):
            return
        await self.repository.update_enrollment(
            enrollment.id,
            first_measured_at=reading.measured_at,
            first_received_at=received_at,
            first_energy_wh=reading.value,
        )

    async def _enrollment(self, enrollment_id: UUID) -> Enrollment:
        enrollment = await self.repository.enrollment(enrollment_id)
        if enrollment is None:
            raise NotFoundError()
        return enrollment

    async def _owned_assignment(self, site_id: UUID, principal: PrincipalModel) -> MeterAssignment:
        assignment = await self.repository.assigned_to_site(site_id)
        if (
            principal.kind is not PrincipalKind.USER
            or assignment is None
            or assignment.owner_id != principal.id
            or assignment.meter_revoked_at is not None
        ):
            raise NotFoundError()
        return assignment

    async def _ingest(self, site: SiteModel, source: SourceModel, reading: ReadingInput, received_at: datetime) -> None:
        result = await self.ingest.ingest(site, source, [reading], received_at=received_at)
        if result.rejected:
            raise RequestInvalidError()
