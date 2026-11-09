"""Postgres mapping for the meter pilot."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MeterAssignmentRecord(Base):
    """A site has one lab meter with independent owner and meter revocation."""

    __tablename__ = "meter_pilot_assignments"

    meter_id: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), unique=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("principals.id", ondelete="CASCADE"))
    access_digest: Mapped[str | None] = mapped_column(String(64), unique=True)
    access_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meter_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_id: Mapped[UUID | None] = mapped_column(ForeignKey("sources.id"))


class EnrollmentRecord(Base):
    """An expiring setup with the staged counter and its confirmation result."""

    __tablename__ = "meter_pilot_enrollments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    site_id: Mapped[UUID] = mapped_column(ForeignKey("meter_pilot_assignments.site_id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column("created_at", DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    first_measured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_energy_wh: Mapped[Decimal | None] = mapped_column(Numeric())
    asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("assets.id"))
    confirm_key: Mapped[str | None] = mapped_column(String(128))
    asset_name: Mapped[str | None] = mapped_column(Text)


class StartRequestRecord(Base):
    """Keep start retries stable when multiple requests refer to the same setup."""

    __tablename__ = "meter_pilot_start_requests"

    site_id: Mapped[UUID] = mapped_column(
        ForeignKey("meter_pilot_assignments.site_id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    enrollment_id: Mapped[UUID] = mapped_column(ForeignKey("meter_pilot_enrollments.id", ondelete="CASCADE"))
