"""Private reporting and scope-limited operator case handling."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context, require_account, require_operator_scope
from app.core import clock
from app.core.errors import codes
from app.core.errors.base import AppError, NotFoundError
from app.identity.model.models import Principal
from app.intake.service.service import lock_moderation_target as lock_intake_target
from app.moderation.model.schema import (
    CreateReportRequest,
    OperatorActionRequest,
    OperatorActionResponse,
    OperatorReportResponse,
    ReportResponse,
)
from app.moderation.repository.sqlalchemy.models import ListingSuspensionRecord, OperatorActionRecord, ReportRecord
from app.moderation.repository.sqlalchemy.repository import SqlAlchemyModerationRepository
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import check_expected
from app.portfolio.service.service import lock_moderation_target as lock_invention_target

MODERATION_SCOPE = "moderation"
_TRANSITIONS = {
    "START_REVIEW": {"RECEIVED": "IN_REVIEW"},
    "RESOLVE": {"IN_REVIEW": "RESOLVED"},
    "DISMISS": {"RECEIVED": "DISMISSED", "IN_REVIEW": "DISMISSED"},
}


class InvalidReportTransitionError(AppError):
    """The case cannot accept this action in its current state."""

    code = codes.APP_INVALID_TRANSITION


def reporter_view(report: ReportRecord, operation_id: UUID | None = None) -> ReportResponse:
    """Expose the case identifier and its status to the reporter."""
    return ReportResponse.model_validate(
        {
            "id": report.id,
            "case_number": f"TR-{report.case_number:06d}",
            "status": report.status,
            "operation_id": operation_id,
        }
    )


class ReportService:
    """Keep private reports accessible to their reporter and authorized operators."""

    def __init__(self, session: AsyncSession) -> None:
        """Join the caller's transaction."""
        self.session = session
        self.repository = SqlAlchemyModerationRepository(session)

    async def authorize_operator(self, principal: Principal) -> None:
        """Require a current moderation grant before reading cases or replaying mutations."""
        grant = await self.repository.operator_grant(principal.account_id, MODERATION_SCOPE)
        require_operator_scope(granted=grant is not None)

    async def create(self, principal: Principal, body: CreateReportRequest, operation_id: UUID) -> ReportResponse:
        """Accept a report without probing for the reported object."""
        check_context(principal, body.acting_party_id)
        report = await self.repository.add(
            ReportRecord(
                reporter_account_id=principal.account_id,
                reporter_party_id=principal.active_party_id,
                category=body.category,
                subject_type=body.subject_type,
                subject_id=body.subject_id,
                subject_label=body.subject_label,
                reason=body.reason,
            )
        )
        await self._audit(principal, report.id, "report.received")
        return reporter_view(report, operation_id)

    async def read(self, principal: Principal, report_id: UUID) -> ReportResponse:
        """Return one case's public-to-reporter fields to its owner."""
        report = await self._find(report_id)
        require_account(principal, report.reporter_account_id)
        return reporter_view(report)

    async def list_mine(self, principal: Principal) -> list[ReportResponse]:
        """List only the requesting account's cases."""
        return [reporter_view(row) for row in await self.repository.reports_of(principal.account_id)]

    async def queue(self, principal: Principal, status: str | None, limit: int) -> list[OperatorReportResponse]:
        """Read the scoped case queue, oldest first."""
        await self.authorize_operator(principal)
        rows = await self.repository.report_queue(status, limit)
        if not rows:
            return []
        actions = await self.repository.queue_actions([row.id for row in rows])
        suspended = await self.repository.queue_suspensions(
            [(row.subject_type, row.subject_id) for row in rows if row.subject_id is not None]
        )
        return [
            self._operator_view(row, actions.get(row.id, []), (row.subject_type, row.subject_id) in suspended)
            for row in rows
        ]

    async def act(
        self, principal: Principal, report_id: UUID, body: OperatorActionRequest, operation_id: UUID
    ) -> OperatorReportResponse:
        """Apply one scoped case transition and record its private note and sanitized audit."""
        await self.authorize_operator(principal)
        check_context(principal, body.acting_party_id)
        report = await self._find(report_id, lock=True)
        check_expected(report.version, body.expected_version)
        if body.action in {"SUSPEND_LISTING", "LIFT_SUSPENSION"}:
            status = await self._set_suspension(report, principal, suspend=body.action == "SUSPEND_LISTING")
        else:
            status = _TRANSITIONS.get(body.action, {}).get(report.status)
        if status is None:
            raise InvalidReportTransitionError()
        report.status = status
        report.version += 1
        await self.repository.add(
            OperatorActionRecord(
                report_id=report.id, operator_account_id=principal.account_id, action=body.action, note=body.note
            )
        )
        await self._audit(principal, report.id, f"report.{body.action.lower()}")
        actions = await self.repository.actions_of(report.id)
        suspension = (
            await self.repository.active_suspension(report.subject_type, report.subject_id)
            if report.subject_id is not None
            else None
        )
        return self._operator_view(report, actions, suspension is not None, operation_id)

    async def _set_suspension(self, report: ReportRecord, principal: Principal, *, suspend: bool) -> str:
        subject_id = report.subject_id
        if subject_id is None or report.subject_type not in {"INVENTION", "PARTNER_PROFILE", "OPPORTUNITY"}:
            raise InvalidReportTransitionError()
        if suspend and report.status not in {"RECEIVED", "IN_REVIEW"}:
            raise InvalidReportTransitionError()
        if report.subject_type == "INVENTION":
            await lock_invention_target(self.session, subject_id)
        else:
            await lock_intake_target(self.session, report.subject_type, subject_id)
        active = await self.repository.active_suspension(report.subject_type, subject_id)
        if suspend:
            if active is not None:
                raise InvalidReportTransitionError()
            await self.repository.add(
                ListingSuspensionRecord(
                    report_id=report.id,
                    subject_type=report.subject_type,
                    subject_id=subject_id,
                    suspended_by_account_id=principal.account_id,
                )
            )
        else:
            if active is None or active.report_id != report.id:
                raise InvalidReportTransitionError()
            active.lifted_at = clock.now()
        topic = "listing.suspended" if suspend else "listing.restored"
        await publish(self.session, topic, {"subject_type": report.subject_type, "subject_id": str(subject_id)})
        return "IN_REVIEW" if suspend else report.status

    async def require_case(self, principal: Principal, report_id: UUID) -> None:
        """Require a scoped operator and an existing case before a file authorization check."""
        await self.authorize_operator(principal)
        await self._find(report_id)

    async def file_grant(self, principal: Principal, report_id: UUID, version_id: UUID) -> UUID | None:
        """Resolve a grant for this operator, case and exact document version."""
        grant = await self.repository.live_file_grant(report_id, version_id, principal.account_id, clock.now())
        return grant.id if grant else None

    async def _find(self, report_id: UUID, *, lock: bool = False) -> ReportRecord:
        report = await self.repository.report(report_id, lock=lock)
        if report is None:
            raise NotFoundError()
        return report

    async def _audit(self, principal: Principal, report_id: UUID, action: str) -> None:
        await record_audit(
            self.session,
            action=action,
            subject_type="report",
            subject_id=str(report_id),
            actor_party_id=principal.active_party_id,
            actor_account_id=principal.account_id,
        )

    @staticmethod
    def _operator_view(
        row: ReportRecord, actions: list[OperatorActionRecord], suspended: bool, operation_id: UUID | None = None
    ) -> OperatorReportResponse:
        return OperatorReportResponse.model_validate(
            {
                "id": row.id,
                "case_number": f"TR-{row.case_number:06d}",
                "version": row.version,
                "category": row.category,
                "subject_type": row.subject_type,
                "subject_id": row.subject_id,
                "subject_label": row.subject_label,
                "reason": row.reason,
                "status": row.status,
                "reporter_party_id": row.reporter_party_id,
                "suspended": suspended,
                "actions": [OperatorActionResponse.model_validate(item, from_attributes=True) for item in actions],
                "created_at": row.created_at,
                "operation_id": operation_id,
            }
        )
