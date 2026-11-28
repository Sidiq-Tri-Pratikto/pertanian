"""Development-only endpoints. ``create_app`` mounts them only when ``ENVIRONMENT=development``."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from pydantic import AwareDatetime, BaseModel
from sqlalchemy.dialects.postgresql import Range

from app.core.database import SessionDep
from app.core.errors.base import NotFoundError
from app.core.settings import get_settings
from app.identity.model.schema import Email, MailboxMessageResponse
from app.identity.repository.sqlalchemy.repository import SqlAlchemyIdentityRepository
from app.scheduling.repository.sqlalchemy.models import BookingRecord
from app.scheduling.repository.sqlalchemy.repository import SqlAlchemySchedulingRepository
from app.subscriptions.repository.sqlalchemy.models import InvestorSubscriptionRecord
from app.subscriptions.service import mail
from app.subscriptions.service.matching import Match

router = APIRouter(prefix="/dev", tags=["development"])


class DevBookingRequest(BaseModel):
    """A busy interval for one party."""

    party_id: UUID
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    title: str = "Agenda lain"


@router.get("/mailbox", summary="Read the development mailbox")
async def read_mailbox(email: Email, session: SessionDep) -> list[MailboxMessageResponse]:
    """Return the newest messages sent to an email, so sign-in can be tested without real email.

    Args:
        email (Email): Recipient.
        session (SessionDep): Database session.

    Returns:
        list[MailboxMessageResponse]: Newest first.
    """
    messages = await SqlAlchemyIdentityRepository(session).mailbox(email)
    return [MailboxMessageResponse(to_email=m.to_email, subject=m.subject, body=m.body, html=m.html) for m in messages]


@router.get("/mail-preview/{template}", response_class=HTMLResponse, summary="Preview one investor email template")
async def preview_mail(template: str, lang: Literal["id", "en"] = Query(default="id")) -> HTMLResponse:
    """Render an investor email template with sample data in development (spec 060)."""
    settings = get_settings()
    origin = settings.web_origin
    topics = {"sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"], "keywords": ["air"]}
    sample_record = InvestorSubscriptionRecord(
        email="investor@example.test",
        topics=topics,
        status="ACTIVE",
        locale=lang,
        confirmed_at=datetime(2026, 4, 1, 2, 0, tzinfo=UTC),
    )
    sample_a = {
        "id": "00000000-0000-0000-0000-000000000001",
        "title": "Sistem Filter Air Tenaga Surya",
        "summary": (
            "Penyaring air berdaya surya untuk desa tanpa listrik stabil. "
            "Kapasitas 2.000 liter per hari dengan biaya perawatan rendah."
        ),
        "sector": "Air dan sanitasi",
        "stage": "PROTOTYPE",
        "tkt_level": 4,
        "inventor_name": "Rina Kusuma",
        "anonymous": False,
        "public_page": True,
        "field_test": "Uji coba terbatas di dua desa di Jawa Barat selama 30 hari.",
        "photo_version_id": None,
        "photo": (None, None, None),
    }
    sample_b = {
        **sample_a,
        "id": "00000000-0000-0000-0000-000000000002",
        "title": "Sensor Kelembapan Tanah Hemat Energi",
        "summary": "Sensor irigasi presisi dengan baterai 12 bulan untuk kebun hortikultura skala menengah.",
        "sector": "Pertanian",
        "stage": "PILOT",
        "tkt_level": 5,
        "field_test": None,
    }
    reason_a = Match(level="ALERT", reasons=["Air dan sanitasi", "Prototipe", "air"])
    reason_b = Match(level="DIGEST", reasons=["Pertanian", "Pilot"])

    if template == "confirm":
        _, _, html, _ = mail.confirm(origin, "sample-confirm-token", topics, lang, demo=settings.demo_mode)
    elif template == "already":
        _, _, html, _ = mail.already_subscribed(origin, "sample-manage-token", lang, demo=settings.demo_mode)
    elif template == "alert":
        _, _, html, _ = mail.alert(
            settings, sample_a, reason_a, sample_record, "sample-manage-token", unsubscribe_token="sample-unsub-token"
        )
    elif template == "digest":
        _, _, html, _ = mail.digest(
            settings,
            [(sample_a, reason_a), (sample_b, reason_b)],
            sample_record,
            "sample-manage-token",
            unsubscribe_token="sample-unsub-token",
        )
    elif template == "follow_confirm":
        _, _, html, _ = mail.follow_confirm(
            origin, "sample-confirm-token", sample_a["title"], lang, demo=settings.demo_mode
        )
    elif template == "follow_already":
        _, _, html, _ = mail.already_following(
            origin, "sample-manage-token", sample_a["title"], lang, demo=settings.demo_mode
        )
    elif template == "follow_update":
        _, _, html, _ = mail.follow_update(
            settings,
            sample_a["id"],
            sample_a["title"],
            "Uji coba 30 hari selesai di desa kedua",
            "Debit stabil pada 1.950 liter per hari selama musim kemarau; dokumentasi uji siap ditinjau.",
            "sample-manage-token",
            lang,
            unsubscribe_token="sample-unsub-token",
        )
    else:
        raise NotFoundError()
    return HTMLResponse(content=html)


@router.post("/bookings", status_code=201, summary="Book a party's time, for tests")
async def book_time(body: DevBookingRequest, session: SessionDep) -> dict[str, str]:
    """Mark a party busy, as another meeting would, so conflicts can be shown without a second pitch.

    Args:
        body (DevBookingRequest): Party, interval and title.
        session (SessionDep): Database session.

    Returns:
        dict[str, str]: The booking id.
    """
    repository = SqlAlchemySchedulingRepository(session)
    await repository.lock_booking_parties(body.party_id)
    booking = await repository.add(
        BookingRecord(party_id=body.party_id, title=body.title, during=Range(body.starts_at, body.ends_at, bounds="[)"))
    )
    return {"id": str(booking.id)}


@router.post("/digest", summary="Send the weekly investor digest now, for tests")
async def send_digest(session: SessionDep) -> dict[str, int]:
    """Run the weekly digest at once instead of waiting for Monday.

    Args:
        session (SessionDep): Database session.

    Returns:
        dict[str, int]: Digests sent.
    """
    from app.subscriptions.service.service import SubscriptionService  # noqa: PLC0415 - development only

    return {"sent": await SubscriptionService(session).digest()}
