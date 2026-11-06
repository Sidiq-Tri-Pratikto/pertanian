"""Propose, correct, confirm, decline, restrict and contest relationship records (spec 030)."""

from collections import defaultdict
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context
from app.access.service.service import party_names
from app.core.errors import codes
from app.core.errors.base import (
    AppError,
    ConflictError,
    FieldsInvalidError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)
from app.identity.model.models import Principal
from app.pitches.service.decisions import visible_pitch
from app.pitches.service.submission import latest_snapshot
from app.platform.service.audit import record_audit
from app.platform.service.outbox import publish
from app.platform.service.versions import StaleVersionError
from app.portfolio.service.service import invention_ids_of
from app.relationships.model.schema import (
    ConfirmationResponse,
    ConfirmRequest,
    CorrectionRequest,
    EffectiveResponse,
    PartnershipResponse,
    PartnershipValues,
    PartnershipVersionResponse,
    PartyName,
    ProposePartnershipRequest,
    RestrictionResponse,
    RestrictRequest,
    ReviewRequest,
    VersionedPartnershipRequest,
)
from app.relationships.repository.sqlalchemy.models import (
    PartnershipConfirmationRecord,
    PartnershipRecord,
    PartnershipRestrictionRecord,
    PartnershipVersionRecord,
)
from app.relationships.repository.sqlalchemy.repository import SqlAlchemyRelationshipRepository
from app.relationships.service.consent import checksum, effective_fields
from app.scheduling.service.state import meeting_completed

TYPE_LABEL = {"PROJECT": "Proyek", "LICENSE": "Lisensi", "EQUITY": "Ekuitas"}


class EntityRequiredError(AppError):
    """Equity needs an identified legal entity."""

    code = codes.APP_ENTITY_REQUIRED


class MeetingNotCompletedError(AppError):
    """No meeting of the pitch was completed by both parties."""

    code = codes.APP_MEETING_NOT_COMPLETED


def public_values(kind: str, values: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Project a version's values onto public fields. Evidence never appears; a project has no share (AC54).

    Args:
        kind (str): Relationship type.
        values (dict[str, Any]): The version's values.
        fields (list[str]): Effective public fields.

    Returns:
        dict[str, Any]: Field to value.
    """
    shown: dict[str, Any] = {}
    for field in fields:
        if field == "type":
            shown["type"] = TYPE_LABEL[kind]
        elif field == "date":
            shown["date"] = values.get("start_date")
        elif field == "amount" and values.get("amount"):
            shown["amount"] = {"amount": values["amount"], "currency": values.get("currency")}
        elif field == "percent" and kind == "EQUITY" and values.get("percent"):
            shown["percent"] = {"percent": values["percent"], "effective_date": values.get("percent_date")}
        elif field in ("name", "scope"):
            shown[field] = values.get(field)
    return shown


class RelationshipService:
    """Relationship records that exist only as both parties confirm the same version."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyRelationshipRepository(session)

    @staticmethod
    def _can(principal: Principal) -> None:
        if Capability.CONFIRM_RELATIONSHIP not in principal.capabilities:
            raise ForbiddenError()

    @staticmethod
    def _values(kind: str, values: PartnershipValues) -> dict[str, Any]:
        errors = []
        if values.percent and kind != "EQUITY":
            errors.append(
                {
                    "loc": ["body", "values", "percent"],
                    "msg": "Persentase hanya berlaku untuk ekuitas.",
                    "type": "percent",
                }
            )
        if values.percent and values.percent_date is None:
            errors.append(
                {
                    "loc": ["body", "values", "percent_date"],
                    "msg": "Persentase memerlukan tanggal berlaku.",
                    "type": "percent",
                }
            )
        if values.amount and not values.currency:
            errors.append(
                {"loc": ["body", "values", "currency"], "msg": "Pilih mata uang jumlah dana.", "type": "currency"}
            )
        if errors:
            raise FieldsInvalidError(errors)
        return jsonable_encoder(values)

    async def propose(
        self, principal: Principal, pitch_id: UUID, request: ProposePartnershipRequest, operation_id: UUID | None = None
    ) -> PartnershipResponse:
        """Propose version 1 after a completed meeting; the proposer's confirmation comes with it.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.
            request (ProposePartnershipRequest): Type, values, ceiling and the proposer's subset.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.

        Raises:
            MeetingNotCompletedError: Before both parties recorded a completed meeting.
            EntityRequiredError: For equity without an identified legal entity (AC21).
            ConflictError: When the pitch already has a relationship.
        """
        check_context(principal, request.acting_party_id)
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        self._can(principal)
        if record.status != "APPROVED_FOR_DISCUSSION":
            raise InvalidTransitionError()
        if not await meeting_completed(self.session, record.id):
            raise MeetingNotCompletedError()
        snapshot = await latest_snapshot(self.session, record.id)
        # Only a raise for a company that already exists has an identified entity (AC21).
        if request.type == "EQUITY" and (snapshot.get("source") or {}).get("subject_type") != "EXISTING_ENTITY":
            raise EntityRequiredError()
        if await self.repository.of_pitches([record.id]):
            raise ConflictError()
        values = self._values(request.type, request.values)
        inventions = await invention_ids_of(
            self.session, [UUID(item["version_id"]) for item in snapshot.get("inventions", [])]
        )
        partnership = await self.repository.add(
            PartnershipRecord(
                pitch_id=record.id,
                type=request.type,
                requester_party_id=record.requester_party_id,
                recipient_party_id=record.recipient_party_id,
                invention_ids=[str(invention) for invention in inventions],
            )
        )
        ceiling = list(dict.fromkeys(request.ceiling))
        version = await self._version(partnership, 1, values, ceiling, principal, "")
        await self._confirm(version, principal, request.subset)
        await self._event(principal, partnership, "partnership.proposed", version.number)
        return await self.read_record(principal, partnership, operation_id)

    async def _version(
        self,
        partnership: PartnershipRecord,
        number: int,
        values: dict[str, Any],
        ceiling: list[str],
        principal: Principal,
        note: str,
    ) -> PartnershipVersionRecord:
        return await self.repository.add(
            PartnershipVersionRecord(
                partnership_id=partnership.id,
                number=number,
                values=values,
                ceiling=ceiling,
                checksum=checksum(partnership.type, number, values, ceiling),
                proposed_by_party_id=principal.active_party_id,
                note=note,
            )
        )

    async def _confirm(self, version: PartnershipVersionRecord, principal: Principal, subset: list[str]) -> None:
        await self.repository.add(
            PartnershipConfirmationRecord(
                version_id=version.id,
                party_id=principal.active_party_id,
                subset=[field for field in dict.fromkeys(subset) if field in version.ceiling],
                checksum=version.checksum,
                confirmed_by_account_id=principal.account_id,
            )
        )

    async def _event(self, principal: Principal, partnership: PartnershipRecord, topic: str, number: int) -> None:
        await publish(
            self.session,
            topic,
            {
                "pitch_id": str(partnership.pitch_id),
                "partnership_id": str(partnership.id),
                "actor_party_id": str(principal.active_party_id),
                "version": f"{partnership.id}:{number}",
            },
        )
        await record_audit(
            self.session,
            action=topic,
            subject_type="partnership",
            subject_id=str(partnership.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )

    async def _owned(
        self, principal: Principal, partnership_id: UUID, acting_party_id: UUID
    ) -> tuple[PartnershipRecord, PartnershipVersionRecord]:
        check_context(principal, acting_party_id)
        partnership = await self.repository.find(partnership_id, lock=True)
        parties = (partnership.requester_party_id, partnership.recipient_party_id) if partnership else ()
        if partnership is None or principal.active_party_id not in parties:
            raise NotFoundError()
        self._can(principal)
        current = (await self.repository.versions([partnership.id]))[-1]
        return partnership, current

    @staticmethod
    def _current(current: PartnershipVersionRecord, version: int) -> None:
        if current.number != version:
            raise StaleVersionError(current.number)

    async def correct(
        self, principal: Principal, partnership_id: UUID, request: CorrectionRequest, operation_id: UUID | None = None
    ) -> PartnershipResponse:
        """Start the next version with no confirmations; a pending one becomes ``CHANGES_REQUESTED`` (AC53).

        A confirmed version stays effective until both confirm the new one.

        Args:
            principal (Principal): Who is signed in.
            partnership_id (UUID): The relationship.
            request (CorrectionRequest): The version corrected, the new values, ceiling and a note.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.
        """
        partnership, current = await self._owned(principal, partnership_id, request.acting_party_id)
        self._current(current, request.version)
        if current.status not in ("PENDING_COUNTERPARTY", "CONFIRMED"):
            raise InvalidTransitionError()
        values = self._values(partnership.type, request.values)
        if current.status == "PENDING_COUNTERPARTY":
            current.status = "CHANGES_REQUESTED"
        ceiling = list(dict.fromkeys(request.ceiling)) if request.ceiling else current.ceiling
        version = await self._version(partnership, current.number + 1, values, ceiling, principal, request.note)
        partnership.version += 1
        await self._event(principal, partnership, "partnership.corrected", version.number)
        return await self.read_record(principal, partnership, operation_id)

    async def confirm(
        self, principal: Principal, partnership_id: UUID, request: ConfirmRequest, operation_id: UUID | None = None
    ) -> PartnershipResponse:
        """Confirm the current version by its checksum; both parties confirming makes it ``CONFIRMED`` (AC52).

        Args:
            principal (Principal): Who is signed in.
            partnership_id (UUID): The relationship.
            request (ConfirmRequest): Version, checksum and public subset.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.

        Raises:
            StaleVersionError: For another version or checksum; an old confirmation never confirms a new version.
            InvalidTransitionError: When the version is not pending, or this party already confirmed it.
        """
        partnership, current = await self._owned(principal, partnership_id, request.acting_party_id)
        self._current(current, request.version)
        if request.checksum != current.checksum:
            raise StaleVersionError(current.number)
        confirmations = await self.repository.confirmations([current.id])
        if current.status != "PENDING_COUNTERPARTY" or any(
            item.party_id == principal.active_party_id for item in confirmations
        ):
            raise InvalidTransitionError()
        await self._confirm(current, principal, request.subset)
        if len(confirmations) + 1 == 2:
            current.status = "CONFIRMED"
            await self._event(principal, partnership, "partnership.confirmed", current.number)
        partnership.version += 1
        await self.session.flush()
        return await self.read_record(principal, partnership, operation_id)

    async def decline(
        self,
        principal: Principal,
        partnership_id: UUID,
        request: VersionedPartnershipRequest,
        operation_id: UUID | None = None,
    ) -> PartnershipResponse:
        """Decline the pending version.

        Args:
            principal (Principal): Who is signed in.
            partnership_id (UUID): The relationship.
            request (VersionedPartnershipRequest): The version.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.
        """
        partnership, current = await self._owned(principal, partnership_id, request.acting_party_id)
        self._current(current, request.version)
        if current.status != "PENDING_COUNTERPARTY":
            raise InvalidTransitionError()
        current.status = "DECLINED"
        partnership.version += 1
        await self.session.flush()
        return await self.read_record(principal, partnership, operation_id)

    async def restrict(
        self, principal: Principal, partnership_id: UUID, request: RestrictRequest, operation_id: UUID | None = None
    ) -> PartnershipResponse:
        """Hide one public field at once. Append-only: history and confirmations stay as they were.

        Args:
            principal (Principal): Who is signed in.
            partnership_id (UUID): The relationship.
            request (RestrictRequest): The field.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.
        """
        partnership, _ = await self._owned(principal, partnership_id, request.acting_party_id)
        await self.repository.add(
            PartnershipRestrictionRecord(
                partnership_id=partnership.id,
                field=request.field,
                party_id=principal.active_party_id,
                restricted_by_account_id=principal.account_id,
            )
        )
        partnership.version += 1
        await self.session.flush()
        return await self.read_record(principal, partnership, operation_id)

    async def request_review(
        self, principal: Principal, partnership_id: UUID, request: ReviewRequest, operation_id: UUID | None = None
    ) -> PartnershipResponse:
        """Contest the public claim; the public projection hides it while private history stays.

        Args:
            principal (Principal): Who is signed in.
            partnership_id (UUID): The relationship.
            request (ReviewRequest): A reason.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.
        """
        partnership, _ = await self._owned(principal, partnership_id, request.acting_party_id)
        partnership.contested = True
        partnership.version += 1
        await self.session.flush()
        await record_audit(
            self.session,
            action="partnership.contested",
            subject_type="partnership",
            subject_id=str(partnership.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return await self.read_record(principal, partnership, operation_id)

    async def read(self, principal: Principal, partnership_id: UUID) -> PartnershipResponse:
        """Read a relationship as one of its two parties.

        Args:
            principal (Principal): Who is signed in.
            partnership_id (UUID): The relationship.

        Returns:
            PartnershipResponse: The relationship.

        Raises:
            NotFoundError: For anyone else.
        """
        partnership = await self.repository.find(partnership_id)
        parties = (partnership.requester_party_id, partnership.recipient_party_id) if partnership else ()
        if partnership is None or principal.active_party_id not in parties:
            raise NotFoundError()
        return await self.read_record(principal, partnership)

    async def of_pitch(self, principal: Principal, pitch_id: UUID) -> PartnershipResponse | None:
        """Read the relationship of a pitch, if any.

        Args:
            principal (Principal): Who is signed in.
            pitch_id (UUID): The pitch.

        Returns:
            PartnershipResponse | None: The relationship, or None before one is proposed.
        """
        record, _ = await visible_pitch(self.session, principal, pitch_id)
        found = await self.repository.of_pitches([record.id])
        return await self.read_record(principal, found[0]) if found else None

    async def effective(self, partnership: PartnershipRecord) -> EffectiveResponse:
        """Compute what may be public now (FR-002).

        Args:
            partnership (PartnershipRecord): The relationship.

        Returns:
            EffectiveResponse: The newest version both confirmed, its public fields and values.
        """
        versions = await self.repository.versions([partnership.id])
        confirmed = [version for version in versions if version.status == "CONFIRMED"]
        if not confirmed:
            return EffectiveResponse(version=None, fields=[], values={})
        version = confirmed[-1]
        subsets = [item.subset for item in await self.repository.confirmations([version.id])]
        restricted = {item.field for item in await self.repository.restrictions([partnership.id])}
        fields = effective_fields(version.ceiling, subsets, restricted)
        return EffectiveResponse(
            version=version.number, fields=fields, values=public_values(partnership.type, version.values, fields)
        )

    async def read_record(
        self, principal: Principal, partnership: PartnershipRecord, operation_id: UUID | None = None
    ) -> PartnershipResponse:
        """Build the parties' view.

        Args:
            principal (Principal): Who is signed in.
            partnership (PartnershipRecord): The relationship.
            operation_id (UUID | None, optional): For the response. Defaults to None.

        Returns:
            PartnershipResponse: The relationship.
        """
        versions = await self.repository.versions([partnership.id])
        by_version: dict[UUID, list[PartnershipConfirmationRecord]] = defaultdict(list)
        for item in await self.repository.confirmations([version.id for version in versions]):
            by_version[item.version_id].append(item)
        parties = [partnership.requester_party_id, partnership.recipient_party_id]
        names = await party_names(self.session, parties)
        views = [
            PartnershipVersionResponse(
                number=version.number,
                status=version.status,  # type: ignore[arg-type]
                values=version.values,
                ceiling=version.ceiling,
                checksum=version.checksum,
                proposed_by_party_id=version.proposed_by_party_id,
                note=version.note,
                created_at=version.created_at,
                confirmations=[
                    ConfirmationResponse(party_id=item.party_id, subset=item.subset, confirmed_at=item.created_at)
                    for item in by_version[version.id]
                ],
            )
            for version in versions
        ]
        current = views[-1]
        confirmed_by_me = any(item.party_id == principal.active_party_id for item in current.confirmations)
        allowed: list[str] = []
        if Capability.CONFIRM_RELATIONSHIP in principal.capabilities:
            if current.status == "PENDING_COUNTERPARTY" and not confirmed_by_me:
                allowed += ["confirm", "decline"]
            if current.status in ("PENDING_COUNTERPARTY", "CONFIRMED"):
                allowed.append("correct")
            if any(view.status == "CONFIRMED" for view in views):
                allowed += ["restrict", "request_review"]
        return PartnershipResponse(
            id=partnership.id,
            pitch_id=partnership.pitch_id,
            type=partnership.type,  # type: ignore[arg-type]
            parties=[PartyName(party_id=party, name=names.get(party, "")) for party in parties],
            invention_ids=[UUID(item) for item in partnership.invention_ids],
            contested=partnership.contested,
            current=current,
            versions=views,
            restrictions=[
                RestrictionResponse(field=item.field, party_id=item.party_id, created_at=item.created_at)
                for item in await self.repository.restrictions([partnership.id])
            ],
            effective=await self.effective(partnership),
            allowed_actions=allowed,
            operation_id=operation_id,
        )
