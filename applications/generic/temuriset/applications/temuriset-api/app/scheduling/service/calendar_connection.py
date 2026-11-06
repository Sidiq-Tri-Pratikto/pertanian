"""Account-owned consent, expiring OAuth state and generation-checked credentials."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from hmac import compare_digest, digest
from secrets import token_urlsafe
from typing import Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import require_account
from app.core.errors import codes
from app.core.errors.base import AppError, InvalidTransitionError, NotFoundError, UnauthenticatedError
from app.core.errors.public import public_error_for_code
from app.core.errors.recorder import record_failure
from app.core.secret_envelope import InvalidEnvelopeError, open_sealed, seal
from app.core.settings import Settings
from app.identity.model.models import Principal
from app.identity.service.accounts import account_is_active
from app.platform.service.versions import check_expected
from app.scheduling.model.schema import CalendarStatusResponse
from app.scheduling.repository.sqlalchemy.models import CalendarConnectionRecord
from app.scheduling.repository.sqlalchemy.repository import SqlAlchemySchedulingRepository
from app.scheduling.service.calendar_adapter import CalendarToken, CalendarUnavailableError, calendar_adapter

_PENDING_TTL = timedelta(minutes=5)


class CalendarCallbackInvalidError(AppError):
    """The callback cannot complete the signed-in session's pending consent."""

    code = codes.APP_CALENDAR_CALLBACK_INVALID


@dataclass(frozen=True)
class PendingCalendarAttempt:
    """The consumed generation and its in-memory verifier."""

    version: int
    verifier: str = field(repr=False)


@dataclass(frozen=True)
class CalendarCredential:
    """A generation-scoped bearer token kept in memory for one lookup."""

    version: int
    token: str = field(repr=False)


def record_calendar_failure(error: AppError, operation: str) -> None:
    """Record an advisory failure at the boundary where it becomes a safe fallback."""
    record_failure(error, operation=operation, http_status=public_error_for_code(error.code).http_status)


def _clear_pending(record: CalendarConnectionRecord) -> None:
    record.state_sha256 = record.encrypted_verifier = None
    record.state_session_id = record.state_expires_at = None


def _status(record: CalendarConnectionRecord | None, *, enabled: bool = True) -> CalendarStatusResponse:
    if not enabled:
        has_data = record is not None and (record.encrypted_token is not None or record.state_expires_at is not None)
        return CalendarStatusResponse(
            state="off_with_connection" if has_data else "off",
            version=record.version if record is not None else 0,
            revocation=_revocation(record),
        )
    if record is None:
        return CalendarStatusResponse(state="disconnected", version=0)
    now = datetime.now(UTC)
    if record.token_expires_at is not None:
        state = "connected" if record.token_expires_at > now else "expired"
        return CalendarStatusResponse(state=state, version=record.version)
    if record.state_expires_at is not None and record.state_expires_at > now:
        return CalendarStatusResponse(state="pending", version=record.version)
    return CalendarStatusResponse(state="disconnected", version=record.version, revocation=_revocation(record))


def _revocation(record: CalendarConnectionRecord | None) -> Literal["confirmed", "unconfirmed"] | None:
    if record is None or record.provider_revocation_confirmed is None:
        return None
    return "confirmed" if record.provider_revocation_confirmed else "unconfirmed"


async def erase_calendar_connection(session: AsyncSession, account_id: UUID) -> None:
    """Erase all local calendar data during the account-profile deletion transaction."""
    await SqlAlchemySchedulingRepository(session).erase_calendar(account_id)


class CalendarConnectionService:
    """Read and mutate only the signed-in account's calendar generation."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind calendar policy to the request's repository and deployment."""
        self.session = session
        self.repository = SqlAlchemySchedulingRepository(session)
        self.adapter = calendar_adapter(settings)
        self.key = settings.calendar_envelope_key

    @property
    def enabled(self) -> bool:
        """Whether calendar credentials can be decrypted and used in this process."""
        return self.adapter.enabled and self.key is not None

    def require_enabled(self) -> None:
        """Keep loopback operations unavailable in the off profile."""
        if not self.enabled:
            raise NotFoundError()

    async def status(self, principal: Principal) -> CalendarStatusResponse:
        """Report the owner's current state, including the adapter-off profile."""
        return _status(await self._read(principal), enabled=self.enabled)

    async def begin(self, principal: Principal, expected_version: int) -> CalendarStatusResponse:
        """Create or replace a short-lived, explicit consent attempt."""
        self.require_enabled()
        record = await self.repository.lock_calendar(principal.account_id)
        require_account(principal, record.account_id)
        await self._require_active(principal)
        check_expected(record.version, expected_version)
        if _status(record).state == "connected":
            raise InvalidTransitionError()
        verifier = token_urlsafe(48)
        record.version += 1
        record.encrypted_token = record.token_expires_at = None
        record.provider_revocation_confirmed = None
        record.state_sha256 = sha256(self._state(verifier).encode("ascii")).hexdigest()
        record.encrypted_verifier = seal(self._key(), self._purpose(record, "verifier"), verifier.encode("ascii"))
        record.state_session_id = principal.session_id
        record.state_expires_at = datetime.now(UTC) + _PENDING_TTL
        return _status(record)

    async def authorization(self, principal: Principal, version: int) -> str:
        """Send the initiating session to the configured provider with a fresh PKCE challenge."""
        self.require_enabled()
        record = await self._pending(principal)
        check_expected(record.version, version)
        verifier = self._open(record, "verifier", record.encrypted_verifier)
        return self.adapter.authorization(self._state(verifier), verifier)

    async def consume(self, principal: Principal, state: str) -> PendingCalendarAttempt:
        """Consume the exact live state under an account lock before any token exchange."""
        self.require_enabled()
        record = await self._pending(principal, lock=True)
        if not compare_digest(record.state_sha256 or "", sha256(state.encode("utf-8")).hexdigest()):
            raise CalendarCallbackInvalidError()
        verifier = self._open(record, "verifier", record.encrypted_verifier)
        record.state_sha256 = record.encrypted_verifier = None
        return PendingCalendarAttempt(record.version, verifier)

    async def complete(
        self,
        principal: Principal,
        version: int,
        token: CalendarToken,
    ) -> bool:
        """Install a credential only when this consumed attempt is still current."""
        record = await self._read(principal, lock=True)
        if (
            record is None
            or record.version != version
            or record.state_session_id != principal.session_id
            or record.state_expires_at is None
            or record.state_expires_at <= datetime.now(UTC)
            or record.state_sha256 is not None
            or token.expires_at <= datetime.now(UTC)
        ):
            return False
        record.version += 1
        record.encrypted_token = seal(
            self._key(), self._purpose(record, "access-token"), token.access_token.encode("ascii")
        )
        record.token_expires_at = token.expires_at
        _clear_pending(record)
        return True

    async def abandon(self, principal: Principal, version: int) -> None:
        """Clean up a failed consumed flow without touching a newer one."""
        record = await self._read(principal, lock=True)
        if record is not None and record.version == version and record.state_session_id == principal.session_id:
            _clear_pending(record)
            record.version += 1

    async def invalidate(
        self,
        principal: Principal,
        expected_version: int,
    ) -> tuple[CalendarStatusResponse, str | None, bool]:
        """Delete pending state and the stored token locally before attempting provider revocation."""
        record = await self._read(principal, lock=True)
        if record is None or (not self.enabled and _status(record, enabled=False).state != "off_with_connection"):
            raise NotFoundError()
        await self._require_active(principal)
        check_expected(record.version, expected_version)
        had_token = record.encrypted_token is not None
        token = None
        if had_token and self.enabled:
            try:
                token = self._open(record, "access-token", record.encrypted_token)
            except CalendarUnavailableError as error:
                record_calendar_failure(error, "calendar.disconnect")
        _clear_pending(record)
        record.encrypted_token = record.token_expires_at = None
        record.provider_revocation_confirmed = False if had_token else None
        record.version += 1
        return _status(record, enabled=self.enabled), token, had_token

    async def confirm_revocation(self, principal: Principal, version: int) -> None:
        """Record the provider confirmation separately from the stable local operation receipt."""
        record = await self._read(principal, lock=True)
        if record is not None and record.version == version and record.provider_revocation_confirmed is False:
            record.provider_revocation_confirmed = True

    async def _require_active(self, principal: Principal) -> None:
        # The account erasure transaction freezes sign-in before removing this row. A request resolved
        # earlier may not leave behind a new generation after the freeze.
        if not await account_is_active(self.session, principal.account_id):
            raise UnauthenticatedError()

    async def credential(self, principal: Principal) -> CalendarCredential | None:
        """Return the account's own currently usable token, without locking across the lookup."""
        if not self.enabled:
            return None
        record = await self._read(principal)
        if record is None or _status(record).state != "connected":
            return None
        return CalendarCredential(record.version, self._open(record, "access-token", record.encrypted_token))

    async def current(self, principal: Principal, version: int) -> bool:
        """Check the generation at the end of the lookup and serialize it with a disconnect."""
        record = await self._read(principal, lock=True)
        return record is not None and record.version == version and _status(record).state == "connected"

    async def _read(self, principal: Principal, *, lock: bool = False) -> CalendarConnectionRecord | None:
        record = await self.repository.calendar(principal.account_id, lock=lock)
        if record is not None:
            require_account(principal, record.account_id)
        return record

    async def _pending(self, principal: Principal, *, lock: bool = False) -> CalendarConnectionRecord:
        record = await self._read(principal, lock=lock)
        if (
            record is None
            or record.state_session_id != principal.session_id
            or record.state_expires_at is None
            or record.state_expires_at <= datetime.now(UTC)
            or record.state_sha256 is None
        ):
            raise CalendarCallbackInvalidError()
        return record

    def _key(self) -> str:
        if self.key is None:
            raise CalendarUnavailableError("missing calendar credential key")
        return self.key.get_secret_value()

    def _state(self, verifier: str) -> str:
        # The browser can get the same state again, while the database holds only a hash and ciphertext.
        return digest(self._key().encode("ascii"), f"calendar:state:{verifier}".encode("ascii"), "sha256").hex()

    @staticmethod
    def _purpose(record: CalendarConnectionRecord, kind: str) -> str:
        return f"calendar:{kind}:{record.account_id}:{record.version}"

    def _open(self, record: CalendarConnectionRecord, kind: str, envelope: bytes | None) -> str:
        if envelope is None:
            raise CalendarUnavailableError("missing calendar credential envelope")
        try:
            # A completed token belongs to the new generation that was recorded with it.
            return open_sealed(self._key(), self._purpose(record, kind), envelope).decode("ascii")
        except (InvalidEnvelopeError, UnicodeError) as error:
            raise CalendarUnavailableError("invalid calendar credential envelope", error) from error
