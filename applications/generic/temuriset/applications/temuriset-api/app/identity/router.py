"""Sign-in with emailed codes, sign-out, and the signed-in account."""

from fastapi import APIRouter, Request, Response, status

from app.core.database import SessionDep
from app.core.security import SESSION_COOKIE, PrincipalDep
from app.core.settings import get_settings
from app.identity.model.schema import CodeRequest, CodeSentResponse, MeResponse, UpdateMeRequest, VerifyRequest
from app.identity.service.service import SESSION_LIFETIME, IdentityService

auth_router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(prefix="/me", tags=["account"])


def _client_address(request: Request) -> str:
    # ponytail: trusts the first X-Forwarded-For hop, which the web app's proxy sets; a direct caller can spoof it,
    # so the per-email limit is the one that always holds. Pin trusted proxies when deployment (037) fixes them.
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")


@auth_router.post("/code", status_code=status.HTTP_202_ACCEPTED, summary="Email a sign-in code")
async def request_code(body: CodeRequest, request: Request, session: SessionDep) -> CodeSentResponse:
    """Email a six-digit code. The answer is the same whether or not the email has an account.

    Args:
        body (CodeRequest): Email, purpose and, for sign-up, the profile.
        request (Request): The request.
        session (SessionDep): Database session.

    Returns:
        CodeSentResponse: Always ``{"sent": true}``.
    """
    await IdentityService(session, get_settings()).request_code(body, _client_address(request))
    return CodeSentResponse()


@auth_router.post("/verify", summary="Verify a code and sign in")
async def verify(body: VerifyRequest, response: Response, session: SessionDep) -> MeResponse:
    """Check the code, start a session cookie and return the account.

    Args:
        body (VerifyRequest): Email and code.
        response (Response): Carries the session cookie.
        session (SessionDep): Database session.

    Returns:
        MeResponse: The signed-in account.
    """
    settings = get_settings()
    service = IdentityService(session, settings)
    token, principal = await service.verify(body)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return await service.me(principal)


@auth_router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT, summary="Sign out")
async def sign_out(principal: PrincipalDep, response: Response, session: SessionDep) -> None:
    """Revoke this session and clear its cookie.

    Args:
        principal (PrincipalDep): Who is signed in.
        response (Response): Clears the cookie.
        session (SessionDep): Database session.
    """
    await IdentityService(session, get_settings()).sign_out(principal)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax")


@me_router.get("", summary="Read the signed-in account")
async def get_me(principal: PrincipalDep, session: SessionDep) -> MeResponse:
    """Return the signed-in account and the party it acts as.

    Args:
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        MeResponse: The account.
    """
    return await IdentityService(session, get_settings()).me(principal)


@me_router.patch("", summary="Change account preferences")
async def update_me(body: UpdateMeRequest, principal: PrincipalDep, session: SessionDep) -> MeResponse:
    """Change profile or notification preferences against ``expected_version``.

    Args:
        body (UpdateMeRequest): Changes.
        principal (PrincipalDep): Who is signed in.
        session (SessionDep): Database session.

    Returns:
        MeResponse: The updated account.
    """
    return await IdentityService(session, get_settings()).update_me(principal, body)
