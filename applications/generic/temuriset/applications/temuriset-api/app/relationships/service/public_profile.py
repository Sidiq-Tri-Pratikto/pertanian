"""Public profiles: a deliberately published biography, published inventions, and consented relationship fields."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.models import Capability
from app.access.service.policy import check_context, require
from app.access.service.service import find_party, party_names
from app.core.errors.base import NotFoundError
from app.identity.model.models import Principal
from app.platform.service.audit import record_audit
from app.platform.service.versions import check_expected
from app.portfolio.service.service import published_titles
from app.relationships.model.schema import (
    ProfileResponse,
    PublicInvention,
    PublicProfileResponse,
    PublicRelationship,
    SaveProfileRequest,
)
from app.relationships.repository.sqlalchemy.repository import SqlAlchemyRelationshipRepository
from app.relationships.service.service import RelationshipService

# The role a party holds in a relationship, by type and side; without "type" in public both read "Mitra Kerja Sama".
ROLE = {
    ("PROJECT", "requester"): "Penerima dukungan proyek",
    ("PROJECT", "recipient"): "Mitra proyek",
    ("LICENSE", "requester"): "Pemberi lisensi",
    ("LICENSE", "recipient"): "Pemegang lisensi",
    ("EQUITY", "requester"): "Perusahaan penerima investasi",
    ("EQUITY", "recipient"): "Investor",
}
MANAGER = "Pengelola inovasi"


class PublicProfileService:
    """The public read, with no cache, and the owner's publication settings."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session

    async def read(self, party_id: UUID) -> PublicProfileResponse:
        """Compute a party's public profile from current publication and consent state (FR-001, FR-002).

        A contested relationship is hidden (AC57); an equity relationship over two inventions appears once (AC56).

        Args:
            party_id (UUID): The party.

        Returns:
            PublicProfileResponse: What anyone may see.

        Raises:
            NotFoundError: For an unknown party.
        """
        party = await find_party(self.session, party_id)
        if party is None:
            raise NotFoundError()
        visible = []
        counterpart_ids: set[UUID] = set()
        partnerships = await SqlAlchemyRelationshipRepository(self.session).of_party(party_id)
        projections = await RelationshipService(self.session).effective_many(partnerships)
        for partnership in partnerships:
            effective = projections[partnership.id]
            if effective.version is None or not effective.values:
                continue
            side = "requester" if partnership.requester_party_id == party_id else "recipient"
            counterpart = None
            if "name" in effective.fields:
                counterpart = partnership.recipient_party_id if side == "requester" else partnership.requester_party_id
                counterpart_ids.add(counterpart)
            visible.append((partnership, effective, side, counterpart))

        names = await party_names(self.session, list(counterpart_ids))
        public = await published_titles(self.session, {party_id, *counterpart_ids})
        inventions = [
            PublicInvention(id=invention_id, title=title, role=MANAGER)
            for owner, invention_id, title in public
            if owner == party_id
        ]
        relationships = []
        for partnership, effective, side, counterpart in visible:
            linked = {UUID(item) for item in partnership.invention_ids}
            relationships.append(
                PublicRelationship(
                    id=partnership.id,
                    role=ROLE[(partnership.type, side)] if "type" in effective.fields else "Mitra Kerja Sama",
                    counterpart_party_id=counterpart,
                    counterpart_name=names.get(counterpart) if counterpart else None,
                    fields=effective.values,
                    inventions=[
                        PublicInvention(id=invention_id, title=title, role=MANAGER)
                        for owner, invention_id, title in public
                        if owner in (party_id, counterpart) and invention_id in linked
                    ],
                )
            )
        bio = party.bio if party.profile_published and party.bio else None
        return PublicProfileResponse(
            party_id=party.id,
            name=party.display_name,
            bio=bio,
            inventions=inventions,
            relationships=relationships,
            nothing_published=not (bio or inventions or relationships),
        )

    async def mine(self, principal: Principal) -> ProfileResponse:
        """Read the acting party's profile settings.

        Args:
            principal (Principal): Who is signed in.

        Returns:
            ProfileResponse: Bio, published flag and version.
        """
        party = await find_party(self.session, principal.active_party_id)
        assert party is not None  # noqa: S101 - the session's active party exists
        return ProfileResponse(
            party_id=party.id, bio=party.bio, published=party.profile_published, version=party.version
        )

    async def save(self, principal: Principal, request: SaveProfileRequest) -> ProfileResponse:
        """Publish, change or withdraw the acting party's biography.

        Args:
            principal (Principal): Who is signed in.
            request (SaveProfileRequest): Bio, published flag and ``expected_version``.

        Returns:
            ProfileResponse: The saved settings.
        """
        check_context(principal, request.acting_party_id)
        require(principal, Capability.EDIT_PORTFOLIO, principal.active_party_id)
        party = await find_party(self.session, principal.active_party_id, lock=True)
        assert party is not None  # noqa: S101 - the session's active party exists
        check_expected(party.version, request.expected_version)
        party.bio, party.profile_published = request.bio, request.published
        party.version += 1
        await self.session.flush()
        await record_audit(
            self.session,
            action="profile.saved",
            subject_type="party",
            subject_id=str(party.id),
            actor_account_id=principal.account_id,
            actor_party_id=principal.active_party_id,
        )
        return ProfileResponse(
            party_id=party.id, bio=party.bio, published=party.profile_published, version=party.version
        )
