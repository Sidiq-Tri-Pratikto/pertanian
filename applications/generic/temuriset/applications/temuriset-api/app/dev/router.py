"""Development-only endpoints. ``create_app`` mounts them only when ``ENVIRONMENT=development``."""

from fastapi import APIRouter

from app.core.database import SessionDep
from app.identity.model.schema import Email, MailboxMessageResponse
from app.identity.repository.sqlalchemy.repository import SqlAlchemyIdentityRepository

router = APIRouter(prefix="/dev", tags=["development"])


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
