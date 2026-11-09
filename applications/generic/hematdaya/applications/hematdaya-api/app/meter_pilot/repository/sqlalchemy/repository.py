"""Postgres persistence for the meter pilot."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.meter_pilot.model.models import Enrollment, MeterAssignment
from app.meter_pilot.repository.sqlalchemy.models import EnrollmentRecord, MeterAssignmentRecord, StartRequestRecord


class SqlAlchemyPilotRepository:
    """Read and write lab state in the caller's transaction."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def assigned_to_site(self, site_id: UUID) -> MeterAssignment | None:
        record = await self.session.scalar(
            select(MeterAssignmentRecord).where(MeterAssignmentRecord.site_id == site_id)
        )
        return MeterAssignment.model_validate(record) if record else None

    async def assigned_meter(self, meter_id: UUID) -> MeterAssignment | None:
        record = await self.session.get(MeterAssignmentRecord, meter_id, populate_existing=True)
        return MeterAssignment.model_validate(record) if record else None

    async def authenticate(self, digest: str, now: datetime) -> MeterAssignment | None:
        record = await self.session.scalar(
            select(MeterAssignmentRecord).where(
                MeterAssignmentRecord.access_digest == digest, MeterAssignmentRecord.access_expires_at > now
            )
        )
        return MeterAssignment.model_validate(record) if record else None

    async def enrollment(self, enrollment_id: UUID) -> Enrollment | None:
        record = await self.session.get(EnrollmentRecord, enrollment_id, populate_existing=True)
        return Enrollment.model_validate(record) if record else None

    async def for_start_key(self, site_id: UUID, key: str) -> Enrollment | None:
        record = await self.session.get(StartRequestRecord, (site_id, key))
        return await self.enrollment(record.enrollment_id) if record else None

    async def latest(self, site_id: UUID) -> Enrollment | None:
        record = await self.session.scalar(
            select(EnrollmentRecord)
            .where(EnrollmentRecord.site_id == site_id)
            .order_by(EnrollmentRecord.started_at.desc(), EnrollmentRecord.id.desc())
            .limit(1)
        )
        return Enrollment.model_validate(record) if record else None

    async def add_enrollment(self, site_id: UUID, now: datetime, expires_at: datetime) -> Enrollment:
        record = EnrollmentRecord(site_id=site_id, started_at=now, expires_at=expires_at)
        self.session.add(record)
        await self.session.flush()
        return Enrollment.model_validate(record)

    async def remember_start(self, site_id: UUID, key: str, enrollment_id: UUID) -> None:
        self.session.add(StartRequestRecord(site_id=site_id, key=key, enrollment_id=enrollment_id))
        await self.session.flush()

    async def update_enrollment(self, enrollment_id: UUID, **values: object) -> Enrollment:
        result = await self.session.scalars(
            update(EnrollmentRecord)
            .where(EnrollmentRecord.id == enrollment_id)
            .values(**values)
            .returning(EnrollmentRecord)
        )
        return Enrollment.model_validate(result.one())

    async def update_assignment(self, meter_id: UUID, **values: object) -> None:
        await self.session.execute(
            update(MeterAssignmentRecord).where(MeterAssignmentRecord.meter_id == meter_id).values(**values)
        )
