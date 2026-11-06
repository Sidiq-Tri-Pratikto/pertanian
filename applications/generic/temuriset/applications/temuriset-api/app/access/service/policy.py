"""The one authorization policy (architecture: deny by default, NOT_FOUND for the invisible, FORBIDDEN for the rest)."""

from uuid import UUID

from app.access.model.models import Capability
from app.core.errors import codes
from app.core.errors.base import AppError, ForbiddenError, NotFoundError
from app.identity.model.models import Principal


class StaleContextError(AppError):
    """The request acts as a party other than the session's active party."""

    code = codes.APP_STALE_CONTEXT


def check_context(principal: Principal, acting_party_id: UUID) -> None:
    """Refuse a consequential action sent from a tab that still shows another context.

    Args:
        principal (Principal): Who is signed in.
        acting_party_id (UUID): The party the client believes it acts as.

    Raises:
        StaleContextError: When it differs from the session's active party.
    """
    if acting_party_id != principal.active_party_id:
        raise StaleContextError()


def require(principal: Principal, action: Capability, owner_party_id: UUID) -> None:
    """Allow an action on a resource owned by a party.

    Args:
        principal (Principal): Who is signed in, with the active party's capabilities.
        action (Capability): What the request does.
        owner_party_id (UUID): The party that owns the resource.

    Raises:
        NotFoundError: When the active party does not own the resource, so its existence stays hidden (AC05).
        ForbiddenError: When the active party owns it but lacks the capability (AC04).
    """
    if owner_party_id != principal.active_party_id:
        raise NotFoundError()
    if action not in principal.capabilities:
        raise ForbiddenError()


def require_account(principal: Principal, owner_account_id: UUID) -> None:
    """Restrict a private record to its owning account, even in an organization context."""
    if principal.account_id != owner_account_id:
        raise NotFoundError()


def require_operator_scope(*, granted: bool) -> None:
    """Keep operator surfaces invisible to accounts without the required live grant."""
    if not granted:
        raise NotFoundError()


def require_case_file(*, granted: bool) -> None:
    """Deny a file action within an already visible operator case without an exact grant."""
    if not granted:
        raise ForbiddenError()
