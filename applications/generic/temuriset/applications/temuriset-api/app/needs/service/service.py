"""Support requests: one outcome each, a versioned budget, and an honest status."""

from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.core.errors.base import FieldsInvalidError, InvalidTransitionError, NotFoundError
from app.identity.model.models import Principal
from app.needs.model.schema import (
    CreateSupportRequest,
    SupportRequestInput,
    SupportRequestResponse,
    TransitionRequest,
    UpdateSupportRequest,
)
from app.needs.repository.sqlalchemy.models import SupportRequestRecord
from app.needs.repository.sqlalchemy.repository import SqlAlchemyNeedsRepository
from app.needs.service.budget import budget_response, validate_budget
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import check_expected
from app.portfolio.service.service import invention_reference, owned_submittable_version

# Allowed status changes; EXPIRED is set by the deadline, never by a person.
TRANSITIONS = {
    "activate": ({"DRAFT", "PAUSED"}, "ACTIVE"),
    "pause": ({"ACTIVE"}, "PAUSED"),
    "close": ({"DRAFT", "ACTIVE", "PAUSED"}, "CLOSED"),
}
_CONTENT = (
    "outcome",
    "support_forms",
    "relationship_form",
    "scope",
    "months",
    "region",
    "accepts_partial",
    "accepts_noncash",
    "noncash_description",
)


class NeedsService:
    """Support requests of the acting party."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyNeedsRepository(session)

    async def _owned(self, principal: Principal, request_id: UUID, *, lock: bool = False) -> SupportRequestRecord:
        record = await self.repository.find(request_id, lock=lock)
        if record is None or record.owner_party_id != principal.active_party_id:
            raise NotFoundError()
        return record

    async def view(self, record: SupportRequestRecord, operation_id: UUID | None = None) -> SupportRequestResponse:
        """Render a request with the budget of its current version.

        Args:
            record (SupportRequestRecord): The request.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            SupportRequestResponse: The request.
        """
        budget, lines = await self.repository.budget(record.id, record.version)
        reference = await invention_reference(self.session, record.invention_version_id)
        return SupportRequestResponse(
            id=record.id,
            version=record.version,
            invention_id=record.invention_id,
            invention_version=reference.number,
            invention_title=reference.title,
            status=record.status,
            budget=budget_response(budget, lines) if budget else None,
            operation_id=operation_id,
            **{field: getattr(record, field) for field in _CONTENT},
        )

    async def _carry_budget(self, request_id: UUID, from_version: int, to_version: int) -> None:
        """Copy a version's budget to the next version when the change did not touch it."""
        budget, lines = await self.repository.budget(request_id, from_version)
        if budget is None:
            return
        columns = ("min_amount", "max_amount", "currency", "basis", "period", "scope", "estimated_on", "assumptions")
        columns += ("unknown_reason", "financial", "lines_explanation")
        await self.repository.write_budget(
            request_id,
            to_version,
            {column: getattr(budget, column) for column in columns},
            [
                {
                    "position": line.position,
                    "label": line.label,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "explanation": line.explanation,
                }
                for line in lines
            ],
        )

    async def _write(self, record: SupportRequestRecord, request: SupportRequestInput) -> None:
        if request.budget is not None:
            errors, values, lines = validate_budget(request.budget)
            if errors:
                raise FieldsInvalidError(errors)
        for field in _CONTENT:
            setattr(record, field, getattr(request, field))
        await self.session.flush()
        if request.budget is not None:
            await self.repository.write_budget(record.id, record.version, values, lines)
        await self.repository.snapshot(record.id, record.version, jsonable_encoder(await self.view(record)))
        await publish(
            self.session, "support_request.changed", {"support_request_id": str(record.id), "version": record.version}
        )

    async def create(self, principal: Principal, request: CreateSupportRequest) -> SupportRequestResponse:
        """Start a request for a published invention the acting party manages.

        Args:
            principal (Principal): Who is signed in.
            request (CreateSupportRequest): Invention and content.

        Returns:
            SupportRequestResponse: The draft request.

        Raises:
            FieldsInvalidError: When the budget breaks a rule; nothing is stored.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, principal.active_party_id)
        version_id = await owned_submittable_version(self.session, request.invention_id, principal.active_party_id)
        record = await self.repository.add(
            SupportRequestRecord(
                invention_id=request.invention_id,
                owner_party_id=principal.active_party_id,
                invention_version_id=version_id,
            )
        )
        await self._write(record, request)
        return await self.view(record)

    async def list_mine(self, principal: Principal, invention_id: UUID | None) -> list[SupportRequestResponse]:
        """List the acting party's requests.

        Args:
            principal (Principal): Who is signed in.
            invention_id (UUID | None): Only this invention's.

        Returns:
            list[SupportRequestResponse]: Requests.
        """
        return [
            await self.view(record)
            for record in await self.repository.of_party(principal.active_party_id, invention_id)
        ]

    async def read(self, principal: Principal, request_id: UUID) -> SupportRequestResponse:
        """Read one request as its owner.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.

        Returns:
            SupportRequestResponse: The request.
        """
        return await self.view(await self._owned(principal, request_id))

    async def source(self, principal: Principal, request_id: UUID) -> tuple[SupportRequestResponse, UUID]:
        """Read an owned request for matching, with the invention version it references (019).

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.

        Returns:
            tuple[SupportRequestResponse, UUID]: The request and its invention version.

        Raises:
            NotFoundError: When the acting party does not own it.
        """
        record = await self._owned(principal, request_id)
        return await self.view(record), record.invention_version_id

    async def version(self, principal: Principal, request_id: UUID, number: int) -> dict:
        """Read the request as it stood at an earlier version, for submissions that reference it.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.
            number (int): The version.

        Returns:
            dict: The snapshot.
        """
        await self._owned(principal, request_id)
        snapshot = await self.repository.version_snapshot(request_id, number)
        if snapshot is None:
            raise NotFoundError()
        return snapshot

    async def update(
        self, principal: Principal, request_id: UUID, request: UpdateSupportRequest, operation_id: UUID | None = None
    ) -> SupportRequestResponse:
        """Replace the content as a new version; the previous version stays readable.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.
            request (UpdateSupportRequest): Content and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            SupportRequestResponse: The new version.

        Raises:
            FieldsInvalidError: When the budget breaks a rule; the request keeps its previous values (AC16).
        """
        check_context(principal, request.acting_party_id)
        record = await self._owned(principal, request_id, lock=True)
        require(principal, Capability.EDIT_PORTFOLIO, record.owner_party_id)
        if record.status in {"CLOSED", "EXPIRED"}:
            raise InvalidTransitionError()
        check_expected(record.version, request.expected_version)
        if request.budget is not None:
            errors, _, _ = validate_budget(request.budget)
            if errors:
                raise FieldsInvalidError(errors)
        record.version += 1
        if request.budget is None:
            await self._carry_budget(record.id, record.version - 1, record.version)
        await self._write(record, request)
        return await self.view(record, operation_id)

    async def transition(
        self,
        principal: Principal,
        request_id: UUID,
        action: str,
        request: TransitionRequest,
        operation_id: UUID | None = None,
    ) -> SupportRequestResponse:
        """Activate, pause or close. Activation needs an outcome and at least one support form.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.
            action (str): ``activate``, ``pause`` or ``close``.
            request (TransitionRequest): Acting party and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            SupportRequestResponse: The request in its new status.

        Raises:
            InvalidTransitionError: From a status that does not allow it.
            FieldsInvalidError: When activating without an outcome or support forms.
        """
        check_context(principal, request.acting_party_id)
        record = await self._owned(principal, request_id, lock=True)
        require(principal, Capability.EDIT_PORTFOLIO, record.owner_party_id)
        check_expected(record.version, request.expected_version)
        allowed, target = TRANSITIONS[action]
        if record.status not in allowed:
            raise InvalidTransitionError()
        if target == "ACTIVE":
            missing = []
            if not record.outcome:
                missing.append(
                    {"loc": ["body", "outcome"], "msg": "Isi hasil yang ingin dicapai.", "type": "activation"}
                )
            if not record.support_forms:
                missing.append(
                    {
                        "loc": ["body", "support_forms"],
                        "msg": "Pilih setidaknya satu bentuk dukungan.",
                        "type": "activation",
                    }
                )
            if missing:
                raise FieldsInvalidError(missing)
        record.status = target
        record.version += 1
        await self.session.flush()
        await self._carry_budget(record.id, record.version - 1, record.version)
        await self.repository.snapshot(record.id, record.version, jsonable_encoder(await self.view(record)))
        await publish(
            self.session, "support_request.changed", {"support_request_id": str(record.id), "version": record.version}
        )
        await record_audit(
            self.session,
            action=f"support_request.{action}",
            subject_type="support_request",
            subject_id=str(record.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return await self.view(record, operation_id)
