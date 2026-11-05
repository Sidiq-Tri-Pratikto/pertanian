"""Partner intake: profiles that state only what is known, and opportunities with versions, states and requirements."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.access.service.service import party_names
from app.core import clock
from app.core.errors.base import ConflictError, FieldsInvalidError, InvalidTransitionError, NotFoundError
from app.core.types import money_text
from app.identity.model.models import Principal
from app.intake.model.schema import (
    AvailabilityResponse,
    CreateOpportunityRequest,
    FinancialResponse,
    HandoffResponse,
    OpportunityContent,
    OpportunityResponse,
    OpportunityTransitionRequest,
    OpportunityVersionResponse,
    PartnerProfileContent,
    PartnerProfileResponse,
    RangeResponse,
    RecordHandoffRequest,
    RequirementResponse,
    SaveOpportunityRequest,
    SavePartnerProfileRequest,
    TargetAvailabilityResponse,
)
from app.intake.repository.sqlalchemy.models import (
    ExternalHandoffRecord,
    OpportunityRecord,
    OpportunityVersionRecord,
    PartnerProfileRecord,
    RequirementRecord,
)
from app.intake.repository.sqlalchemy.repository import SqlAlchemyIntakeRepository
from app.intake.service.financial import validate_check_range, validate_financial
from app.intake.service.requirements import validate_requirements
from app.platform.service.audit import record_audit
from app.platform.service.outbox import enqueue_job, publish
from app.platform.service.versions import StaleVersionError, check_expected

EXPIRE_JOB = "intake.expire_opportunity"
GENERAL_INTAKE_LABEL = "berdasarkan profil umum mitra"

# Allowed status changes; EXPIRED comes from ``closes_at``, never from a person.
TRANSITIONS = {
    "activate": ({"DRAFT", "PAUSED"}, "ACTIVE"),
    "pause": ({"ACTIVE"}, "PAUSED"),
    "close": ({"DRAFT", "ACTIVE", "PAUSED"}, "CLOSED"),
}
_LIVE = frozenset({"ACTIVE", "PAUSED"})
_SOURCE_LABELS = {"OWNER_CONFIRMED": "Dikonfirmasi pemilik profil", "SOURCE_REPORTED": "Dilaporkan sumber"}
_INTAKE_LABELS = {
    "OPEN": "Pitching dibuka",
    "CLOSED": "Penerimaan ditutup",
    "UNCONFIRMED": "Ketersediaan belum dikonfirmasi",
}
_READY_FIELDS = {
    "title": "Isi judul mandat.",
    "outcome": "Isi hasil yang dicari.",
    "included": "Isi apa yang termasuk.",
    "excluded": "Isi apa yang tidak termasuk.",
    "support": "Isi dukungan yang ditawarkan.",
    "accepted_stages": "Pilih setidaknya satu tahap yang diterima.",
    "relationship_forms": "Pilih setidaknya satu bentuk kerja sama.",
    "timing": "Isi waktu penerimaan.",
    "financial": "Isi dasar keuangan mandat ini.",
}
_VERSION_FIELDS = (
    "title",
    "outcome",
    "included",
    "excluded",
    "support",
    "accepted_stages",
    "relationship_forms",
    "sectors",
    "keywords",
    "timing",
)
_REQUIREMENT_FIELDS = (
    "label",
    "field",
    "operator",
    "value",
    "mandatory",
    "applies_at",
    "verification_mode",
    "visibility",
    "reason",
)


def effective_status(status: str, closes_at: datetime | None, now: datetime) -> str:
    """Return the status a reader should see: a live opportunity past ``closes_at`` has expired, stored or not.

    Args:
        status (str): The stored status.
        closes_at (datetime | None): When it closes.
        now (datetime): The current product time.

    Returns:
        str: The status.
    """
    return "EXPIRED" if status in _LIVE and closes_at is not None and closes_at <= now else status


def current_intake_status(intake_status: str, intake_from: date | None, intake_until: date | None, today: date) -> str:
    """Return the intake state to show now: an open intake outside its dates is no longer confirmed.

    Args:
        intake_status (str): The stored state.
        intake_from (date | None): First day of the intake.
        intake_until (date | None): Last day of the intake.
        today (date): The current product date.

    Returns:
        str: The state.
    """
    if intake_status != "OPEN":
        return intake_status
    outside = (intake_from is not None and today < intake_from) or (intake_until is not None and today > intake_until)
    return "UNCONFIRMED" if outside else "OPEN"


def target_availability_of(
    *,
    kind: str,
    status: str,
    contact_route: str,
    intake_status: str,
    intake_from: date | None,
    intake_until: date | None,
    today: date,
) -> TargetAvailabilityResponse:
    """Decide whether a pitch may target this now (D16). The first check that fails gives the reason.

    Args:
        kind (str): ``SPECIFIC`` or ``GENERAL_INTAKE``.
        status (str): The effective status.
        contact_route (str): The partner's route.
        intake_status (str): The partner's stored intake state.
        intake_from (date | None): First day of the intake.
        intake_until (date | None): Last day of the intake.
        today (date): The current product date.

    Returns:
        TargetAvailabilityResponse: Whether it is available, and why not.
    """
    reason = None
    current = current_intake_status(intake_status, intake_from, intake_until, today)
    if status != "ACTIVE":
        reason = "TARGET_NOT_ACTIVE"
    elif contact_route == "EXTERNAL":
        reason = "EXTERNAL_ROUTE"
    elif contact_route == "NONE":
        reason = "NO_NEW_APPROACHES"
    elif kind == "GENERAL_INTAKE" and current == "CLOSED":
        reason = "DIRECT_INTAKE_CLOSED"
    elif kind == "GENERAL_INTAKE" and current == "UNCONFIRMED":
        reason = "INTAKE_UNCONFIRMED"
    return TargetAvailabilityResponse(available=reason is None, reason=reason)


def _not_ready(loc: list[Any], message: str) -> dict:
    return {"loc": loc, "msg": message, "type": "activation"}


class IntakeService:
    """Partner profiles, opportunities and external handoffs."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyIntakeRepository(session)

    async def _profile_view(
        self, record: PartnerProfileRecord, operation_id: UUID | None = None
    ) -> PartnerProfileResponse:
        names = await party_names(self.session, [record.party_id])
        check_range = None
        if record.range_subject is not None:
            check_range = RangeResponse(
                subject=record.range_subject,
                basis=record.range_basis,
                min=money_text(record.check_min),
                max=money_text(record.check_max),
                currency=record.currency,
                period=record.range_period,
                months=record.range_months,
                unknown_reason=record.unknown_reason,
            )
        current = current_intake_status(
            record.intake_status, record.intake_from, record.intake_until, clock.now().date()
        )
        return PartnerProfileResponse(
            party_id=record.party_id,
            party_name=names.get(record.party_id, ""),
            version=record.version,
            subtype=record.subtype,
            thesis=record.thesis,
            sectors=record.sectors,
            stages=record.stages,
            regions=record.regions,
            support_forms=record.support_forms,
            relationship_forms=record.relationship_forms,
            review_expectations=record.review_expectations,
            check_range=check_range,
            availability=AvailabilityResponse(
                source=record.source,
                source_label=_SOURCE_LABELS[record.source],
                intake_status=record.intake_status,
                current_intake_status=current,
                label=_INTAKE_LABELS[current],
                intake_from=record.intake_from,
                intake_until=record.intake_until,
            ),
            contact_route=record.contact_route,
            external_url=record.external_url,
            operation_id=operation_id,
        )

    @staticmethod
    def _profile_columns(content: PartnerProfileContent) -> dict[str, Any]:
        """Validate what a profile states and turn it into columns.

        Args:
            content (PartnerProfileContent): The content as sent.

        Returns:
            dict[str, Any]: Profile columns.

        Raises:
            FieldsInvalidError: When a field breaks a rule.
        """
        errors: list[dict] = []
        values: dict[str, Any] = {}
        if content.check_range is not None:
            errors, values = validate_check_range(content.check_range, ["body", "check_range"])
        if content.contact_route == "EXTERNAL" and content.external_url is None:
            errors.append(
                {"loc": ["body", "external_url"], "msg": "Isi alamat jalur eksternal.", "type": "partner_profile"}
            )
        if content.intake_from and content.intake_until and content.intake_until < content.intake_from:
            errors.append(
                {
                    "loc": ["body", "intake_until"],
                    "msg": "Tanggal akhir tidak boleh sebelum tanggal mulai.",
                    "type": "partner_profile",
                }
            )
        if errors:
            raise FieldsInvalidError(errors)
        return {
            "subtype": content.subtype,
            "thesis": content.thesis,
            "sectors": content.sectors,
            "stages": content.stages,
            "regions": content.regions,
            "support_forms": content.support_forms,
            "relationship_forms": content.relationship_forms,
            "review_expectations": content.review_expectations,
            "check_min": values.get("min"),
            "check_max": values.get("max"),
            "currency": values.get("currency"),
            "range_subject": values.get("subject"),
            "range_basis": values.get("basis"),
            "range_period": values.get("period", ""),
            "range_months": values.get("months"),
            "unknown_reason": values.get("unknown_reason"),
            "intake_from": content.intake_from,
            "intake_until": content.intake_until,
            "contact_route": content.contact_route,
            "external_url": str(content.external_url) if content.contact_route == "EXTERNAL" else None,
        }

    async def read_profile(self, party_id: UUID) -> PartnerProfileResponse:
        """Read a party's profile as anyone signed in may see it.

        Args:
            party_id (UUID): The party.

        Returns:
            PartnerProfileResponse: The profile.

        Raises:
            NotFoundError: When the party has no profile.
        """
        record = await self.repository.profile(party_id)
        if record is None:
            raise NotFoundError()
        return await self._profile_view(record)

    async def save_profile(
        self, principal: Principal, party_id: UUID, request: SavePartnerProfileRequest, operation_id: UUID | None = None
    ) -> PartnerProfileResponse:
        """Save the acting party's own profile. Always owner-confirmed; the first save has no version to compare (D17).

        Args:
            principal (Principal): Who is signed in.
            party_id (UUID): The party.
            request (SavePartnerProfileRequest): The content and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnerProfileResponse: The saved profile.

        Raises:
            StaleVersionError: When the version is not the stored one, or a first save lost a race.
            FieldsInvalidError: When a field breaks a rule.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, party_id)
        columns = self._profile_columns(request)
        columns |= {"intake_status": request.intake_status, "source": "OWNER_CONFIRMED"}
        record = await self.repository.profile(party_id, lock=True)
        if record is None:
            record = await self._first_profile(party_id, columns, request.expected_version)
        else:
            if request.expected_version is None:
                raise StaleVersionError(record.version)
            check_expected(record.version, request.expected_version)
            for name, value in columns.items():
                setattr(record, name, value)
            record.version += 1
            await self.session.flush()
        await self._profile_changed(record, "partner.saved", principal)
        return await self._profile_view(record, operation_id)

    async def _first_profile(
        self, party_id: UUID, columns: dict[str, Any], expected_version: int | None
    ) -> PartnerProfileRecord:
        if expected_version is not None:
            raise StaleVersionError(0)
        created = await self.repository.insert_first_profile({"party_id": party_id, **columns})
        record = await self.repository.profile(party_id)
        assert record is not None  # noqa: S101 - it was inserted, or another request just committed it
        if not created:
            raise StaleVersionError(record.version)
        return record

    async def _profile_changed(
        self, record: PartnerProfileRecord, action: str, principal: Principal | None = None
    ) -> None:
        await publish(self.session, "partner.changed", {"party_id": str(record.party_id), "version": record.version})
        await record_audit(
            self.session,
            action=action,
            subject_type="partner_profile",
            subject_id=str(record.party_id),
            actor_account_id=principal.account_id if principal else None,
            actor_party_id=principal.active_party_id if principal else None,
        )

    async def record_directory_profile(self, party_id: UUID, content: PartnerProfileContent) -> PartnerProfileResponse:
        """Record what a source reports about a party. Service only: nobody may claim a source through the API (D6).

        Args:
            party_id (UUID): The party.
            content (PartnerProfileContent): What the source reports; anything it did not say stays empty.

        Returns:
            PartnerProfileResponse: The profile, labelled as reported, with intake unconfirmed.

        Raises:
            ConflictError: When the party already has a profile, which a directory entry must not replace.
        """
        columns = self._profile_columns(content) | {"intake_status": "UNCONFIRMED", "source": "SOURCE_REPORTED"}
        if not await self.repository.insert_first_profile({"party_id": party_id, **columns}):
            raise ConflictError()
        record = await self.repository.profile(party_id)
        assert record is not None  # noqa: S101 - it was just inserted
        await self._profile_changed(record, "partner.directory_recorded")
        return await self._profile_view(record)

    async def record_handoff(
        self, principal: Principal, party_id: UUID, request: RecordHandoffRequest, operation_id: UUID | None = None
    ) -> HandoffResponse:
        """Record that the acting party followed a partner's external route. It is never a pitch (AC24).

        Args:
            principal (Principal): Who is signed in.
            party_id (UUID): The partner.
            request (RecordHandoffRequest): The acting party.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            HandoffResponse: The handoff, with the address to open.

        Raises:
            NotFoundError: When the party has no profile.
            ConflictError: When its route is not external.
        """
        check_context(principal, request.acting_party_id)
        profile = await self.repository.profile(party_id)
        if profile is None:
            raise NotFoundError()
        if profile.contact_route != "EXTERNAL" or profile.external_url is None:
            raise ConflictError("Mitra ini tidak memakai jalur eksternal. Gunakan jalur yang tersedia pada profilnya.")
        handoff = await self.repository.add(
            ExternalHandoffRecord(
                partner_party_id=party_id, actor_party_id=principal.active_party_id, external_url=profile.external_url
            )
        )
        await record_audit(
            self.session,
            action="external_handoff.recorded",
            subject_type="partner_profile",
            subject_id=str(party_id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return HandoffResponse(
            id=handoff.id, partner_party_id=party_id, external_url=handoff.external_url, operation_id=operation_id
        )

    def _availability(
        self, record: OpportunityRecord, profile: PartnerProfileRecord | None, status: str
    ) -> TargetAvailabilityResponse:
        return target_availability_of(
            kind=record.kind,
            status=status,
            # Activation needs a profile, so only a target that is not active can lack one.
            contact_route=profile.contact_route if profile else "NONE",
            intake_status=profile.intake_status if profile else "UNCONFIRMED",
            intake_from=profile.intake_from if profile else None,
            intake_until=profile.intake_until if profile else None,
            today=clock.now().date(),
        )

    @staticmethod
    def _content(version: OpportunityVersionRecord, rows: list[RequirementRecord], *, owner: bool) -> dict[str, Any]:
        visible = [row for row in rows if owner or row.visibility == "PUBLIC"]
        return {
            "number": version.number,
            **{name: getattr(version, name) for name in _VERSION_FIELDS},
            "financial": FinancialResponse(**version.financial) if version.financial else None,
            "requirements": [
                RequirementResponse(
                    id=row.id, version=version.number, **{name: getattr(row, name) for name in _REQUIREMENT_FIELDS}
                )
                for row in visible
            ],
        }

    def _view(
        self,
        record: OpportunityRecord,
        version: OpportunityVersionRecord,
        rows: list[RequirementRecord],
        profile: PartnerProfileRecord | None,
        *,
        owner: bool,
        operation_id: UUID | None = None,
    ) -> OpportunityResponse:
        status = effective_status(record.status, record.closes_at, clock.now())
        return OpportunityResponse(
            id=record.id,
            partner_party_id=record.partner_party_id,
            version=record.version,
            kind=record.kind,
            status=status,
            closes_at=record.closes_at,
            target_availability=self._availability(record, profile, status),
            general_intake_label=GENERAL_INTAKE_LABEL if record.kind == "GENERAL_INTAKE" else None,
            operation_id=operation_id,
            **self._content(version, rows, owner=owner),
        )

    async def _owner_view(self, record: OpportunityRecord, operation_id: UUID | None = None) -> OpportunityResponse:
        version = await self.repository.version(record.current_version_id)
        assert version is not None  # noqa: S101 - the pointer always names a stored version
        rows = await self.repository.requirements([version.id])
        profile = await self.repository.profile(record.partner_party_id)
        return self._view(record, version, rows[version.id], profile, owner=True, operation_id=operation_id)

    @staticmethod
    def _validated(content: OpportunityContent) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Validate an opportunity's content and turn it into version columns and requirement rows.

        Args:
            content (OpportunityContent): The content as sent.

        Returns:
            tuple[dict[str, Any], list[dict[str, Any]]]: Version columns and requirement rows.

        Raises:
            FieldsInvalidError: When a field breaks a rule.
        """
        errors: list[dict] = []
        financial = None
        if content.financial is not None:
            errors, financial = validate_financial(content.financial)
        requirement_errors, rows = validate_requirements(content.requirements, financial)
        errors += requirement_errors
        if errors:
            raise FieldsInvalidError(errors)
        return {**{name: getattr(content, name) for name in _VERSION_FIELDS}, "financial": financial}, rows

    async def _require_ready(
        self, party_id: UUID, columns: dict[str, Any], rows: list[dict[str, Any]], closes_at: datetime | None
    ) -> None:
        """Refuse content that may not go live (D1). Activation and any save on a live opportunity pass through here.

        Args:
            party_id (UUID): The partner.
            columns (dict[str, Any]): Version columns.
            rows (list[dict[str, Any]]): Requirement rows.
            closes_at (datetime | None): When it closes.

        Raises:
            FieldsInvalidError: Naming everything still missing.
        """
        errors = [_not_ready(["body", name], message) for name, message in _READY_FIELDS.items() if not columns[name]]
        errors += [
            _not_ready(["body", "requirements", index, "reason"], "Jelaskan alasan syarat wajib ini.")
            for index, row in enumerate(rows)
            if row["mandatory"] and not row["reason"]
        ]
        if closes_at is not None and closes_at <= clock.now():
            errors.append(_not_ready(["body", "closes_at"], "Pilih waktu tutup yang belum lewat."))
        if await self.repository.profile(party_id) is None:
            errors.append(_not_ready(["partner_profile"], "Simpan profil mitra sebelum mengaktifkan mandat."))
        if errors:
            raise FieldsInvalidError(errors)

    async def _owned(self, principal: Principal, opportunity_id: UUID, *, lock: bool = False) -> OpportunityRecord:
        record = await self.repository.find(opportunity_id, lock=lock)
        if record is None:
            raise NotFoundError()
        require(principal, Capability.EDIT_PORTFOLIO, record.partner_party_id)
        return record

    async def _changed(self, record: OpportunityRecord, action: str, principal: Principal | None = None) -> None:
        await publish(
            self.session, "opportunity.changed", {"opportunity_id": str(record.id), "version": record.version}
        )
        await record_audit(
            self.session,
            action=f"opportunity.{action}",
            subject_type="opportunity",
            subject_id=str(record.id),
            actor_account_id=principal.account_id if principal else None,
            actor_party_id=principal.active_party_id if principal else None,
        )

    async def _point_general_intake(self, record: OpportunityRecord, version_id: UUID | None) -> None:
        if record.kind != "GENERAL_INTAKE":
            return
        profile = await self.repository.profile(record.partner_party_id)
        if profile is not None:
            profile.general_intake_version_id = version_id
            await self.session.flush()

    async def _schedule_expiry(self, record: OpportunityRecord) -> None:
        if record.closes_at is not None:
            await enqueue_job(
                self.session,
                EXPIRE_JOB,
                {"opportunity_id": str(record.id)},
                actor_party_id=record.partner_party_id,
                run_after=record.closes_at,
            )

    async def create(
        self, principal: Principal, request: CreateOpportunityRequest, operation_id: UUID | None = None
    ) -> OpportunityResponse:
        """Start a draft for the acting party. A draft needs no profile and may be incomplete.

        Args:
            principal (Principal): Who is signed in.
            request (CreateOpportunityRequest): The kind and content.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            OpportunityResponse: The draft.

        Raises:
            FieldsInvalidError: When a field breaks a rule.
            ConflictError: When the partner already has an open general intake.
        """
        check_context(principal, request.acting_party_id)
        party_id = principal.active_party_id
        require(principal, Capability.EDIT_PORTFOLIO, party_id)
        columns, rows = self._validated(request)
        if request.kind == "GENERAL_INTAKE" and await self.repository.open_general_intake(party_id) is not None:
            raise ConflictError(
                "Mitra ini sudah punya penerimaan umum yang terbuka. Tutup yang lama lalu buat yang baru."
            )
        record = await self.repository.add(
            OpportunityRecord(partner_party_id=party_id, kind=request.kind, closes_at=request.closes_at)
        )
        version = await self.repository.add(OpportunityVersionRecord(opportunity_id=record.id, number=1, **columns))
        record.current_version_id = version.id
        await self.session.flush()
        await self.repository.replace_requirements(version.id, rows)
        await self._changed(record, "created", principal)
        return await self._owner_view(record, operation_id)

    async def save(
        self,
        principal: Principal,
        opportunity_id: UUID,
        request: SaveOpportunityRequest,
        operation_id: UUID | None = None,
    ) -> OpportunityResponse:
        """Save an opportunity: a draft in place, a live one as the next version that is current at once (D1).

        Args:
            principal (Principal): Who is signed in.
            opportunity_id (UUID): The opportunity.
            request (SaveOpportunityRequest): The content and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            OpportunityResponse: The opportunity with its new content.

        Raises:
            InvalidTransitionError: When it is closed or expired.
            FieldsInvalidError: When a field breaks a rule, or a live save lacks what going live needs.
        """
        check_context(principal, request.acting_party_id)
        record = await self._owned(principal, opportunity_id, lock=True)
        status = effective_status(record.status, record.closes_at, clock.now())
        if status in {"CLOSED", "EXPIRED"}:
            raise InvalidTransitionError()
        check_expected(record.version, request.expected_version)
        columns, rows = self._validated(request)
        moved = record.closes_at != request.closes_at
        current = await self.repository.version(record.current_version_id)
        assert current is not None  # noqa: S101 - the pointer always names a stored version
        if status in _LIVE:
            await self._require_ready(record.partner_party_id, columns, rows, request.closes_at)
            version = await self.repository.add(
                OpportunityVersionRecord(opportunity_id=record.id, number=current.number + 1, **columns)
            )
            record.current_version_id = version.id
        else:
            version = current
            for name, value in columns.items():
                setattr(version, name, value)
        record.closes_at = request.closes_at
        record.version += 1
        await self.session.flush()
        await self.repository.replace_requirements(version.id, rows)
        if status in _LIVE:
            await self._point_general_intake(record, version.id)
            if moved:
                await self._schedule_expiry(record)
        await self._changed(record, "saved", principal)
        return await self._owner_view(record, operation_id)

    async def transition(
        self,
        principal: Principal,
        opportunity_id: UUID,
        action: str,
        request: OpportunityTransitionRequest,
        operation_id: UUID | None = None,
    ) -> OpportunityResponse:
        """Activate, pause or close.

        Args:
            principal (Principal): Who is signed in.
            opportunity_id (UUID): The opportunity.
            action (str): ``activate``, ``pause`` or ``close``.
            request (OpportunityTransitionRequest): Acting party and ``expected_version``.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            OpportunityResponse: The opportunity in its new status.

        Raises:
            InvalidTransitionError: From a status that does not allow it.
            FieldsInvalidError: When activating what may not go live.
        """
        check_context(principal, request.acting_party_id)
        record = await self._owned(principal, opportunity_id, lock=True)
        check_expected(record.version, request.expected_version)
        allowed, target = TRANSITIONS[action]
        if effective_status(record.status, record.closes_at, clock.now()) not in allowed:
            raise InvalidTransitionError()
        if target == "ACTIVE":
            await self._require_current_ready(record)
        record.status = target
        record.version += 1
        await self.session.flush()
        if target == "ACTIVE":
            await self._point_general_intake(record, record.current_version_id)
            await self._schedule_expiry(record)
        elif target == "CLOSED":
            await self._point_general_intake(record, None)
        await self._changed(record, action, principal)
        return await self._owner_view(record, operation_id)

    async def _require_current_ready(self, record: OpportunityRecord) -> None:
        version = await self.repository.version(record.current_version_id)
        assert version is not None  # noqa: S101 - the pointer always names a stored version
        stored = await self.repository.requirements([version.id])
        columns = {name: getattr(version, name) for name in _READY_FIELDS}
        rows = [{"mandatory": row.mandatory, "reason": row.reason} for row in stored[version.id]]
        await self._require_ready(record.partner_party_id, columns, rows, record.closes_at)

    async def read(self, principal: Principal, opportunity_id: UUID) -> OpportunityResponse:
        """Read an opportunity. Others never reach a draft and see only requirements meant for applicants (D4, D9).

        Args:
            principal (Principal): Who is signed in.
            opportunity_id (UUID): The opportunity.

        Returns:
            OpportunityResponse: The opportunity with its current version.

        Raises:
            NotFoundError: When it does not exist, or is a draft of another party.
        """
        record = await self.repository.find(opportunity_id)
        owner = record is not None and record.partner_party_id == principal.active_party_id
        if record is None or (record.status == "DRAFT" and not owner):
            raise NotFoundError()
        version = await self.repository.version(record.current_version_id)
        assert version is not None  # noqa: S101 - the pointer always names a stored version
        rows = await self.repository.requirements([version.id])
        profile = await self.repository.profile(record.partner_party_id)
        return self._view(record, version, rows[version.id], profile, owner=owner)

    async def read_version(self, principal: Principal, opportunity_id: UUID, number: int) -> OpportunityVersionResponse:
        """Read one version as it stood. Others may read only the current version of what they can see.

        Args:
            principal (Principal): Who is signed in.
            opportunity_id (UUID): The opportunity.
            number (int): The version number.

        Returns:
            OpportunityVersionResponse: The version.

        Raises:
            NotFoundError: When it does not exist or is not for this party to see.
        """
        record = await self.repository.find(opportunity_id)
        if record is None:
            raise NotFoundError()
        owner = record.partner_party_id == principal.active_party_id
        version = await self.repository.version_by_number(opportunity_id, number)
        hidden = not owner and (record.status == "DRAFT" or (version and version.id != record.current_version_id))
        if version is None or hidden:
            raise NotFoundError()
        rows = await self.repository.requirements([version.id])
        return OpportunityVersionResponse(
            id=version.id,
            opportunity_id=record.id,
            status=effective_status(record.status, record.closes_at, clock.now()),
            **self._content(version, rows[version.id], owner=owner),
        )

    async def list_for(
        self, principal: Principal, partner_party_id: UUID | None, limit: int
    ) -> list[OpportunityResponse]:
        """List the acting party's opportunities, or what another partner has made visible.

        Args:
            principal (Principal): Who is signed in.
            partner_party_id (UUID | None): Another partner; None for one's own.
            limit (int): The most to return.

        Returns:
            list[OpportunityResponse]: Newest change first.
        """
        party_id = partner_party_id or principal.active_party_id
        owner = party_id == principal.active_party_id
        records = await self.repository.of_partner(party_id, include_drafts=owner, limit=limit)
        if not records:
            return []
        version_ids = [record.current_version_id for record in records]
        versions = await self.repository.versions(version_ids)
        rows = await self.repository.requirements(version_ids)
        profile = await self.repository.profile(party_id)
        return [
            self._view(
                record,
                versions[record.current_version_id],
                rows[record.current_version_id],
                profile,
                owner=owner,
            )
            for record in records
        ]

    async def target_availability(self, opportunity_id: UUID) -> TargetAvailabilityResponse:
        """Say whether a pitch may target this now. Matching (019) and submission (023) call this, never their own rule.

        Args:
            opportunity_id (UUID): The opportunity.

        Returns:
            TargetAvailabilityResponse: Whether it is available, and why not.

        Raises:
            NotFoundError: When it does not exist.
        """
        record = await self.repository.find(opportunity_id)
        if record is None:
            raise NotFoundError()
        profile = await self.repository.profile(record.partner_party_id)
        status = effective_status(record.status, record.closes_at, clock.now())
        return self._availability(record, profile, status)

    async def expire(self, opportunity_id: UUID) -> None:
        """Persist expiry for an opportunity past ``closes_at``. Does nothing when the time moved or it already ended.

        Args:
            opportunity_id (UUID): The opportunity.
        """
        record = await self.repository.find(opportunity_id, lock=True)
        if record is None or record.status not in _LIVE:
            return
        if effective_status(record.status, record.closes_at, clock.now()) != "EXPIRED":
            return
        record.status = "EXPIRED"
        record.version += 1
        await self.session.flush()
        await self._point_general_intake(record, None)
        await self._changed(record, "expired")
