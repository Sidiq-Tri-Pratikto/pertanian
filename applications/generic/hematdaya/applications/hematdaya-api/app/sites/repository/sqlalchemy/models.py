"""Site ORM record."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SiteRecord(Base):
    """Row in ``sites``."""

    __tablename__ = "sites"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_principal_id: Mapped[UUID] = mapped_column(ForeignKey("principals.id"), index=True)
    kind: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text, default="unspecified")
    timezone: Mapped[str] = mapped_column(Text, default="Asia/Jakarta")
    currency: Mapped[str] = mapped_column(Text, default="IDR")
    virtual_now: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    binding_revision: Mapped[int] = mapped_column(BigInteger, default=0)
    measurement_revision: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
