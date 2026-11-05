"""Company funding requests: one raise owns its target and links several invention versions (FR07)."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.capabilities.service.service import SUPPORTED_CURRENCIES
from app.core.errors.base import FieldsInvalidError, InvalidTransitionError, NotFoundError
from app.core.types import money_text, parse_decimal
from app.funding.model.schema import (
    PROPOSED_LABEL,
    FundingRequestInput,
    FundingRequestResponse,
    LegalEntityInput,
    LegalEntityResponse,
    LinkedInvention,
    UpdateFundingRequest,
)
from app.funding.repository.sqlalchemy.models import FundingRequestRecord, LegalEntityRecord
from app.funding.repository.sqlalchemy.repository import SqlAlchemyFundingRepository
from app.identity.model.models import Principal
from app.needs.model.schema import TransitionRequest
from app.needs.service.service import TRANSITIONS
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import check_expected
from app.portfolio.service.service import invention_reference, owned_submittable_version

NOT_A_NUMBER = "Isi dengan angka desimal, misalnya 500000 atau 500000.50."
_CONTENT = (
    "subject_type",
    "legal_entity_id",
    "proposed_name",
    "financing_stage",
    "financing_form",
    "currency",
    "accepts_partial",
    "accepts_syndicated",
    "intended_use",
    "timing",
)


def _field_error(field: str, message: str) -> dict[str, Any]:
    return {"loc": ["body", field], "msg": message, "type": "funding"}


def validate_amounts(request: FundingRequestInput) -> tuple[list[dict[str, Any]], dict[str, Decimal | None]]:
    """Check the target and desired contribution exactly.

    Args:
        request (FundingRequestInput): The content.

    Returns:
        tuple[list[dict[str, Any]], dict[str, Decimal | None]]: Field errors, and the parsed amounts.
    """
    errors: list[dict[str, Any]] = []
    values: dict[str, Decimal | None] = {}
    for field in ("target_amount", "desired_min", "desired_max"):
        text = getattr(request, field)
        values[field] = None if text in (None, "") else parse_decimal(text)
        if text not in (None, "") and values[field] is None:
            errors.append(_field_error(field, NOT_A_NUMBER))
    target, low, high = values["target_amount"], values["desired_min"], values["desired_max"]
    if target is not None and target <= 0:
        errors.append(_field_error("target_amount", "Isi target pendanaan lebih dari nol."))
    if (low is None) != (high is None) and not errors:
        errors.append(_field_error("desired_max", "Isi batas bawah dan batas atas, atau kosongkan keduanya."))
    if low is not None and low < 0:
        errors.append(_field_error("desired_min", "Isi angka tanpa tanda minus."))
    if low is not None and high is not None and high < low:
        errors.append(_field_error("desired_max", "Batas atas tidak boleh lebih kecil dari batas bawah."))
    if any(value is not None for value in values.values()) and request.currency is None:
        errors.append(_field_error("currency", "Pilih mata uang."))
    if request.currency is not None and request.currency not in SUPPORTED_CURRENCIES:
        errors.append(_field_error("currency", "Mata uang ini belum didukung. Pilih IDR atau USD."))
    return errors, values


def _entity(record: LegalEntityRecord) -> LegalEntityResponse:
    return LegalEntityResponse(
        id=record.id,
        name=record.name,
        jurisdiction=record.jurisdiction,
        registration_reference=record.registration_reference,
        review_status=record.review_status,
    )


class FundingService:
    """Legal entities and funding requests of the acting party."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyFundingRepository(session)

    async def declare_entity(self, principal: Principal, request: LegalEntityInput) -> LegalEntityResponse:
        """Record a company as declared by the acting party.

        Args:
            principal (Principal): Who is signed in.
            request (LegalEntityInput): Name, jurisdiction and registration reference.

        Returns:
            LegalEntityResponse: The entity, ``declared``.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, principal.active_party_id)
        record = await self.repository.add(
            LegalEntityRecord(
                owner_party_id=principal.active_party_id,
                name=request.name,
                jurisdiction=request.jurisdiction,
                registration_reference=request.registration_reference,
            )
        )
        return _entity(record)

    async def entities(self, principal: Principal) -> list[LegalEntityResponse]:
        """List the acting party's legal entities.

        Args:
            principal (Principal): Who is signed in.

        Returns:
            list[LegalEntityResponse]: Entities.
        """
        return [_entity(record) for record in await self.repository.entities_of(principal.active_party_id)]

    async def view(self, record: FundingRequestRecord, operation_id: UUID | None = None) -> FundingRequestResponse:
        """Render a request with its entity and linked invention versions.

        Args:
            record (FundingRequestRecord): The request.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            FundingRequestResponse: The request.
        """
        entity = await self.repository.entity(record.legal_entity_id) if record.legal_entity_id else None
        inventions = []
        for link in await self.repository.links(record.id):
            reference = await invention_reference(self.session, link.invention_version_id)
            inventions.append(
                LinkedInvention(invention_id=link.invention_id, version=reference.number, title=reference.title)
            )
        return FundingRequestResponse(
            id=record.id,
            version=record.version,
            subject_label=entity.name if entity else PROPOSED_LABEL,
            legal_entity=_entity(entity) if entity else None,
            target_amount=money_text(record.target_amount),
            desired_min=money_text(record.desired_min),
            desired_max=money_text(record.desired_max),
            inventions=inventions,
            status=record.status,
            operation_id=operation_id,
            **{field: getattr(record, field) for field in _CONTENT if field != "legal_entity_id"},
        )

    async def _owned(self, principal: Principal, request_id: UUID, *, lock: bool = False) -> FundingRequestRecord:
        record = await self.repository.find(request_id, lock=lock)
        if record is None or record.owner_party_id != principal.active_party_id:
            raise NotFoundError()
        return record

    async def _checked(self, principal: Principal, request: FundingRequestInput) -> dict[str, Any]:
        """Validate everything before any write; return the parsed amounts and the links."""
        errors, amounts = validate_amounts(request)
        if request.subject_type == "EXISTING_ENTITY" and request.legal_entity_id is None:
            errors.append(_field_error("legal_entity_id", "Pilih badan hukum perusahaan."))
        if request.subject_type == "PROPOSED_ENTITY" and request.legal_entity_id is not None:
            errors.append(
                _field_error("legal_entity_id", "Perusahaan yang belum didirikan tidak memiliki badan hukum.")
            )
        if errors:
            raise FieldsInvalidError(errors)
        if request.legal_entity_id is not None:
            entity = await self.repository.entity(request.legal_entity_id)
            if entity is None or entity.owner_party_id != principal.active_party_id:
                raise NotFoundError()
        links = []
        for invention_id in dict.fromkeys(request.invention_ids):
            links.append(
                (invention_id, await owned_submittable_version(self.session, invention_id, principal.active_party_id))
            )
        return {"amounts": amounts, "links": links}

    async def _record_version(self, record: FundingRequestRecord) -> None:
        await self.repository.snapshot(record.id, record.version, jsonable_encoder(await self.view(record)))
        await publish(
            self.session, "funding_request.changed", {"funding_request_id": str(record.id), "version": record.version}
        )

    async def _write(self, record: FundingRequestRecord, request: FundingRequestInput, checked: dict[str, Any]) -> None:
        for field in _CONTENT:
            setattr(record, field, getattr(request, field))
        for field, value in checked["amounts"].items():
            setattr(record, field, value)
        await self.session.flush()
        await self.repository.replace_links(record.id, checked["links"])
        await self._record_version(record)

    async def create(self, principal: Principal, request: FundingRequestInput) -> FundingRequestResponse:
        """Start a draft raise for an existing or a proposed company.

        Args:
            principal (Principal): Who is signed in.
            request (FundingRequestInput): Content and invention links.

        Returns:
            FundingRequestResponse: The draft.

        Raises:
            FieldsInvalidError: When an amount or the subject breaks a rule; nothing is stored.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, principal.active_party_id)
        checked = await self._checked(principal, request)
        record = await self.repository.add(
            FundingRequestRecord(
                owner_party_id=principal.active_party_id,
                subject_type=request.subject_type,
                legal_entity_id=request.legal_entity_id,
            )
        )
        await self._write(record, request, checked)
        return await self.view(record)

    async def list_mine(self, principal: Principal) -> list[FundingRequestResponse]:
        """List the acting party's funding requests, readable whatever the composition (AC67).

        Args:
            principal (Principal): Who is signed in.

        Returns:
            list[FundingRequestResponse]: Requests.
        """
        return [await self.view(record) for record in await self.repository.of_party(principal.active_party_id)]

    async def read(self, principal: Principal, request_id: UUID) -> FundingRequestResponse:
        """Read one request as its owner.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.

        Returns:
            FundingRequestResponse: The request.
        """
        return await self.view(await self._owned(principal, request_id))

    async def version(self, principal: Principal, request_id: UUID, number: int) -> dict:
        """Read the request as it stood at an earlier version.

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
        self, principal: Principal, request_id: UUID, request: UpdateFundingRequest, operation_id: UUID | None = None
    ) -> FundingRequestResponse:
        """Replace the content as a new version; earlier versions stay readable.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.
            request (UpdateFundingRequest): Content and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            FundingRequestResponse: The new version.
        """
        check_context(principal, request.acting_party_id)
        record = await self._owned(principal, request_id, lock=True)
        require(principal, Capability.EDIT_PORTFOLIO, record.owner_party_id)
        if record.status == "CLOSED":
            raise InvalidTransitionError()
        check_expected(record.version, request.expected_version)
        checked = await self._checked(principal, request)
        record.version += 1
        await self._write(record, request, checked)
        return await self.view(record, operation_id)

    async def transition(
        self,
        principal: Principal,
        request_id: UUID,
        action: str,
        request: TransitionRequest,
        operation_id: UUID | None = None,
    ) -> FundingRequestResponse:
        """Activate, pause or close. Activation needs a target, a currency and at least one invention.

        Args:
            principal (Principal): Who is signed in.
            request_id (UUID): The request.
            action (str): ``activate``, ``pause`` or ``close``.
            request (TransitionRequest): Acting party and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            FundingRequestResponse: The request in its new status.

        Raises:
            InvalidTransitionError: From a status that does not allow it.
            FieldsInvalidError: When activating an incomplete request.
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
            if record.target_amount is None:
                missing.append(_field_error("target_amount", "Isi target pendanaan sebelum mengaktifkan."))
            if not await self.repository.links(record.id):
                missing.append(_field_error("invention_ids", "Tautkan setidaknya satu inovasi yang sudah terbit."))
            if missing:
                raise FieldsInvalidError(missing)
        record.status = target
        record.version += 1
        await self.session.flush()
        await self._record_version(record)
        await record_audit(
            self.session,
            action=f"funding_request.{action}",
            subject_type="funding_request",
            subject_id=str(record.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return await self.view(record, operation_id)
