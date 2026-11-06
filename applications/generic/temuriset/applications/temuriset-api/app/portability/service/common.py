"""Shared requester checks and generated artifact identifiers."""

from collections.abc import AsyncIterator
from dataclasses import replace
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import require
from app.access.service.service import party_access_for, personal_party_id
from app.core.errors.base import NotFoundError
from app.documents.service.service import FileTooLargeError
from app.identity.model.models import Principal
from app.identity.service.accounts import account_is_active
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.portability.repository.sqlalchemy.models import ExportJobRecord, ImportRunRecord


async def actor_membership(session: AsyncSession, actor: Principal) -> UUID | None:
    """Authorize portability in the active context and capture its current membership."""
    if not await account_is_active(session, actor.account_id):
        raise NotFoundError()
    access = await party_access_for(session, actor.account_id, actor.active_party_id)
    if access is None:
        raise NotFoundError()
    require(replace(actor, capabilities=access[0]), Capability.EDIT_PORTFOLIO, actor.active_party_id)
    return access[1]


async def live_actor(session: AsyncSession, record: ImportRunRecord | ExportJobRecord) -> Principal:
    """Rebuild the original actor from live access and the pinned membership identity."""
    if not await account_is_active(session, record.account_id):
        raise NotFoundError()
    access = await party_access_for(session, record.account_id, record.party_id)
    if access is None or access[1] != record.membership_id:
        raise NotFoundError()
    actor = Principal(
        account_id=record.account_id,
        session_id=record.session_id,
        personal_party_id=await personal_party_id(session, record.account_id),
        active_party_id=record.party_id,
        capabilities=access[0],
    )
    require(actor, Capability.EDIT_PORTFOLIO, record.party_id)
    return actor


async def announce(session: AsyncSession, record: ImportRunRecord | ExportJobRecord, subject: str, event: str) -> None:
    """Audit and publish only the internal subject ID and transition name."""
    action = f"portability.{subject}.{event}"
    await record_audit(
        session,
        action=action,
        subject_type=subject,
        subject_id=str(record.id),
        actor_party_id=record.party_id,
        actor_account_id=record.account_id,
    )
    await publish(session, action, {"id": str(record.id)})


def artifact_key(kind: str, identifier: UUID) -> str:
    """Derive an internal key from the generated ID without using uploaded labels."""
    return f"portability-{kind}-{identifier.hex}.json"


async def byte_chunks(data: bytes) -> AsyncIterator[bytes]:
    """Pass already bounded bytes to the private storage adapter."""
    for offset in range(0, len(data), 65_536):
        yield data[offset : offset + 65_536]


async def read_bounded(chunks: AsyncIterator[bytes], limit: int, *, limit_text: str = "20 MiB") -> bytes:
    """Read at most the declared portable file limit, including chunked requests."""
    data = bytearray()
    async for chunk in chunks:
        if len(data) + len(chunk) > limit:
            raise FileTooLargeError(limit_text)
        data.extend(chunk)
    return bytes(data)
