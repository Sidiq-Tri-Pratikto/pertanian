"""Independent in-app and optional email notifications from the same pitch events (AC46)."""

from collections.abc import Awaitable, Callable
from hashlib import sha256
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.service import assert_can_act, authorized_accounts
from app.core import clock
from app.core.errors.base import ForbiddenError, NotFoundError
from app.core.settings import get_settings
from app.discussion.repository.sqlalchemy.repository import SqlAlchemyDiscussionRepository
from app.identity.service.accounts import email_notification_accounts, email_notification_address
from app.identity.service.mailbox_service import (
    NOTIFICATION_DELIVERY,
    NOTIFICATION_RETRY_WINDOW,
    deliver_to_relay,
    loopback_mail_enabled,
)
from app.pitches.repository.sqlalchemy.models import PitchRecord
from app.pitches.service.decisions import CAPABILITY_OF, pitch_by_id
from app.pitches.service.transitions import Side
from app.platform.service.outbox import enqueue_job
from app.worker.registry import registry

CONSUMER = "notifications.in_app"
EMAIL_CONSUMER = "notifications.email"

Target = Literal["requester", "recipient", "other"]

# topic: (who is told, the text before the subject title, the room tab it opens)
RULES: dict[str, tuple[Target, str, str]] = {
    "pitch.submitted": ("recipient", "Pitching baru", "ringkasan"),
    "pitch.approve": ("requester", "Pitching disetujui untuk diskusi", "jadwal"),
    "pitch.reject": ("requester", "Pitching ditolak", "ringkasan"),
    "pitch.request_revision": ("requester", "Revisi diminta", "revisi"),
    "pitch.resubmit": ("recipient", "Pitching dikirim ulang", "revisi"),
    "pitch.withdraw": ("recipient", "Pitching ditarik", "ringkasan"),
    "pitch.close": ("other", "Diskusi ditutup", "ringkasan"),
    "schedule.proposed": ("other", "Usulan waktu pertemuan baru", "jadwal"),
    "meeting.confirmed": ("other", "Waktu pertemuan dikonfirmasi", "jadwal"),
    "meeting.replaced": ("other", "Jadwal pengganti dikonfirmasi", "jadwal"),
    "meeting.cancelled": ("other", "Pertemuan dibatalkan", "jadwal"),
    "partnership.proposed": ("other", "Ringkasan Kerja Sama perlu konfirmasi", "ringkasan"),
    "partnership.corrected": ("other", "Ringkasan Kerja Sama dikoreksi", "ringkasan"),
    "partnership.confirmed": ("other", "Kerja Sama dikonfirmasi kedua pihak", "ringkasan"),
}


def event_key(topic: str, payload: dict[str, Any]) -> str:
    """Name one event stably, so a redelivery finds the notification it already made.

    Args:
        topic (str): The topic.
        payload (dict[str, Any]): The payload.

    Returns:
        str: The key.
    """
    subject = payload.get("meeting_id") or payload.get("proposal_id") or payload.get("version")
    return f"{topic}:{payload['pitch_id']}:{subject}"


async def notify(session: AsyncSession, topic: str, payload: dict[str, Any]) -> None:
    """Tell the party that must act now, in the app.

    Args:
        session (AsyncSession): The worker's session.
        topic (str): The topic.
        payload (dict[str, Any]): The event payload.
    """
    target, text, tab = RULES[topic]
    record = await pitch_by_id(session, UUID(payload["pitch_id"]))
    if record is None:
        return
    party, _side = _target_party(record, target, payload)
    await SqlAlchemyDiscussionRepository(session).notify(
        {
            "party_id": party,
            "pitch_id": record.id,
            "event_key": event_key(topic, payload),
            "channel": "in_app",
            "text": f"{text}: {record.subject_title} → {record.opportunity_title}"[:300],
            "tab": tab,
        }
    )


def _target_party(record: PitchRecord, target: Target, payload: dict[str, Any]) -> tuple[UUID, Side]:
    side = target
    if side == "other":
        side = "recipient" if UUID(payload["actor_party_id"]) == record.requester_party_id else "requester"
    return (record.requester_party_id if side == "requester" else record.recipient_party_id), side


def _delivery_capability(topic: str, side: Side) -> Capability:
    if topic.startswith(("meeting.", "schedule.")):
        return Capability.SCHEDULE
    if topic.startswith("partnership."):
        return Capability.CONFIRM_RELATIONSHIP
    return CAPABILITY_OF[side]


async def _queue_email(session: AsyncSession, topic: str, payload: dict[str, Any]) -> None:
    if not loopback_mail_enabled(get_settings()):
        return
    record = await pitch_by_id(session, UUID(payload["pitch_id"]))
    if record is None:
        return
    party_id, side = _target_party(record, RULES[topic][0], payload)
    candidates = await authorized_accounts(session, party_id, _delivery_capability(topic, side))
    for account_id in await email_notification_accounts(session, candidates):
        key = sha256(f"{event_key(topic, payload)}:{account_id}:email".encode()).hexdigest()
        await enqueue_job(
            session,
            NOTIFICATION_DELIVERY,
            {
                "key": key,
                "topic": topic,
                "account_id": str(account_id),
                "party_id": str(party_id),
                "pitch_id": str(record.id),
            },
            dedupe_key=key,
            input_expires_at=clock.now() + NOTIFICATION_RETRY_WINDOW,
        )


@registry.job(NOTIFICATION_DELIVERY)
async def deliver_notification(session: AsyncSession, job_input: dict[str, Any]) -> None:
    """Recheck the event's party access and the recipient's live opt-in on every attempt."""
    settings = get_settings()
    if not loopback_mail_enabled(settings):
        return
    party_id, account_id = UUID(job_input["party_id"]), UUID(job_input["account_id"])
    record = await pitch_by_id(session, UUID(job_input["pitch_id"]))
    if record is None or party_id not in (record.requester_party_id, record.recipient_party_id):
        return
    side = "requester" if party_id == record.requester_party_id else "recipient"
    try:
        await assert_can_act(session, account_id, party_id, _delivery_capability(job_input["topic"], side))
    except (ForbiddenError, NotFoundError):
        return
    address = await email_notification_address(session, account_id)
    if address is None:
        return
    await deliver_to_relay(
        settings,
        delivery_key=job_input["key"],
        to_email=address,
        subject="Pemberitahuan TemuRiset",
        body=(
            "Ada pembaruan yang perlu Anda tinjau di TemuRiset. Masuk untuk melihat pemberitahuan:\n\n"
            f"{settings.web_origin.rstrip('/')}/home"
        ),
    )


def _consumer(
    topic: str, notify_for_channel: Callable[[AsyncSession, str, dict[str, Any]], Awaitable[None]]
) -> Callable[[AsyncSession, dict[str, Any]], Awaitable[None]]:
    async def handle(session: AsyncSession, payload: dict[str, Any]) -> None:
        await notify_for_channel(session, topic, payload)

    return handle


for _topic in RULES:
    registry.consumer(_topic, CONSUMER)(_consumer(_topic, notify))
    registry.consumer(_topic, EMAIL_CONSUMER)(_consumer(_topic, _queue_email))
