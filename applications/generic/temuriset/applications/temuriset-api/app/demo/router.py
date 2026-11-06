"""Labelled demo: list accounts, sign in from the picker, reset. Every route is absent unless demo mode is on."""

from fastapi import APIRouter, Depends, Response

from app.core.database import SessionDep
from app.core.errors.base import NotFoundError
from app.core.security import SESSION_COOKIE
from app.core.settings import get_settings
from app.demo.model.schema import DemoAccount, DemoResetRequest, DemoResetResponse, DemoSignInRequest
from app.demo.service.fixtures import Variants, demo_accounts, demo_email, reset
from app.identity.model.schema import MeResponse
from app.identity.service.service import SESSION_LIFETIME, IdentityService, start_demo_session


async def _demo_mode() -> None:
    if not get_settings().demo_mode:
        raise NotFoundError()


router = APIRouter(prefix="/demo", tags=["demo"], dependencies=[Depends(_demo_mode)])


@router.get("/accounts", summary="List demo accounts")
async def list_demo_accounts() -> list[DemoAccount]:
    """List the labelled demo accounts.

    Returns:
        list[DemoAccount]: Accounts, each labelled "Akun demo · data fiktif".
    """
    return [DemoAccount.model_validate(account) for account in demo_accounts()]


@router.post("/sign-in", summary="Sign in as a demo account")
async def demo_sign_in(body: DemoSignInRequest, response: Response, session: SessionDep) -> MeResponse:
    """Start a session for a demo account. Demo accounts have no code by email; this picker is their only way in.

    Args:
        body (DemoSignInRequest): The account key.
        response (Response): Carries the session cookie.
        session (SessionDep): Database session.

    Returns:
        MeResponse: The signed-in demo account.
    """
    settings = get_settings()
    known = {account["key"] for account in demo_accounts()}
    if body.key not in known:
        raise NotFoundError()
    token, principal = await start_demo_session(session, settings, demo_email(body.key))
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return await IdentityService(session, settings).me(principal)


@router.post("/reset", summary="Reset the demo")
async def reset_demo(body: DemoResetRequest, session: SessionDep) -> DemoResetResponse:
    """Delete only demo rows and recreate them with the same ids; real accounts are untouched.

    Args:
        body (DemoResetRequest): Fixture states.
        session (SessionDep): Database session.

    Returns:
        DemoResetResponse: What was recreated.
    """
    subjects = await reset(session, get_settings(), Variants(**body.model_dump()))
    return DemoResetResponse(accounts=len(demo_accounts()), inventions=len(subjects) - 1)
