"""Read-only fit matrix across an inventor's published products and active mandates (spec 059)."""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context
from app.access.service.service import party_names
from app.capabilities.service.service import select_capabilities
from app.core.errors.base import FieldsInvalidError
from app.core.settings import get_settings
from app.funding.service.service import FundingService
from app.identity.model.models import Principal
from app.intake.service.service import IntakeService
from app.matching.engine.evaluate import evaluate
from app.matching.engine.inputs import Source
from app.matching.engine.recommend import recommend
from app.matching.model.schema import (
    FitInvention,
    FitItem,
    FitOpportunity,
    FitResponse,
    MatchResultResponse,
    MatchSource,
    PartnerBestFit,
)
from app.matching.service.service import MatchingService, preview_source, target_of
from app.moderation.service.suspension import ListingSuspendedError, is_suspended
from app.needs.service.service import NeedsService
from app.portfolio.service.service import PortfolioService

MAX_INVENTIONS = 50
MAX_MANDATES = 200
MAX_PAIRS = MAX_INVENTIONS * MAX_MANDATES

_ELIGIBILITY_ORDER = {"ELIGIBLE": 0, "NEEDS_VERIFICATION": 1, "INCOMPATIBLE": 2}
_POSITIVE_LABELS = {"Kecocokan kuat", "Kecocokan potensial"}


def _item_sort_key(item: FitItem) -> tuple[int, int, int, Decimal, Decimal, str, str]:
    res = item.result
    incompatible = 1 if res.eligibility == "INCOMPATIBLE" else 0
    not_ready = 0 if (res.readiness == "READY_TO_SUBMIT" and not item.preview) else 1
    return (
        incompatible,
        _ELIGIBILITY_ORDER[res.eligibility],
        not_ready,
        -Decimal(res.fit.lower),
        -Decimal(res.fit.coverage),
        item.invention.title.casefold(),
        item.opportunity.title.casefold(),
    )


def _best_sort_key(item: FitItem) -> tuple[int, int, Decimal, Decimal, str]:
    res = item.result
    incompatible = 1 if res.eligibility == "INCOMPATIBLE" else 0
    irrelevant = 0 if res.relevant else 1
    return (
        incompatible,
        irrelevant,
        -Decimal(res.fit.lower),
        -Decimal(res.fit.coverage),
        item.invention.title.casefold(),
    )


class FitService:
    """Computes read-only fit for an inventor's own published products against active mandates (spec 059)."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request's database session."""
        self.session = session

    async def _build_sources(
        self, principal: Principal, invention_id: UUID | None
    ) -> list[tuple[FitInvention, Source, MatchSource | None, bool]]:
        portfolio = PortfolioService(self.session)
        mine = [item for item in await portfolio.list_mine(principal) if item.status == "PUBLISHED"]
        if invention_id is not None:
            mine = [item for item in mine if item.id == invention_id]
        if not mine:
            return []
        if len(mine) > MAX_INVENTIONS:
            raise FieldsInvalidError(
                [
                    {
                        "loc": ["query", "invention_id"],
                        "msg": "Terlalu banyak kombinasi; pilih satu produk atau satu investor.",
                        "type": "fit_bounds",
                    }
                ]
            )

        # Active support requests (newest first as list_mine orders them) per invention.
        needs = await NeedsService(self.session).list_mine(principal, None)
        need_by_invention: dict[UUID, Any] = {}
        for req in needs:
            if req.status == "ACTIVE" and req.invention_id not in need_by_invention:
                need_by_invention[req.invention_id] = req

        # Active company funding requests per linked invention (only when company_funding is enabled).
        raise_by_invention: dict[UUID, Any] = {}
        settings = get_settings()
        if "company_funding" in select_capabilities(settings.composition, settings.composition_overrides):
            raises = await FundingService(self.session).list_mine(principal)
            for req in raises:
                if req.status != "ACTIVE":
                    continue
                for link in req.inventions:
                    raise_by_invention.setdefault(link.invention_id, req)

        matching = MatchingService(self.session)
        built: list[tuple[FitInvention, Source, MatchSource | None, bool]] = []
        for summary in mine:
            if await is_suspended(self.session, "INVENTION", summary.id):
                continue
            detail = await portfolio.owner_view(principal, summary.id)
            pub = detail.published
            if pub is None:
                continue
            readiness = getattr(pub, "readiness", None)
            fit_inv = FitInvention(
                id=summary.id,
                title=pub.title,
                stage=pub.stage,
                tkt_level=readiness.tkt_level if readiness is not None else None,
            )
            active_need = need_by_invention.get(summary.id)
            active_raise = raise_by_invention.get(summary.id)
            try:
                if active_need is not None:
                    src, title, _ = await matching.source_of(principal, "SUPPORT_REQUEST", active_need.id)
                    built.append(
                        (
                            fit_inv,
                            src,
                            MatchSource(type="SUPPORT_REQUEST", id=active_need.id, version=src.version, title=title),
                            False,
                        )
                    )
                elif active_raise is not None:
                    src, title, _ = await matching.source_of(principal, "FUNDING_REQUEST", active_raise.id)
                    built.append(
                        (
                            fit_inv,
                            src,
                            MatchSource(type="FUNDING_REQUEST", id=active_raise.id, version=src.version, title=title),
                            False,
                        )
                    )
                else:
                    built.append((fit_inv, preview_source(pub, summary.id), None, True))
            except ListingSuspendedError:
                continue
        return built

    async def list(
        self,
        principal: Principal,
        *,
        acting_party_id: UUID | None = None,
        partner_party_id: UUID | None = None,
        invention_id: UUID | None = None,
        include_recommendations: bool = True,
    ) -> list[FitItem]:
        """Score the acting party's published inventions against active mandates, filtered optionally (FR-001).

        Args:
            principal (Principal): Signed-in actor.
            acting_party_id (UUID | None, optional): Optional acting party check. Defaults to None.
            partner_party_id (UUID | None, optional): Filter to one investor/partner. Defaults to None.
            invention_id (UUID | None, optional): Filter to one own product. Defaults to None.
            include_recommendations (bool, optional): Attach improvement recommendations. Defaults to True.

        Returns:
            list[FitItem]: Ordered fit items; never stored.
        """
        if acting_party_id is not None:
            check_context(principal, acting_party_id)
        sources = await self._build_sources(principal, invention_id)
        if not sources:
            return []
        opportunities = await IntakeService(self.session).active_targets(principal.active_party_id)
        if partner_party_id is not None:
            opportunities = [opp for opp in opportunities if opp.partner_party_id == partner_party_id]
        if not opportunities:
            return []
        if len(opportunities) > MAX_MANDATES or len(sources) * len(opportunities) > MAX_PAIRS:
            raise FieldsInvalidError(
                [
                    {
                        "loc": ["query", "partner_party_id"],
                        "msg": "Terlalu banyak kombinasi; pilih satu produk atau satu investor.",
                        "type": "fit_bounds",
                    }
                ]
            )

        names = await party_names(self.session, list({opp.partner_party_id for opp in opportunities}))
        targets = [target_of(opp, names.get(opp.partner_party_id, "")) for opp in opportunities]

        items: list[FitItem] = []
        for fit_inv, source, match_source, is_preview in sources:
            for tgt in targets:
                evaluated = evaluate(source, tgt)
                if include_recommendations:
                    evaluated["recommendations"] = recommend(source, tgt, evaluated, preview=is_preview)
                else:
                    evaluated["recommendations"] = []
                items.append(
                    FitItem(
                        invention=fit_inv,
                        source=match_source,
                        opportunity=FitOpportunity(
                            id=UUID(tgt.opportunity_id),
                            title=tgt.title,
                            partner_party_id=UUID(tgt.partner_party_id),
                            partner=tgt.partner_name,
                        ),
                        result=MatchResultResponse.model_validate(evaluated),
                        preview=is_preview,
                    )
                )
        items.sort(key=_item_sort_key)
        return items

    async def best_by_partner(
        self, principal: Principal, *, invention_id: UUID | None = None
    ) -> dict[UUID, PartnerBestFit]:
        """Compute each partner's best fit summary across one or all of the acting party's products (FR-004).

        Skips recommendation what-if expansion so partner list ordering stays fast.

        Args:
            principal (Principal): Signed-in actor.
            invention_id (UUID | None, optional): Specific product id, or None for all products.

        Returns:
            dict[UUID, PartnerBestFit]: Best fit keyed by partner party id.
        """
        items = await self.list(principal, invention_id=invention_id, include_recommendations=False)
        by_partner: dict[UUID, list[FitItem]] = {}
        for item in items:
            by_partner.setdefault(item.opportunity.partner_party_id, []).append(item)
        summary: dict[UUID, PartnerBestFit] = {}
        for partner_id, partner_items in by_partner.items():
            best = min(partner_items, key=_best_sort_key)
            matching_invs = {item.invention.id for item in partner_items if item.result.label in _POSITIVE_LABELS}
            summary[partner_id] = PartnerBestFit(
                label=best.result.label,
                eligibility=best.result.eligibility,
                fit=FitResponse(
                    lower=best.result.fit.lower,
                    upper=best.result.fit.upper,
                    coverage=best.result.fit.coverage,
                ),
                invention_id=best.invention.id,
                invention_title=best.invention.title,
                opportunity_id=best.opportunity.id,
                preview=best.preview,
                matching_products=len(matching_invs),
            )
        return summary
