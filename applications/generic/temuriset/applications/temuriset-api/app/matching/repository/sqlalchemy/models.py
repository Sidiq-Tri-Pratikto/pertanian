"""Match runs and their results, kept so any run can be reproduced from its inputs and versions."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, Row


class MatchRunRecord(Row, Base):
    """One evaluation of a source version against the active targets at that moment."""

    __tablename__ = "match_runs"

    actor_party_id: Mapped[UUID] = mapped_column(ForeignKey("parties.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(16))
    source_id: Mapped[UUID]
    source_version: Mapped[int]
    source_title: Mapped[str] = mapped_column(String(200), default="")
    engine: Mapped[str] = mapped_column(String(40))
    policy_versions: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # The source projection the engine read, so the run can be reproduced byte for byte.
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB)


class MatchResultRecord(Row, Base):
    """One target's result in a run."""

    __tablename__ = "match_results"

    run_id: Mapped[UUID] = mapped_column(ForeignKey("match_runs.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    shown: Mapped[bool]
    opportunity_version_id: Mapped[UUID]
    eligibility: Mapped[str] = mapped_column(String(24))
    readiness: Mapped[str] = mapped_column(String(32))
    relevant: Mapped[bool]
    fit_lower: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    fit_upper: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    coverage: Mapped[Decimal] = mapped_column(Numeric(3, 2))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)
