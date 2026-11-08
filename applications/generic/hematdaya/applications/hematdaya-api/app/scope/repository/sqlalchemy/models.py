"""Confirmed selection records."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AggregationSelectionRecord(Base):
    """The optional confirmed selection of one site."""

    __tablename__ = "aggregation_selections"
    __table_args__ = (CheckConstraint("revision > 0", name="aggregation_selections_positive_revision"),)

    site_id: Mapped[UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), primary_key=True)
    revision: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AggregationSelectionAssetRecord(Base):
    """One distinct same-site member of a confirmed selection."""

    __tablename__ = "aggregation_selection_assets"
    __table_args__ = (
        ForeignKeyConstraint(["site_id", "asset_id"], ["assets.site_id", "assets.id"], ondelete="CASCADE"),
        Index("ix_aggregation_selection_assets_asset", "asset_id"),
    )

    site_id: Mapped[UUID] = mapped_column(
        ForeignKey("aggregation_selections.site_id", ondelete="CASCADE"), primary_key=True
    )
    asset_id: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
