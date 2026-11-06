"""Moderation data access. Writes join the caller's transaction."""

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.moderation.repository.sqlalchemy.models import (
    ListingSuspensionRecord,
    OperatorActionRecord,
    OperatorFileGrantRecord,
    OperatorGrantRecord,
    PrivacyRequestRecord,
    ReportRecord,
    RetentionHoldRecord,
    RetentionPolicyRecord,
)


class SqlAlchemyModerationRepository:
    """Reports, operators, suspensions and privacy requests over one session."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to a session.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def add(self, record: Any) -> Any:
        """Insert a row.

        Args:
            record (Any): An ORM row.

        Returns:
            Any: The row with generated values.
        """
        self.session.add(record)
        await self.session.flush()
        return record

    async def report(self, report_id: UUID, *, lock: bool = False) -> ReportRecord | None:
        """Find a report.

        Args:
            report_id (UUID): The report.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            ReportRecord | None: The report.
        """
        query = select(ReportRecord).where(ReportRecord.id == report_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def reports_of(self, account_id: UUID) -> list[ReportRecord]:
        """List what an account reported.

        Args:
            account_id (UUID): The reporter.

        Returns:
            list[ReportRecord]: Newest first.
        """
        query = select(ReportRecord).where(ReportRecord.reporter_account_id == account_id)
        return list(await self.session.scalars(query.order_by(ReportRecord.created_at.desc())))

    async def report_queue(self, status: str | None, limit: int) -> list[ReportRecord]:
        """List cases for operators.

        Args:
            status (str | None): Only this status.
            limit (int): The most to return.

        Returns:
            list[ReportRecord]: Oldest first, so nothing waits forever.
        """
        query = select(ReportRecord)
        if status is not None:
            query = query.where(ReportRecord.status == status)
        return list(await self.session.scalars(query.order_by(ReportRecord.created_at).limit(limit)))

    async def actions_of(self, report_id: UUID) -> list[OperatorActionRecord]:
        """List what operators did on a case.

        Args:
            report_id (UUID): The report.

        Returns:
            list[OperatorActionRecord]: Oldest first.
        """
        query = select(OperatorActionRecord).where(OperatorActionRecord.report_id == report_id)
        return list(await self.session.scalars(query.order_by(OperatorActionRecord.created_at)))

    async def queue_actions(self, report_ids: list[UUID]) -> dict[UUID, list[OperatorActionRecord]]:
        """Fetch ordered case actions for a whole queue page in one query."""
        rows = await self.session.scalars(
            select(OperatorActionRecord)
            .where(OperatorActionRecord.report_id.in_(report_ids))
            .order_by(OperatorActionRecord.created_at, OperatorActionRecord.id)
        )
        grouped: dict[UUID, list[OperatorActionRecord]] = defaultdict(list)
        for row in rows:
            grouped[row.report_id].append(row)
        return grouped

    async def queue_suspensions(self, targets: list[tuple[str, UUID]]) -> set[tuple[str, UUID]]:
        """Resolve live suspension flags for a whole queue page in one query."""
        if not targets:
            return set()
        rows = await self.session.execute(
            select(ListingSuspensionRecord.subject_type, ListingSuspensionRecord.subject_id).where(
                tuple_(ListingSuspensionRecord.subject_type, ListingSuspensionRecord.subject_id).in_(targets),
                ListingSuspensionRecord.lifted_at.is_(None),
            )
        )
        return {(row.subject_type, row.subject_id) for row in rows}

    async def operator_grant(self, account_id: UUID, scope: str) -> OperatorGrantRecord | None:
        """Find an account's live operator grant.

        Args:
            account_id (UUID): The account.
            scope (str): The scope.

        Returns:
            OperatorGrantRecord | None: The grant.
        """
        return await self.session.scalar(
            select(OperatorGrantRecord).where(
                OperatorGrantRecord.account_id == account_id,
                OperatorGrantRecord.scope == scope,
                OperatorGrantRecord.revoked_at.is_(None),
            )
        )

    async def live_file_grant(
        self, report_id: UUID, version_id: UUID, operator_account_id: UUID, now: datetime
    ) -> OperatorFileGrantRecord | None:
        """Find the grant that lets one operator open one file version on one case now.

        Args:
            report_id (UUID): The case.
            version_id (UUID): The document version.
            operator_account_id (UUID): The operator.
            now (datetime): Product time.

        Returns:
            OperatorFileGrantRecord | None: The grant.
        """
        return await self.session.scalar(
            select(OperatorFileGrantRecord)
            .where(
                OperatorFileGrantRecord.report_id == report_id,
                OperatorFileGrantRecord.document_version_id == version_id,
                OperatorFileGrantRecord.operator_account_id == operator_account_id,
                OperatorFileGrantRecord.expires_at > now,
            )
            .limit(1)
        )

    async def active_suspension(self, subject_type: str, subject_id: UUID) -> ListingSuspensionRecord | None:
        """Find a listing's live suspension.

        Args:
            subject_type (str): The listing type.
            subject_id (UUID): The listing.

        Returns:
            ListingSuspensionRecord | None: The suspension.
        """
        return await self.session.scalar(
            select(ListingSuspensionRecord).where(
                ListingSuspensionRecord.subject_type == subject_type,
                ListingSuspensionRecord.subject_id == subject_id,
                ListingSuspensionRecord.lifted_at.is_(None),
            )
        )

    async def suspended_among(self, subject_type: str, subject_ids: list[UUID]) -> set[UUID]:
        """Say which of several listings are suspended, in one query.

        Args:
            subject_type (str): The listing type.
            subject_ids (list[UUID]): The listings.

        Returns:
            set[UUID]: Those suspended now.
        """
        rows = await self.session.scalars(
            select(ListingSuspensionRecord.subject_id).where(
                ListingSuspensionRecord.subject_type == subject_type,
                ListingSuspensionRecord.subject_id.in_(subject_ids),
                ListingSuspensionRecord.lifted_at.is_(None),
            )
        )
        return set(rows)

    async def policies(self) -> list[RetentionPolicyRecord]:
        """Read the retention policy.

        Returns:
            list[RetentionPolicyRecord]: Every category, in order.
        """
        query = select(RetentionPolicyRecord).order_by(RetentionPolicyRecord.position)
        return list(await self.session.scalars(query))

    async def privacy_request(self, request_id: UUID, *, lock: bool = False) -> PrivacyRequestRecord | None:
        """Find a privacy request.

        Args:
            request_id (UUID): The request.
            lock (bool, optional): Lock it for this transaction. Defaults to False.

        Returns:
            PrivacyRequestRecord | None: The request.
        """
        query = select(PrivacyRequestRecord).where(PrivacyRequestRecord.id == request_id)
        return await self.session.scalar(query.with_for_update() if lock else query)

    async def privacy_requests_of(self, account_id: UUID) -> list[PrivacyRequestRecord]:
        """List an account's privacy requests.

        Args:
            account_id (UUID): The account.

        Returns:
            list[PrivacyRequestRecord]: Newest first.
        """
        query = select(PrivacyRequestRecord).where(PrivacyRequestRecord.account_id == account_id)
        return list(await self.session.scalars(query.order_by(PrivacyRequestRecord.created_at.desc())))

    async def open_deletion(self, account_id: UUID) -> PrivacyRequestRecord | None:
        """Find an account's deletion request still waiting for an operator.

        Args:
            account_id (UUID): The account.

        Returns:
            PrivacyRequestRecord | None: The request.
        """
        return await self.session.scalar(
            select(PrivacyRequestRecord).where(
                PrivacyRequestRecord.account_id == account_id,
                PrivacyRequestRecord.kind == "DELETION",
                PrivacyRequestRecord.status.in_(("RECEIVED", "PROCESSING")),
            )
        )

    async def open_deletions(self, limit: int) -> list[PrivacyRequestRecord]:
        """List deletion requests waiting for an operator.

        Args:
            limit (int): The most to return.

        Returns:
            list[PrivacyRequestRecord]: Oldest first.
        """
        query = select(PrivacyRequestRecord).where(
            PrivacyRequestRecord.kind == "DELETION", PrivacyRequestRecord.status == "RECEIVED"
        )
        return list(await self.session.scalars(query.order_by(PrivacyRequestRecord.created_at).limit(limit)))

    async def revoke_operator(self, grant_id: UUID, now: datetime) -> bool:
        """Withdraw one active scope grant."""
        grant = await self.session.get(OperatorGrantRecord, grant_id, with_for_update=True)
        if grant is None or grant.revoked_at is not None:
            return False
        grant.revoked_at = now
        return True

    async def revoke_file_grant(self, grant_id: UUID) -> bool:
        """Remove one case-file authorization while its audit history stays intact."""
        grant = await self.session.get(OperatorFileGrantRecord, grant_id, with_for_update=True)
        if grant is None:
            return False
        await self.session.delete(grant)
        return True

    async def active_holds(self, account_id: UUID) -> list[RetentionHoldRecord]:
        """Read the current unreleased holds, oldest first."""
        query = select(RetentionHoldRecord).where(
            RetentionHoldRecord.account_id == account_id, RetentionHoldRecord.released_at.is_(None)
        )
        return list(await self.session.scalars(query.order_by(RetentionHoldRecord.created_at)))
