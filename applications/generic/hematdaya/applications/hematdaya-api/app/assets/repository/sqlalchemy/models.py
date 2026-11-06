"""Asset ORM records."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AssetRecord(Base):
    """Row in ``assets``."""

    __tablename__ = "assets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    scope_kind: Mapped[str] = mapped_column(Text)
    parent_asset_id: Mapped[UUID | None]
    expected_use: Mapped[str] = mapped_column(Text, default="unknown")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceRecord(Base):
    """Row in ``sources``."""

    __tablename__ = "sources"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(Text)
    measurement_kind: Mapped[str] = mapped_column(Text)
    cadence_seconds: Mapped[int | None] = mapped_column(Integer)
    resolution_mwh: Mapped[int | None] = mapped_column(BigInteger)
    transport_status: Mapped[str] = mapped_column(Text, default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BindingRecord(Base):
    """Row in ``bindings``."""

    __tablename__ = "bindings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    site_id: Mapped[UUID]
    source_id: Mapped[UUID]
    asset_id: Mapped[UUID]
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    authoritative: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssetRelationRecord(Base):
    """Row in ``asset_relations``."""

    __tablename__ = "asset_relations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    site_id: Mapped[UUID]
    from_asset_id: Mapped[UUID]
    to_asset_id: Mapped[UUID]
    kind: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
