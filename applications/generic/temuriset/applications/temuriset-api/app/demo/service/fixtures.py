"""Seed and reset the labelled demo: F01–F06, FRaise01 and Recipients A–E, written through the domain services so they
obey the same rules as real data (spec 021, FR-001). Ids are seeded, so a reset recreates the same ids and versions."""

import io
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from pypdf import PdfWriter
from sqlalchemy.ext.asyncio import AsyncSession

from app.access.model.schema import CreateOrganizationRequest
from app.access.service.service import AccessService, capabilities_for
from app.core.database import seeded_ids
from app.core.settings import Settings
from app.demo.repository.sqlalchemy.repository import SqlAlchemyDemoRepository
from app.demo.service import data
from app.discovery.service.projection import refresh_funding, refresh_invention, refresh_partner
from app.discovery.service.service import DiscoveryService
from app.documents.model.schema import UploadIntentRequest
from app.documents.service import jobs as document_jobs
from app.documents.service.service import DocumentService
from app.funding.model.schema import FundingRequestInput, LegalEntityInput
from app.funding.service.service import FundingService
from app.identity.model.models import Principal
from app.identity.service.service import create_demo_account
from app.intake.model.schema import (
    CreateOpportunityRequest,
    OpportunityTransitionRequest,
    PartnerProfileContent,
    SavePartnerProfileRequest,
)
from app.intake.service.service import IntakeService
from app.needs.model.schema import CreateSupportRequest, TransitionRequest
from app.needs.service.service import NeedsService
from app.portfolio.model.schema import CreateInventionRequest, DraftRequest, VersionedActionRequest
from app.portfolio.service.service import PortfolioService

DEMO_EMAIL_DOMAIN = "demo.invalid"
DEMO_LABEL = "Akun demo · data fiktif"


@dataclass(frozen=True)
class Variants:
    """Selectable fixture states (FR-003).

    Attributes:
        gap (bool): F01-GAP: F01's range is not filled in yet.
        scan (bool): F01-SCAN: F01's test report is a scan with no text.
        proposed_entity (bool): FRaise01 for a company not founded yet.
    """

    gap: bool = False
    scan: bool = False
    proposed_entity: bool = False


def demo_accounts() -> list[dict[str, str]]:
    """List the demo picker's accounts in a stable order.

    Returns:
        list[dict[str, str]]: Key, name, persona, the fixture it holds, and the label.
    """
    inventors = [
        {"key": key, "name": account["name"], "persona": "inovator", "fixture": data.INVENTOR_FIXTURES[key]}
        for key, account in data.ACCOUNTS.items()
    ]
    partners = [
        {"key": account["key"], "name": account["name"], "persona": "mitra", "fixture": f"Recipient {recipient}"}
        for recipient, account in data.RECIPIENT_ACCOUNTS.items()
    ]
    return [{**account, "label": DEMO_LABEL} for account in inventors + partners]


def demo_email(key: str) -> str:
    """The reserved address of a demo account; ``.invalid`` can never receive mail.

    Args:
        key (str): Account key, such as ``rani``.

    Returns:
        str: The address.
    """
    return f"{key}@{DEMO_EMAIL_DOMAIN}"


def _pdf(text: str | None) -> bytes:
    """A one-page PDF. With text it can be read; without, it reads like a scan, which needs a person to read it."""
    if text is None:
        writer, buffer = PdfWriter(), io.BytesIO()
        writer.add_blank_page(width=612, height=792)
        writer.write(buffer)
        return buffer.getvalue()
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


class DemoSeeder:
    """Writes the demo through the services, as each demo account would."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind to a transaction.

        Args:
            session (AsyncSession): One transaction for the whole seed.
            settings (Settings): Settings.
        """
        self.session = session
        self.settings = settings
        self.principals: dict[str, Principal] = {}

    async def _account(self, key: str, name: str, persona: str, zone: str, organization: str | None) -> Principal:
        account_id, party_id = await create_demo_account(
            self.session, email=demo_email(key), display_name=name, persona=persona, time_zone=zone
        )
        principal = Principal(
            account_id=account_id,
            session_id=uuid4(),
            personal_party_id=party_id,
            active_party_id=party_id,
            capabilities=await capabilities_for(self.session, account_id, party_id) or frozenset(),
        )
        if organization is not None:
            created = await AccessService(self.session, self.settings).create_organization(
                principal, CreateOrganizationRequest(name=organization, kind="company")
            )
            principal = Principal(
                account_id=account_id,
                session_id=principal.session_id,
                personal_party_id=party_id,
                active_party_id=created.party_id,
                capabilities=await capabilities_for(self.session, account_id, created.party_id) or frozenset(),
            )
        self.principals[key] = principal
        return principal

    async def _document(self, principal: Principal, title: str, scan: bool) -> UUID:
        documents = DocumentService(self.session, self.settings)
        content = _pdf(None if scan else title)
        intent = await documents.create_intent(
            principal,
            UploadIntentRequest(
                acting_party_id=principal.active_party_id,
                title=title,
                kind="evidence",
                media_type="application/pdf",
                size_bytes=len(content),
            ),
        )

        async def body() -> Any:  # noqa: ANN401 - an async byte stream
            yield content

        uploaded = await documents.receive(principal, intent.intent_id, body())
        version_id = uploaded.version_id
        await document_jobs.scan(self.session, {"version_id": str(version_id)})
        await document_jobs.extract(self.session, {"version_id": str(version_id)})
        return version_id

    async def _invention(self, key: str, variants: Variants) -> UUID:
        fixture = data.INVENTIONS[key]
        principal = self.principals[fixture["account"]]
        content = {**fixture["content"], "facts": [dict(fact) for fact in fixture["content"]["facts"]]}
        for fact in content["facts"]:
            if fact["key"] in fixture.get("documents", {}):
                fact["document_version_id"] = await self._document(
                    principal, fixture["documents"][fact["key"]], scan=variants.scan
                )
        portfolio = PortfolioService(self.session)
        party = principal.active_party_id
        created = await portfolio.create(principal, CreateInventionRequest(acting_party_id=party))
        saved = await portfolio.save_draft(
            principal,
            created.id,
            DraftRequest(acting_party_id=party, expected_version=created.version, **content),
        )
        await portfolio.publish(
            principal, created.id, VersionedActionRequest(acting_party_id=party, expected_version=saved.version)
        )
        return created.id

    async def _inventors(self, variants: Variants) -> dict[str, UUID]:
        for key, account in data.ACCOUNTS.items():
            zone = data.INVENTOR_ZONES.get(key, "Asia/Jakarta")
            await self._account(key, account["name"], "inovator", zone, account["organization"])
        inventions = {key: await self._invention(key, variants) for key in data.INVENTIONS}
        needs = NeedsService(self.session)
        for key, content in data.SUPPORT_REQUESTS.items():
            principal = self.principals[data.INVENTIONS[key]["account"]]
            party = principal.active_party_id
            budget = data.F01_GAP_BUDGET if key == "F01" and variants.gap else content["budget"]
            created = await needs.create(
                principal,
                CreateSupportRequest(
                    acting_party_id=party, invention_id=inventions[key], **{**content, "budget": budget}
                ),
            )
            await needs.transition(
                principal,
                created.id,
                "activate",
                TransitionRequest(acting_party_id=party, expected_version=created.version),
            )
        principal = self.principals["bima"]
        party = principal.active_party_id
        funding = FundingService(self.session)
        subject: dict[str, Any] = {"subject_type": "PROPOSED_ENTITY", "proposed_name": data.FRAISE01["entity"]["name"]}
        if not variants.proposed_entity:
            entity = await funding.declare_entity(
                principal, LegalEntityInput(acting_party_id=party, **data.FRAISE01["entity"])
            )
            subject = {"subject_type": "EXISTING_ENTITY", "legal_entity_id": entity.id}
        raise_ = await funding.create(
            principal,
            FundingRequestInput(
                acting_party_id=party,
                **subject,
                **data.FRAISE01["content"],
                invention_ids=[inventions[key] for key in data.FRAISE01["inventions"]],
            ),
        )
        await funding.transition(
            principal, raise_.id, "activate", TransitionRequest(acting_party_id=party, expected_version=raise_.version)
        )
        inventions["FRaise01"] = raise_.id
        return inventions

    async def _recipients(self) -> list[UUID]:
        intake = IntakeService(self.session)
        parties: dict[str, UUID] = {}
        for recipient, profile in data.PROFILES.items():
            account = data.RECIPIENT_ACCOUNTS[recipient]
            organization = profile["party"]["name"] if profile["party"]["kind"] == "organization" else None
            principal = await self._account(account["key"], account["name"], "mitra", account["zone"], organization)
            party = principal.active_party_id
            parties[recipient] = party
            content = PartnerProfileContent.model_validate(profile["content"])
            if recipient == "E":
                await intake.record_directory_profile(party, content)
            else:
                await intake.save_profile(
                    principal,
                    party,
                    SavePartnerProfileRequest(acting_party_id=party, expected_version=None, **profile["content"]),
                )
        for opportunity in data.OPPORTUNITIES.values():
            principal = self.principals[data.RECIPIENT_ACCOUNTS[opportunity["partner"]]["key"]]
            party = principal.active_party_id
            created = await intake.create(
                principal, CreateOpportunityRequest(acting_party_id=party, **opportunity["content"])
            )
            await intake.transition(
                principal,
                created.id,
                "activate",
                OpportunityTransitionRequest(acting_party_id=party, expected_version=created.version),
            )
        return list(parties.values())

    async def seed(self, variants: Variants) -> dict[str, UUID]:
        """Write the whole demo with seeded ids, then project it for discovery.

        Args:
            variants (Variants): Fixture states.

        Returns:
            dict[str, UUID]: Invention ids per fixture, and FRaise01's id.
        """
        with seeded_ids("demo"):
            subjects = await self._inventors(variants)
            partners = await self._recipients()
        # The worker would project these from the outbox; doing it now makes the demo searchable at once.
        for key in data.INVENTIONS:
            await refresh_invention(self.session, subjects[key])
        await refresh_funding(self.session, subjects["FRaise01"])
        for party in partners:
            await refresh_partner(self.session, party)
        for key, fixture in data.INVENTIONS.items():
            if fixture.get("curated"):
                await DiscoveryService(self.session).set_curated("INVENTION", subjects[key], True)
        return subjects


async def reset(session: AsyncSession, settings: Settings, variants: Variants | None = None) -> dict[str, UUID]:
    """Remove every demo row and seed the demo again; real accounts are untouched.

    Args:
        session (AsyncSession): One transaction for the whole reset.
        settings (Settings): Settings.
        variants (Variants | None, optional): Fixture states. Defaults to the baseline.

    Returns:
        dict[str, UUID]: Invention ids per fixture, and FRaise01's id.
    """
    await SqlAlchemyDemoRepository(session).remove_namespace()
    await session.flush()
    return await DemoSeeder(session, settings).seed(variants or Variants())
