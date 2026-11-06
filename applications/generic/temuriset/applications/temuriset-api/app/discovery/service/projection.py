"""Keep ``search_documents`` equal to what owners published. Each consumer re-reads the subject through its module's
service and writes or removes its row, so a retried or late event can never resurrect what was withdrawn."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors.base import NotFoundError
from app.discovery.repository.sqlalchemy.repository import SqlAlchemyDiscoveryRepository
from app.funding.service.service import FundingService
from app.intake.service.service import IntakeService
from app.portfolio.service.service import PortfolioService
from app.worker.registry import registry

CONSUMER = "discovery-projection"


def _text(*parts: Any) -> str:
    return " ".join(str(part) for part in parts if part)


async def refresh_invention(session: AsyncSession, invention_id: UUID) -> None:
    """Project an invention's published version, or remove it when unpublished or archived.

    Args:
        session (AsyncSession): The worker's session.
        invention_id (UUID): The invention.
    """
    repository = SqlAlchemyDiscoveryRepository(session)
    try:
        view = await PortfolioService(session).public_view(invention_id)
    except NotFoundError:
        await repository.remove("INVENTION", invention_id)
        return
    await repository.upsert(
        subject_type="INVENTION",
        subject_id=invention_id,
        version_id=None,
        owner_party_id=view.managing_party_id,
        title=view.title,
        # Only published fields: never private notes, documents or claims' sources.
        body=_text(view.summary, view.problem, view.solution, view.intended_users, view.sector, *view.keywords),
        filters={"sectors": [view.sector] if view.sector else [], "stages": [view.stage] if view.stage else []},
        card={
            "number": view.number,
            "summary": view.summary,
            "sector": view.sector,
            "stage": view.stage,
            "keywords": view.keywords,
            "managing_party_name": view.managing_party_name,
        },
        published_at=view.published_at,
    )


async def refresh_funding(session: AsyncSession, request_id: UUID) -> None:
    """Project an active raise as one card, or remove it when it is not active.

    Args:
        session (AsyncSession): The worker's session.
        request_id (UUID): The raise.
    """
    repository = SqlAlchemyDiscoveryRepository(session)
    published = await FundingService(session).published(request_id)
    if published is None:
        await repository.remove("FUNDING_REQUEST", request_id)
        return
    owner, view = published
    portfolio = PortfolioService(session)
    inventions, sectors, stages, words = [], set(), set(), []
    for link in view.inventions:
        try:
            invention = await portfolio.public_view(link.invention_id)
        except NotFoundError:
            continue
        inventions.append({"invention_id": str(link.invention_id), "title": invention.title, "version": link.version})
        sectors.update([invention.sector] if invention.sector else [])
        stages.update([invention.stage] if invention.stage else [])
        words.extend([invention.title, *invention.keywords])
    await repository.upsert(
        subject_type="FUNDING_REQUEST",
        subject_id=request_id,
        version_id=None,
        owner_party_id=owner,
        title=view.subject_label,
        body=_text(view.intended_use, view.financing_stage, view.financing_form, *words),
        filters={
            "sectors": sorted(sectors),
            "stages": sorted(stages),
            "relationship_forms": ["EQUITY"] if view.financing_form == "equity" else [],
            "currency": view.currency,
            "basis": "per_investment",
            "amount_min": view.desired_min,
            "amount_max": view.desired_max,
        },
        card={
            "version": view.version,
            "subject_label": view.subject_label,
            "financing_stage": view.financing_stage,
            "financing_form": view.financing_form,
            "currency": view.currency,
            "target_amount": view.target_amount,
            "desired_min": view.desired_min,
            "desired_max": view.desired_max,
            "intended_use": view.intended_use,
            "inventions": inventions,
        },
        published_at=None,
    )


async def refresh_partner(session: AsyncSession, party_id: UUID) -> None:
    """Project a partner profile with its active opportunities, or remove it when there is no profile.

    Args:
        session (AsyncSession): The worker's session.
        party_id (UUID): The partner.
    """
    repository = SqlAlchemyDiscoveryRepository(session)
    intake = IntakeService(session)
    try:
        profile = await intake.read_profile(party_id)
    except NotFoundError:
        await repository.remove("PARTNER", party_id)
        return
    opportunities = await intake.published_opportunities(party_id)
    check = profile.check_range
    await repository.upsert(
        subject_type="PARTNER",
        subject_id=party_id,
        version_id=None,
        owner_party_id=party_id,
        title=profile.party_name,
        body=_text(
            profile.subtype,
            profile.thesis,
            *profile.support_forms,
            *profile.sectors,
            *(_text(item.title, item.outcome, item.support, *item.keywords) for item in opportunities),
        ),
        filters={
            "sectors": sorted({*profile.sectors, *(sector for item in opportunities for sector in item.sectors)}),
            "stages": sorted({*profile.stages, *(stage for item in opportunities for stage in item.accepted_stages)}),
            "regions": profile.regions,
            "support_forms": profile.support_forms,
            "relationship_forms": sorted(
                {*profile.relationship_forms, *(form for item in opportunities for form in item.relationship_forms)}
            ),
            "intake": profile.availability.current_intake_status,
            "currency": check.currency if check else None,
            "basis": check.basis if check else None,
            "amount_min": check.min if check else None,
            "amount_max": check.max if check else None,
        },
        card={
            "version": profile.version,
            "subtype": profile.subtype,
            "thesis": profile.thesis,
            "sectors": profile.sectors,
            "support_forms": profile.support_forms,
            "source_label": profile.availability.source_label,
            "availability_label": profile.availability.label,
            "contact_route": profile.contact_route,
            "external_url": profile.external_url if profile.contact_route == "EXTERNAL" else None,
            "check_range": check.model_dump() if check else None,
            "opportunities": [
                {"id": str(item.id), "title": item.title, "support": item.support} for item in opportunities
            ],
        },
        published_at=None,
    )


@registry.consumer("invention.published", CONSUMER)
@registry.consumer("invention.archived", CONSUMER)
async def on_invention(session: AsyncSession, payload: dict[str, Any]) -> None:
    """Refresh an invention."""
    await refresh_invention(session, UUID(payload["invention_id"]))


@registry.consumer("funding_request.changed", CONSUMER)
async def on_funding(session: AsyncSession, payload: dict[str, Any]) -> None:
    """Refresh a raise."""
    await refresh_funding(session, UUID(payload["funding_request_id"]))


@registry.consumer("partner.changed", CONSUMER)
async def on_partner(session: AsyncSession, payload: dict[str, Any]) -> None:
    """Refresh a partner."""
    await refresh_partner(session, UUID(payload["party_id"]))


@registry.consumer("opportunity.changed", CONSUMER)
async def on_opportunity(session: AsyncSession, payload: dict[str, Any]) -> None:
    """Refresh the partner whose opportunities changed."""
    party_id = await IntakeService(session).partner_of(UUID(payload["opportunity_id"]))
    if party_id is not None:
        await refresh_partner(session, party_id)
