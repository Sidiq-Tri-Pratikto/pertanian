"""Development-only endpoints. ``create_app`` mounts them only when ``ENVIRONMENT=development``."""

from uuid import UUID

from fastapi import APIRouter
from pydantic import AwareDatetime, BaseModel
from sqlalchemy.dialects.postgresql import Range

from app.core.database import SessionDep
from app.identity.model.schema import Email, MailboxMessageResponse
from app.identity.repository.sqlalchemy.repository import SqlAlchemyIdentityRepository
from app.scheduling.repository.sqlalchemy.models import BookingRecord

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
    return [MailboxMessageResponse(to_email=m.to_email, subject=m.subject, body=m.body) for m in messages]


@router.post("/bookings", status_code=201, summary="Book a party's time, for tests")
async def book_time(body: DevBookingRequest, session: SessionDep) -> dict[str, str]:
    """Mark a party busy, as another meeting would, so conflicts can be shown without a second pitch.

    Args:
        body (DevBookingRequest): Party, interval and title.
        session (SessionDep): Database session.

    Returns:
        dict[str, str]: The booking id.
    """
    booking = BookingRecord(
        party_id=body.party_id, title=body.title, during=Range(body.starts_at, body.ends_at, bounds="[)")
    )
    session.add(booking)
    await session.flush()
    return {"id": str(booking.id)}
