"""Passwordless sign-in: emailed codes, server-side sessions, the signed-in account."""

import hashlib
import math
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.service import capabilities_for, create_personal_party, memberships_for, personal_party_id
from app.core import clock
from app.core.errors import codes as error_codes
from app.core.errors.base import AppError, NotFoundError, UnauthenticatedError
from app.core.settings import Settings
from app.identity.model.models import AccountModel, Principal
from app.identity.model.schema import (
    AccountResponse,
    CodeRequest,
    MembershipResponse,
    MeResponse,
    UpdateMeRequest,
    VerifyRequest,
)
from app.identity.repository.sqlalchemy.repository import SqlAlchemyIdentityRepository
from app.identity.service.codes import (
    MAX_CODE_ATTEMPTS,
    code_matches,
    hash_code,
    hash_token,
    new_code,
    new_salt,
    new_token,
)
from app.identity.service.mailbox_service import DisabledMailbox, MailboxAdapter, MailUnavailableError, mailbox_for
from app.platform.service.versions import StaleVersionError

CODE_LIFETIME = timedelta(minutes=10)
SESSION_LIFETIME = timedelta(days=30)
# Sliding expiry is written at most once an hour per session, not on every request.
SESSION_REFRESH = timedelta(hours=1)
RATE_WINDOW = timedelta(hours=1)

_CODE_SUBJECT = "Kode verifikasi TemuRiset"
_CODE_BODY = "Kode verifikasi Anda: {code}\n\nKode berlaku 10 menit. Abaikan email ini bila Anda tidak memintanya."
_NO_ACCOUNT_BODY = (
    "Belum ada akun TemuRiset untuk email ini. Buka halaman Mulai untuk mendaftar.\n\n"
    "Abaikan email ini bila Anda tidak memintanya."
)


class CodeInvalidError(AppError):
    """The submitted code does not match."""

    code = error_codes.APP_CODE_INVALID

    def __init__(self, attempts_left: int) -> None:
        """Report how many guesses remain.

        Args:
            attempts_left (int): Remaining guesses for this code.
        """
        super().__init__(public_fields={"attempts_left": attempts_left})


class CodeExpiredError(AppError):
    """No usable code: expired, used up, or never sent."""

    code = error_codes.APP_CODE_EXPIRED


class RateLimitedError(AppError):
    """Too many code requests in the window."""

    code = error_codes.APP_RATE_LIMITED

    def __init__(self, retry_after_seconds: int) -> None:
        """Say when the window frees up.

        Args:
            retry_after_seconds (int): Seconds until another request is allowed.
        """
        super().__init__()
        self.recovery["retry_after_seconds"] = retry_after_seconds


def hash_address(address: str) -> str:
    """Hash a client address so rate limiting stores no IP.

    Args:
        address (str): Client address.

    Returns:
        str: Hex SHA-256.
    """
    return hashlib.sha256(address.encode()).hexdigest()


class IdentityService:
    """Sign-up, sign-in, sessions and the account."""

    def __init__(self, session: AsyncSession, settings: Settings, mailbox: MailboxAdapter | None = None) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
            settings (Settings): Settings.
            mailbox (MailboxAdapter | None, optional): Delivery. Defaults to the development mailbox.
        """
        self.session = session
        self.settings = settings
        self.mailbox = mailbox or mailbox_for(settings)
        self.repository = SqlAlchemyIdentityRepository(session)

    async def request_code(self, request: CodeRequest, client_address: str) -> None:
        """Send a code. The caller always answers the same way, so existence never leaks.

        Sign-up for an existing email signs in instead; sign-in for an unknown email sends a note instead of a code.

        Args:
            request (CodeRequest): Email, purpose and, for sign-up, the profile.
            client_address (str): Client address, for the per-address limit.

        Raises:
            RateLimitedError: Over five requests per email or 20 per address in an hour.
        """
        if isinstance(self.mailbox, DisabledMailbox):
            raise MailUnavailableError()
        address = hash_address(client_address)
        await self._enforce_rate_limit(email=request.email, address=address)
        account = await self.repository.find_account_by_email(request.email, lock=True)
        if account is not None and account.status != "active":
            return
        if account is None and request.purpose == "sign_in":
            await self.mailbox.send(self.session, to_email=request.email, subject=_CODE_SUBJECT, body=_NO_ACCOUNT_BODY)
            return
        if account is None and not request.display_name:
            # Sign-up without a name cannot create an account; the web form always sends one.
            return
        code, salt = new_code(), new_salt()
        profile = (
            None
            if account is not None
            else {
                "display_name": request.display_name,
                "locale": request.locale,
                "time_zone": request.time_zone,
                "persona": request.persona,
            }
        )
        await self.repository.add_code(
            email=request.email,
            purpose=request.purpose,
            code_sha256=hash_code(code, salt),
            salt=salt,
            profile=profile,
            requester_address_sha256=address,
            expires_at=clock.now() + CODE_LIFETIME,
        )
        await self.mailbox.send(
            self.session, to_email=request.email, subject=_CODE_SUBJECT, body=_CODE_BODY.format(code=code)
        )

    async def _enforce_rate_limit(self, *, email: str, address: str) -> None:
        since = clock.now() - RATE_WINDOW
        limits = (
            ({"email": email, "address_sha256": None}, self.settings.code_requests_per_email_per_hour),
            ({"email": None, "address_sha256": address}, self.settings.code_requests_per_address_per_hour),
        )
        for scope, limit in limits:
            if await self.repository.count_codes(since=since, **scope) >= limit:
                oldest = await self.repository.oldest_code_time(since=since, **scope)
                wait = (oldest + RATE_WINDOW - clock.now()).total_seconds()
                raise RateLimitedError(max(1, math.ceil(wait)))

    async def verify(self, request: VerifyRequest) -> tuple[str, Principal]:
        """Check a code and start a session; a first sign-up creates the account and its personal party.

        Args:
            request (VerifyRequest): Email and code.

        Returns:
            tuple[str, Principal]: The session token for the cookie, and who is now signed in.

        Raises:
            CodeExpiredError: No open code, expired, or five wrong guesses already.
            CodeInvalidError: Wrong code; the guess is counted.
        """
        account = await self.repository.find_account_by_email(request.email, lock=True)
        if account is not None and account.status != "active":
            raise CodeExpiredError()
        record = await self.repository.latest_open_code(request.email)
        now = clock.now()
        if record is None or record.expires_at <= now or record.attempts >= MAX_CODE_ATTEMPTS:
            raise CodeExpiredError()
        if not code_matches(request.code, record.salt, record.code_sha256):
            await self.repository.count_attempt(record.id)
            # The guess must count even though this request fails, or the limit could be retried away.
            await self.session.commit()
            raise CodeInvalidError(attempts_left=MAX_CODE_ATTEMPTS - record.attempts - 1)
        await self.repository.consume_codes(request.email, now)
        if account is None:
            if record.profile is None:
                raise CodeExpiredError()
            account = await self.repository.create_account(email=request.email, email_verified_at=now, **record.profile)
            party_id = await create_personal_party(
                self.session, account_id=account.id, display_name=account.display_name
            )
        else:
            party_id = await personal_party_id(self.session, account.id)
        token = new_token()
        session_id = await self._start_session(account.id, token, party_id)
        return token, Principal(
            account_id=account.id,
            session_id=session_id,
            personal_party_id=party_id,
            active_party_id=party_id,
            capabilities=await capabilities_for(self.session, account.id, party_id) or frozenset(),
        )

    async def _start_session(self, account_id: UUID, token: str, party_id: UUID) -> UUID:
        now = clock.now()
        session_id = uuid4()
        await self.repository.add_session(
            id=session_id,
            account_id=account_id,
            token_sha256=hash_token(token),
            active_party_id=party_id,
            expires_at=now + SESSION_LIFETIME,
            last_seen_at=now,
        )
        return session_id

    async def principal_for(self, token: str) -> Principal | None:
        """Resolve a session token, sliding its expiry.

        Args:
            token (str): The cookie value.

        Returns:
            Principal | None: Who is signed in, or None for an unknown, expired or revoked session.
        """
        now = clock.now()
        found = await self.repository.find_live_session(hash_token(token), now)
        if found is None:
            return None
        account = await self.repository.find_account(found.account_id)
        if account is None or account.status != "active":
            return None
        if now - found.last_seen_at >= SESSION_REFRESH:
            await self.repository.update_session(found.id, last_seen_at=now, expires_at=now + SESSION_LIFETIME)
        personal = await personal_party_id(self.session, found.account_id)
        active = found.active_party_id
        capabilities = await capabilities_for(self.session, found.account_id, active)
        if capabilities is None:
            # The membership behind this context ended: fall back to the personal party.
            active = personal
            capabilities = await capabilities_for(self.session, found.account_id, personal)
            await self.repository.update_session(found.id, active_party_id=personal)
        return Principal(
            account_id=found.account_id,
            session_id=found.id,
            personal_party_id=personal,
            active_party_id=active,
            capabilities=capabilities or frozenset(),
        )

    async def set_active_party(self, principal: Principal, party_id: UUID) -> Principal:
        """Act as another party: the personal party or an organization the account belongs to.

        Args:
            principal (Principal): Who is signed in.
            party_id (UUID): The party to act as.

        Returns:
            Principal: The principal in the new context.

        Raises:
            NotFoundError: When the account may not act as that party; nothing about it is revealed (AC05).
        """
        capabilities = await capabilities_for(self.session, principal.account_id, party_id)
        if capabilities is None:
            raise NotFoundError()
        await self.repository.update_session(principal.session_id, active_party_id=party_id)
        return Principal(
            account_id=principal.account_id,
            session_id=principal.session_id,
            personal_party_id=principal.personal_party_id,
            active_party_id=party_id,
            capabilities=capabilities,
        )

    async def sign_out(self, principal: Principal) -> None:
        """Revoke the current session.

        Args:
            principal (Principal): Who is signed in.
        """
        await self.repository.update_session(principal.session_id, revoked_at=clock.now())

    async def lock_account(self, account_id: UUID) -> None:
        """Serialize concurrent requests that are unique to an account."""
        if await self.repository.find_account(account_id, lock=True) is None:
            raise NotFoundError()

    async def lock_active_account(self, account_id: UUID) -> None:
        """Prevent a file write from crossing a concurrent account freeze."""
        account = await self.repository.find_account(account_id, lock=True)
        if account is None or account.status != "active":
            raise UnauthenticatedError()

    async def freeze_for_deletion(self, account_id: UUID, *, remove_sign_in: bool) -> None:
        """Disable sign-in during fulfilment and remove records only when policy permits."""
        account = await self.repository.find_account(account_id, lock=True)
        if account is None:
            raise NotFoundError()
        await self.repository.update_account(account.id, account.version, status="suspended")
        if remove_sign_in:
            await self.repository.remove_sign_in_records(account.id, account.email)

    async def anonymize_for_deletion(self, account_id: UUID) -> str:
        """Remove profile identifiers and return the previous address for one outcome message."""
        account = await self.repository.find_account(account_id, lock=True)
        if account is None:
            raise NotFoundError()
        await self.repository.update_account(
            account.id,
            account.version,
            email=f"deleted-{account.id}@invalid.invalid",
            display_name="Akun dihapus",
            email_verified_at=None,
            locale="id",
            time_zone="Asia/Jakarta",
        )
        return account.email

    async def deletion_address(self, account_id: UUID) -> str:
        """Resolve the destination for a retention-held account's outcome."""
        account = await self.repository.find_account(account_id)
        if account is None:
            raise NotFoundError()
        return account.email

    async def me(self, principal: Principal) -> MeResponse:
        """Describe the signed-in account.

        Args:
            principal (Principal): Who is signed in.

        Returns:
            MeResponse: Account, parties and capabilities.
        """
        account = await self.repository.find_account(principal.account_id)
        assert account is not None  # noqa: S101 - a live session keeps its account (ON DELETE CASCADE)
        return _me(account, principal, await memberships_for(self.session, principal.account_id))

    async def update_me(self, principal: Principal, request: UpdateMeRequest) -> MeResponse:
        """Change account preferences against the version the client saw.

        Args:
            principal (Principal): Who is signed in.
            request (UpdateMeRequest): Changes and ``expected_version``.

        Returns:
            MeResponse: The updated account.

        Raises:
            StaleVersionError: When the account changed since the client read it.
        """
        changes = request.model_dump(exclude_none=True, exclude={"expected_version"})
        account = await self.repository.update_account(principal.account_id, request.expected_version, **changes)
        if account is None:
            current = await self.repository.find_account(principal.account_id)
            raise StaleVersionError(current.version if current else 0)
        return _me(account, principal, await memberships_for(self.session, principal.account_id))


def _me(account: AccountModel, principal: Principal, organizations: list[MembershipResponse]) -> MeResponse:
    return MeResponse(
        account=AccountResponse(
            id=account.id,
            display_name=account.display_name,
            email=account.email,
            email_verified=account.email_verified_at is not None,
            locale=account.locale,
            time_zone=account.time_zone,
            persona=account.persona,
            kind=account.kind,
            version=account.version,
        ),
        personal_party_id=principal.personal_party_id,
        active_party_id=principal.active_party_id,
        capabilities=sorted(principal.capabilities),
        organizations=organizations,
    )
