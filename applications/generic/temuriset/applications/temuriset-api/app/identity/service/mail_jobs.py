"""Worker delivery of short-lived authentication and invitation messages."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.service import invitation_deliverable
from app.core import clock
from app.core.secret_envelope import InvalidEnvelopeError, open_sealed
from app.core.settings import get_settings
from app.identity.repository.sqlalchemy.repository import SqlAlchemyIdentityRepository
from app.identity.service.codes import MAX_CODE_ATTEMPTS
from app.identity.service.mailbox_service import (
    SECRET_DELIVERY,
    SECRET_PURPOSE,
    MailRelayRejectedError,
    deliver_to_relay,
    loopback_mail_enabled,
)
from app.worker.registry import registry


class _SecretMessage(BaseModel):
    to: str
    subject: str
    body: str
    source_kind: Literal["code", "invitation"]
    source_id: UUID


async def _code_deliverable(session: AsyncSession, message: _SecretMessage) -> bool:
    repository = SqlAlchemyIdentityRepository(session)
    account = await repository.find_account_by_email(message.to)
    if account is not None and (account.status != "active" or account.kind == "demo"):
        return False
    code = await repository.latest_open_code(message.to)
    return (
        code is not None
        and code.id == message.source_id
        and code.expires_at > clock.now()
        and code.attempts < MAX_CODE_ATTEMPTS
        and (account is not None or code.profile is not None)
    )


@registry.job(SECRET_DELIVERY)
async def deliver_secret(session: AsyncSession, job_input: dict[str, Any]) -> None:
    """Open an unexpired job envelope only when the relay remains available."""
    settings = get_settings()
    if not loopback_mail_enabled(settings) or settings.email_envelope_key is None:
        return
    try:
        delivery_key = job_input["key"]
        plaintext = open_sealed(
            settings.email_envelope_key.get_secret_value(),
            f"{SECRET_PURPOSE}:{delivery_key}",
            job_input["envelope"].encode("ascii"),
        )
        message = _SecretMessage.model_validate_json(plaintext)
    except (AttributeError, KeyError, UnicodeError, InvalidEnvelopeError, ValidationError) as error:
        raise MailRelayRejectedError() from error
    if message.source_kind == "code":
        deliverable = await _code_deliverable(session, message)
    else:
        deliverable = await invitation_deliverable(session, message.source_id, message.to)
    if not deliverable:
        return
    await deliver_to_relay(
        settings, delivery_key=delivery_key, to_email=message.to, subject=message.subject, body=message.body
    )
