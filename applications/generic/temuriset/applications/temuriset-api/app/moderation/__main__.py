"""Local administration of account moderation scope and exact case-file grants."""

import argparse
import asyncio
from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clock
from app.core.database import get_engine, get_session_factory
from app.core.errors.base import AppError, NotFoundError, RequestInvalidError
from app.core.errors.public import public_error_for_code
from app.core.errors.recorder import record_failure
from app.core.settings import get_settings
from app.documents.service.service import DocumentService
from app.identity.service.service import IdentityService
from app.moderation.repository.sqlalchemy.models import OperatorFileGrantRecord, OperatorGrantRecord
from app.moderation.repository.sqlalchemy.repository import SqlAlchemyModerationRepository
from app.moderation.service.reports import MODERATION_SCOPE
from app.platform.service.audit import record_audit


def parser() -> argparse.ArgumentParser:
    """Define the local commands with typed identifiers."""
    cli = argparse.ArgumentParser(prog="python -m app.moderation")
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("grant-operator").add_argument("account_id", type=UUID)
    commands.add_parser("revoke-operator").add_argument("grant_id", type=UUID)
    commands.add_parser("revoke-case-file").add_argument("grant_id", type=UUID)
    file_grant = commands.add_parser("grant-case-file")
    file_grant.add_argument("report_id", type=UUID)
    file_grant.add_argument("document_version_id", type=UUID)
    file_grant.add_argument("account_id", type=UUID)
    file_grant.add_argument("--purpose", required=True)
    file_grant.add_argument("--hours", type=int, required=True)
    file_grant.add_argument("--granted-by", required=True)
    return cli


async def change_grant(session: AsyncSession, args: argparse.Namespace) -> UUID:
    """Apply a grant change and append a sanitized administrative audit record."""
    repository = SqlAlchemyModerationRepository(session)
    now = clock.now()
    if args.command == "grant-operator":
        await IdentityService(session, get_settings()).lock_account(args.account_id)
        active = await repository.operator_grant(args.account_id, MODERATION_SCOPE)
        if active is not None:
            return active.id
        row = await repository.add(OperatorGrantRecord(account_id=args.account_id, scope=MODERATION_SCOPE))
        grant_id, action = row.id, "operator.granted"
    elif args.command == "revoke-operator":
        if not await repository.revoke_operator(args.grant_id, now):
            raise NotFoundError()
        grant_id, action = args.grant_id, "operator.revoked"
    elif args.command == "revoke-case-file":
        if not await repository.revoke_file_grant(args.grant_id):
            raise NotFoundError()
        grant_id, action = args.grant_id, "operator.case_file_revoked"
    else:
        if not (0 < len(args.purpose.strip()) <= 4000 and 0 < len(args.granted_by.strip()) <= 254 and args.hours > 0):
            raise RequestInvalidError()
        if await repository.report(args.report_id, lock=True) is None:
            raise NotFoundError()
        if await repository.operator_grant(args.account_id, MODERATION_SCOPE) is None:
            raise NotFoundError()
        await DocumentService(session, get_settings()).require_version(args.document_version_id)
        row = await repository.add(
            OperatorFileGrantRecord(
                report_id=args.report_id,
                document_version_id=args.document_version_id,
                operator_account_id=args.account_id,
                purpose=args.purpose.strip(),
                granted_by=args.granted_by.strip(),
                expires_at=now + timedelta(hours=args.hours),
            )
        )
        grant_id, action = row.id, "operator.case_file_granted"
    await record_audit(session, action=action, subject_type="operator_grant", subject_id=str(grant_id))
    return grant_id


async def main() -> None:
    """Run one authorized local database operation."""
    args = parser().parse_args()
    try:
        async with get_session_factory()() as session, session.begin():
            grant_id = await change_grant(session, args)
        print(grant_id)
    except AppError as error:
        public = public_error_for_code(error.code)
        record_failure(error, operation="moderation.admin", http_status=public.http_status)
        raise SystemExit(f"{public.message} ({error.reference_id})") from None
    finally:
        await get_engine().dispose()


if __name__ == "__main__":
    asyncio.run(main())
