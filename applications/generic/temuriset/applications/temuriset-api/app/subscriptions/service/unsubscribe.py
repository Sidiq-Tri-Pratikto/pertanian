"""RFC 8058 one-click unsubscribe token minting and idempotent consumption for subscriptions and follows (spec 060)."""

import hashlib
import secrets
from datetime import timedelta
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.core.errors.base import NotFoundError
from app.subscriptions.repository.sqlalchemy.models import (
    InventionFollowRecord,
    InvestorSubscriptionRecord,
    UnsubscribeLinkRecord,
)

UNSUBSCRIBE_LIFETIME = timedelta(days=365)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def mint_unsubscribe_token(
    session: AsyncSession, kind: Literal["subscription", "follow"], target_id: UUID
) -> str:
    """Create a 365-day single-purpose unsubscribe token, storing only its SHA-256 hash."""
    token = secrets.token_urlsafe(32)
    session.add(
        UnsubscribeLinkRecord(
            kind=kind,
            target_id=target_id,
            token_sha256=_hash(token),
            expires_at=clock.now() + UNSUBSCRIBE_LIFETIME,
        )
    )
    await session.flush()
    return token


async def consume_one_click(session: AsyncSession, token: str) -> dict[str, str]:
    """Unsubscribe the subscription or follow referenced by ``token``; idempotent if already unsubscribed."""
    if not token or len(token) < 20 or len(token) > 200:
        raise NotFoundError()
    link = await session.scalar(select(UnsubscribeLinkRecord).where(UnsubscribeLinkRecord.token_sha256 == _hash(token)))
    if link is None or link.expires_at <= clock.now():
        raise NotFoundError()

    if link.kind == "subscription":
        record = await session.get(InvestorSubscriptionRecord, link.target_id, with_for_update=True)
    else:
        record = await session.get(InventionFollowRecord, link.target_id, with_for_update=True)

    if record is None:
        raise NotFoundError()
    if record.status != "UNSUBSCRIBED":
        record.status = "UNSUBSCRIBED"
        record.unsubscribed_at = clock.now()
        record.version += 1
        await session.flush()
    return {"status": "unsubscribed"}
