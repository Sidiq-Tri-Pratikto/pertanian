"""Provision and revoke lab access from the operator's private shell."""

import argparse
import asyncio
import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import wall_now
from app.core.database import get_engine, get_session_factory
from app.core.errors.base import AppError, ConflictError, NotFoundError
from app.core.errors.database import resolve_database_error
from app.core.errors.public import public_error_for_code
from app.core.errors.recorder import record_failure
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.identity.model.models import PrincipalKind
from app.identity.repository.sqlalchemy.repository import SqlAlchemyPrincipalRepository
from app.identity.service.service import PrincipalService
from app.meter_pilot.dependencies import ACCESS_PREFIX, access_digest, require_pilot
from app.meter_pilot.repository.sqlalchemy.models import MeterAssignmentRecord
from app.meter_pilot.repository.sqlalchemy.repository import SqlAlchemyPilotRepository
from app.sites.dependencies import get_site_service
from app.sites.model.models import SiteKind

ACCESS_TTL = timedelta(hours=8)


async def provision(session: AsyncSession, name: str, meter_id: UUID) -> tuple[UUID, str]:
    """Create one standard site and one short-lived access grant for the assigned meter."""
    require_pilot()
    owner = await PrincipalService(SqlAlchemyPrincipalRepository(session)).create(PrincipalKind.USER)
    site = await get_site_service(session).create(owner, kind=SiteKind.STANDARD, name=name)
    code = ACCESS_PREFIX + secrets.token_urlsafe(32)
    session.add(
        MeterAssignmentRecord(
            meter_id=meter_id,
            site_id=site.id,
            owner_id=owner.id,
            access_digest=access_digest(code),
            access_expires_at=wall_now() + ACCESS_TTL,
        )
    )
    try:
        await session.flush()
    except IntegrityError:
        raise ConflictError() from None
    return site.id, code


async def _operate(args: argparse.Namespace) -> None:
    require_pilot()
    result = None
    async with get_session_factory().begin() as session:
        repo = SqlAlchemyPilotRepository(session)
        if args.action == "provision":
            result = await provision(session, args.site_name, args.meter_id)
        elif args.action in ("renew-access", "revoke-access"):
            await get_site_service(session).lock(args.site_id)
            assignment = await repo.assigned_to_site(args.site_id)
            if assignment is None:
                raise NotFoundError()
            if args.action == "renew-access":
                code = ACCESS_PREFIX + secrets.token_urlsafe(32)
                await repo.update_assignment(
                    assignment.meter_id, access_digest=access_digest(code), access_expires_at=wall_now() + ACCESS_TTL
                )
                result = (args.site_id, code)
            else:
                await repo.update_assignment(assignment.meter_id, access_digest=None)
        else:
            assignment = await repo.assigned_meter(args.meter_id)
            if assignment is None:
                raise NotFoundError()
            await get_site_service(session).lock(assignment.site_id)
            await repo.update_assignment(assignment.meter_id, meter_revoked_at=wall_now())
    if result:
        # This is a one-time handoff to the operator's private shell, after the commit.
        print(f"Site: {result[0]}\nPilot access code (expires in 8 hours): {result[1]}")
    else:
        print("Revocation saved.")


async def _run(args: argparse.Namespace) -> None:
    try:
        await _operate(args)
    finally:
        await get_engine().dispose()


def main() -> None:
    """Run a provisioning command from an isolated lab environment."""
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    create = actions.add_parser("provision")
    create.add_argument("--site-name", required=True)
    create.add_argument("--meter-id", required=True, type=UUID)
    actions.add_parser("renew-access").add_argument("--site-id", required=True, type=UUID)
    actions.add_parser("revoke-access").add_argument("--site-id", required=True, type=UUID)
    actions.add_parser("revoke-meter").add_argument("--meter-id", required=True, type=UUID)
    args = parser.parse_args()
    if args.action == "provision":
        args.site_name = args.site_name.strip()
        if not 1 <= len(args.site_name) <= 60:
            parser.error("Site name must be 1 to 60 characters.")
    setup_logging(get_settings().log_level)
    try:
        asyncio.run(_run(args))
    except (AppError, SQLAlchemyError, OSError) as raw:
        error = resolve_database_error(raw) if isinstance(raw, SQLAlchemyError) else raw
        if not isinstance(error, AppError):
            error = AppError(error=error)
        public = public_error_for_code(error.code)
        record_failure(error, operation="meter_pilot.operator", http_status=public.http_status)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
