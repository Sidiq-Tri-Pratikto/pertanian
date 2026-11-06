"""In-app notifications as outbox consumers: one per event, party and channel (FR-002, AC46)."""

from collections.abc import Awaitable, Callable
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.discussion.repository.sqlalchemy.repository import SqlAlchemyDiscussionRepository
from app.pitches.service.decisions import pitch_by_id
from app.worker.registry import registry

CONSUMER = "notifications.in_app"

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
    if target == "other":
        actor = UUID(payload["actor_party_id"])
        party = record.recipient_party_id if actor == record.requester_party_id else record.requester_party_id
    else:
        party = record.requester_party_id if target == "requester" else record.recipient_party_id
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


def _consumer(topic: str) -> Callable[[AsyncSession, dict[str, Any]], Awaitable[None]]:
    async def handle(session: AsyncSession, payload: dict[str, Any]) -> None:
        await notify(session, topic, payload)

    return handle


for _topic in RULES:
    registry.consumer(_topic, CONSUMER)(_consumer(_topic))
