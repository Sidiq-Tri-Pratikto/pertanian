"""Seed and reset the labelled demo scenario, written through the domain services so it obeys the same rules as real
data (spec 021, FR-001). Ids are seeded, so a reset recreates the same ids and versions.

The reset is the scenario's starting point (``app/demo/service/scenario.py``): Inovator A with Produk A, Investor A
with one open opportunity, and Investor B as an empty account for the presenter to fill in.
"""

import struct
import zlib
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.service import capabilities_for
from app.core.database import seeded_ids
from app.core.settings import Settings
from app.demo.repository.sqlalchemy.repository import SqlAlchemyDemoRepository
from app.demo.service import scenario
from app.discovery.repository.sqlalchemy.repository import SqlAlchemyDiscoveryRepository
from app.discovery.service.projection import refresh_invention, refresh_partner
from app.documents.model.schema import UploadIntentRequest
from app.documents.service import jobs as document_jobs
from app.documents.service.service import DocumentService, document_version_number
from app.identity.model.models import Principal
from app.identity.service.service import create_demo_account
from app.intake.model.schema import CreateOpportunityRequest, OpportunityTransitionRequest, SavePartnerProfileRequest
from app.intake.service.service import IntakeService
from app.needs.model.schema import CreateSupportRequest, TransitionRequest
from app.needs.service.service import NeedsService
from app.portfolio.model.schema import (
    CreateInventionRequest,
    DraftRequest,
    InvestorDigestRequest,
    PublicPageRequest,
    PublicPhotoChoice,
    UpdateRequest,
    VersionedActionRequest,
)
from app.portfolio.service.service import PortfolioService
from app.portfolio.service.updates import UpdateService

DEMO_EMAIL_DOMAIN = "demo.invalid"
DEMO_LABEL = "Akun demo · data fiktif"


def demo_accounts() -> list[dict[str, str]]:
    """List the demo picker's accounts in a stable order.

    Returns:
        list[dict[str, str]]: Key, name, persona, the fixture it holds, what a visitor can try, and the label.
    """
    return [{**account, "label": DEMO_LABEL} for account in scenario.ACCOUNTS]


def demo_email(key: str) -> str:
    """The reserved address of a demo account; ``.invalid`` can never receive mail.

    Args:
        key (str): Account key, such as ``inovator-a``.

    Returns:
        str: The address.
    """
    return f"{key}@{DEMO_EMAIL_DOMAIN}"


def _illustration(
    dark: tuple[int, int, int], light: tuple[int, int, int], width: int = 960, height: int = 640
) -> bytes:
    """A plain PNG illustration: a vertical gradient with a lighter block, so the demo photo needs no file."""
    rows = []
    for y in range(height):
        shade = y / (height - 1)
        background = bytes(round(dark[i] + (light[i] - dark[i]) * shade * 0.35) for i in range(3))
        row = bytearray(background * width)
        if height * 0.3 <= y <= height * 0.75:
            left, right = int(width * 0.35), int(width * 0.65)
            row[left * 3 : right * 3] = bytes(light) * (right - left)
        rows.append(b"\x00" + bytes(row))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )


class DemoSeeder:
    """Writes the scenario's starting point through the services, as each demo account would."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind to a transaction.

        Args:
            session (AsyncSession): One transaction for the whole seed.
            settings (Settings): Settings.
        """
        self.session = session
        self.settings = settings

    async def _account(self, account: dict[str, str]) -> Principal:
        account_id, party_id = await create_demo_account(
            self.session,
            email=demo_email(account["key"]),
            display_name=account["name"],
            persona=account["persona"],
            time_zone="Asia/Jakarta",
        )
        return Principal(
            account_id=account_id,
            session_id=uuid4(),
            personal_party_id=party_id,
            active_party_id=party_id,
            capabilities=await capabilities_for(self.session, account_id, party_id) or frozenset(),
        )

    async def _photo(self, principal: Principal, title: str, image: bytes) -> tuple[UUID, int]:
        documents = DocumentService(self.session, self.settings)
        intent = await documents.create_intent(
            principal,
            UploadIntentRequest(
                acting_party_id=principal.active_party_id,
                title=title,
                kind="evidence",
                media_type="image/png",
                size_bytes=len(image),
            ),
        )

        async def body() -> Any:  # noqa: ANN401 - an async byte stream
            yield image

        uploaded = await documents.receive(principal, intent.intent_id, body())
        await document_jobs.scan(self.session, {"version_id": str(uploaded.version_id)})
        found = await document_version_number(self.session, uploaded.version_id)
        if found is None:  # the seed just stored it; nothing else can remove it in this transaction
            raise LookupError(uploaded.version_id)
        return found

    async def _product(self, principal: Principal, product: dict[str, Any]) -> UUID:
        """Publish an invention with its need, its public page, an illustration and its updates."""
        party = principal.active_party_id
        portfolio = PortfolioService(self.session)
        created = await portfolio.create(principal, CreateInventionRequest(acting_party_id=party))
        saved = await portfolio.save_draft(
            principal,
            created.id,
            DraftRequest(acting_party_id=party, expected_version=created.version, **product["content"]),
        )
        await portfolio.publish(
            principal, created.id, VersionedActionRequest(acting_party_id=party, expected_version=saved.version)
        )
        # Included in investor news too, so the quick subscription (046) can be shown.
        current = await portfolio.owner_view(principal, created.id)
        await portfolio.set_investor_digest(
            principal,
            created.id,
            InvestorDigestRequest(acting_party_id=party, expected_version=current.version, enabled=True),
        )
        page = product["public_page"]
        document_id, number = await self._photo(
            principal, page["photo"]["title"], _illustration(*page["photo"]["colors"])
        )
        current = await portfolio.owner_view(principal, created.id)
        await portfolio.set_public_page(
            principal,
            created.id,
            PublicPageRequest(
                acting_party_id=party,
                expected_version=current.version,
                enabled=True,
                field_test=page["field_test"],
                photo=PublicPhotoChoice(document_id=document_id, version=number),
                photo_alt=page["photo_alt"],
            ),
        )
        updates = UpdateService(self.session)
        for title, text in page["updates"]:
            written = await updates.create(
                principal, created.id, UpdateRequest(acting_party_id=party, title=title, body=text)
            )
            await updates.publish(
                principal,
                created.id,
                written.id,
                VersionedActionRequest(acting_party_id=party, expected_version=written.version),
            )
        needs = NeedsService(self.session)
        need = await needs.create(
            principal, CreateSupportRequest(acting_party_id=party, invention_id=created.id, **product["need"])
        )
        await needs.transition(
            principal, need.id, "activate", TransitionRequest(acting_party_id=party, expected_version=need.version)
        )
        return created.id

    async def _investor(self, principal: Principal, investor: dict[str, Any]) -> None:
        """Save the investor's profile and open its opportunity."""
        party = principal.active_party_id
        intake = IntakeService(self.session)
        await intake.save_profile(
            principal,
            party,
            SavePartnerProfileRequest(acting_party_id=party, expected_version=None, **investor["profile"]),
        )
        created = await intake.create(
            principal, CreateOpportunityRequest(acting_party_id=party, **investor["opportunity"])
        )
        await intake.transition(
            principal,
            created.id,
            "activate",
            OpportunityTransitionRequest(acting_party_id=party, expected_version=created.version),
        )

    async def seed(self) -> dict[str, UUID]:
        """Write the scenario's starting point with seeded ids, then project it for discovery.

        Returns:
            dict[str, UUID]: Produk A's invention id, and Investor A's party id.
        """
        inventor_a, investor_a, investor_b = scenario.ACCOUNTS
        with seeded_ids("demo"):
            inventor = await self._account(inventor_a)
            product_a = await self._product(inventor, scenario.PRODUCT_A)
            investor = await self._account(investor_a)
            await self._investor(investor, scenario.INVESTOR_A)
            # Investor B starts empty: scenario 1 fills it in live.
            await self._account(investor_b)
        # The worker would project these from the outbox; doing it now makes the demo searchable at once.
        await refresh_invention(self.session, product_a)
        await refresh_partner(self.session, investor.active_party_id)
        return {"product_a": product_a, "investor_a": investor.active_party_id}


async def reset(session: AsyncSession, settings: Settings) -> dict[str, UUID]:
    """Remove every demo row and seed the scenario's starting point again; real accounts are untouched.

    Args:
        session (AsyncSession): One transaction for the whole reset.
        settings (Settings): Settings.

    Returns:
        dict[str, UUID]: Produk A's invention id, and Investor A's party id.
    """
    await SqlAlchemyDiscoveryRepository(session).lock_updates(exclusive=True)
    await SqlAlchemyDemoRepository(session).remove_namespace()
    await session.flush()
    return await DemoSeeder(session, settings).seed()
