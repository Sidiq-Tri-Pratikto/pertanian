"""Private request receipts, policy-generated retention answers and fresh account exports."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context, require_account
from app.core import clock
from app.core.errors.base import ConflictError, InvalidTransitionError, NotFoundError
from app.core.settings import get_settings
from app.documents.service.service import DocumentService
from app.identity.model.models import Principal
from app.identity.service.mailbox_service import DisabledMailbox, mailbox_for
from app.identity.service.service import IdentityService
from app.moderation.model.schema import (
    CreatePrivacyRequest,
    FulfillPrivacyRequest,
    PrivacyAnswer,
    PrivacyExportResponse,
    PrivacyRequestResponse,
)
from app.moderation.repository.sqlalchemy.models import PrivacyRequestRecord
from app.moderation.repository.sqlalchemy.repository import SqlAlchemyModerationRepository
from app.moderation.service.reports import ReportService
from app.moderation.service.retention import complete_deletion, deletion_answer, prepare_deletion
from app.platform.service.audit import record_audit
from app.platform.service.outbox import enqueue_job, publish
from app.platform.service.versions import check_expected


def privacy_view(row: PrivacyRequestRecord, operation_id: UUID | None = None) -> PrivacyRequestResponse:
    """Return the current receipt, leaving internal fulfilment data out of the wire response."""
    result = PrivacyRequestResponse.model_validate(row, from_attributes=True)
    return result.model_copy(update={"operation_id": operation_id})


class PrivacyService:
    """Keep privacy requests and exports scoped to the requesting account."""

    def __init__(self, session: AsyncSession) -> None:
        """Join the caller's transaction."""
        self.session = session
        self.repository = SqlAlchemyModerationRepository(session)
        self.identity = IdentityService(session, get_settings())

    async def create(
        self, principal: Principal, body: CreatePrivacyRequest, operation_id: UUID
    ) -> PrivacyRequestResponse:
        """Open a deletion case or a ready-to-read export receipt."""
        check_context(principal, body.acting_party_id)
        if body.kind == "DELETION":
            await self.identity.lock_account(principal.account_id)
            if await self.repository.open_deletion(principal.account_id):
                raise ConflictError("Permintaan penghapusan masih diproses. Lihat status permintaan sebelumnya.")
            answer, policy_version = await deletion_answer(self.session, principal.account_id)
            status, fulfilled_at = "RECEIVED", None
        else:
            answer = PrivacyAnswer(
                to_remove=[], removed=[], retained=[], notice="Ekspor memuat data yang dapat Anda akses saat diunduh."
            )
            policy_version, status, fulfilled_at = None, "FULFILLED", clock.now()
        row = await self.repository.add(
            PrivacyRequestRecord(
                account_id=principal.account_id,
                kind=body.kind,
                status=status,
                answer=answer.model_dump(mode="json"),
                policy_version=policy_version,
                fulfilled_at=fulfilled_at,
            )
        )
        await record_audit(
            self.session,
            action="privacy.requested",
            subject_type="privacy_request",
            subject_id=str(row.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
            detail={"kind": body.kind},
        )
        return privacy_view(row, operation_id)

    async def _owned(self, principal: Principal, request_id: UUID) -> PrivacyRequestRecord:
        row = await self.repository.privacy_request(request_id)
        if row is None:
            raise NotFoundError()
        require_account(principal, row.account_id)
        return row

    async def read(self, principal: Principal, request_id: UUID) -> PrivacyRequestResponse:
        """Read one request owned by the current account."""
        return privacy_view(await self._owned(principal, request_id))

    async def list_mine(self, principal: Principal) -> list[PrivacyRequestResponse]:
        """Read the current account's privacy request statuses."""
        return [privacy_view(row) for row in await self.repository.privacy_requests_of(principal.account_id)]

    async def export(self, principal: Principal, request_id: UUID) -> PrivacyExportResponse:
        """Build an allowlisted export from live permissions on each request."""
        row = await self._owned(principal, request_id)
        if row.kind != "EXPORT" or row.status != "FULFILLED":
            raise NotFoundError()
        me = await self.identity.me(principal)
        return PrivacyExportResponse(
            generated_at=clock.now(),
            account=me.account,
            memberships=me.organizations,
            personal_party_id=me.personal_party_id,
            documents=await DocumentService(self.session, get_settings()).export_personal_metadata(principal),
            reports=await ReportService(self.session).list_mine(principal),
            privacy_requests=await self.list_mine(principal),
        )

    async def operator_queue(self, principal: Principal, limit: int) -> list[PrivacyRequestResponse]:
        """List unfulfilled deletion cases to a scoped operator."""
        await ReportService(self.session).authorize_operator(principal)
        return [privacy_view(row) for row in await self.repository.open_deletions(limit)]

    async def fulfill(
        self, principal: Principal, request_id: UUID, body: FulfillPrivacyRequest, operation_id: UUID
    ) -> PrivacyRequestResponse:
        """Apply the current retention policy once and enqueue verifiable completion."""
        await ReportService(self.session).authorize_operator(principal)
        check_context(principal, body.acting_party_id)
        row = await self.repository.privacy_request(request_id, lock=True)
        if row is None:
            raise NotFoundError()
        check_expected(row.version, body.expected_version)
        if row.kind != "DELETION" or row.status != "RECEIVED":
            raise InvalidTransitionError()

        await self.identity.lock_account(row.account_id)
        answer, row.policy_version = await deletion_answer(self.session, row.account_id)
        await prepare_deletion(self.session, row.account_id, answer)
        row.answer = answer.model_dump(mode="json")
        row.status = "PROCESSING"
        row.version += 1
        row.fulfilled_by_account_id = principal.account_id
        await record_audit(
            self.session,
            action="privacy.fulfilment_started",
            subject_type="privacy_request",
            subject_id=str(row.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
            detail={"policy_version": row.policy_version},
        )
        await enqueue_job(self.session, "documents.erase", {"privacy_request_id": str(row.id)})
        await self.session.flush()
        return privacy_view(row, operation_id)

    async def finish(self, request_id: UUID) -> None:
        """Finalize only after the retryable physical removals have succeeded."""
        row = await self.repository.privacy_request(request_id, lock=True)
        if row is None or row.status != "PROCESSING":
            return
        answer = PrivacyAnswer.model_validate(row.answer)
        address = await complete_deletion(self.session, row.account_id, answer)
        answer.removed = answer.to_remove
        answer.to_remove = []
        row.answer = answer.model_dump(mode="json")
        row.status = "FULFILLED"
        row.version += 1
        row.fulfilled_at = clock.now()
        await record_audit(
            self.session,
            action="privacy.fulfilled",
            subject_type="privacy_request",
            subject_id=str(row.id),
            actor_account_id=row.fulfilled_by_account_id,
            detail={"policy_version": row.policy_version},
        )
        await publish(self.session, "privacy.outcome_ready", {"privacy_request_id": str(row.id)})
        mailbox = mailbox_for(get_settings())
        if isinstance(mailbox, DisabledMailbox):
            await record_audit(
                self.session,
                action="privacy.notification_unavailable",
                subject_type="privacy_request",
                subject_id=str(row.id),
            )
        else:
            sections = ["Permintaan penghapusan selesai.", "Dihapus:"]
            sections.extend(f"- {item.label}" for item in answer.removed)
            sections.append("Tetap disimpan:")
            sections.extend(f"- {item.label}. {item.reason} ({item.period})" for item in answer.retained)
            sections.append(answer.notice)
            await mailbox.send(
                self.session, to_email=address, subject="Hasil permintaan penghapusan", body="\n".join(sections)
            )
