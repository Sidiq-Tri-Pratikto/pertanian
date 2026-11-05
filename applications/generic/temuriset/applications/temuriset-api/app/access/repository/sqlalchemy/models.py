"""Parties: who acts. Spec 006 creates personal parties; spec 007 adds organizations."""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, MutableRow


class PartyRecord(MutableRow, Base):
    """A personal party (one per account) or, from 007, an organization party."""

    __tablename__ = "parties"
    __table_args__ = (CheckConstraint("kind = 'personal' AND account_id IS NOT NULL", name="kind"),)

    kind: Mapped[str] = mapped_column(String(16))
    display_name: Mapped[str] = mapped_column(String(160))
    account_id: Mapped[UUID | None] = mapped_column(ForeignKey("accounts.id", ondelete="RESTRICT"), unique=True)
