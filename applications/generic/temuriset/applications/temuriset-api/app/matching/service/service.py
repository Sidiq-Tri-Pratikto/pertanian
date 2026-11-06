"""Run the engine on authorized projections and keep each run reproducible (spec 019)."""

from dataclasses import asdict
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access.service.policy import check_context
from app.access.service.service import party_names
from app.capabilities.service.guard import CapabilityUnavailableError
from app.capabilities.service.service import select_capabilities
from app.core.errors.base import NotFoundError
from app.core.settings import get_settings
from app.documents.service.service import evidence_results
from app.funding.service.service import FundingService
from app.identity.model.models import Principal
from app.intake.model.schema import OpportunityResponse
from app.intake.service.service import IntakeService
from app.matching.engine.evaluate import ENGINE, POLICY_VERSIONS, evaluate, rank
from app.matching.engine.inputs import Money, Source, Target
from app.matching.model.schema import MatchRequest, MatchResultResponse, MatchRunResponse, MatchSource
from app.matching.repository.sqlalchemy.models import MatchRunRecord
from app.matching.repository.sqlalchemy.repository import SqlAlchemyMatchingRepository
from app.needs.service.service import NeedsService
from app.portfolio.model.schema import InventionVersionResponse
from app.portfolio.service.service import version_view


def _decimal(text: str | None) -> Decimal | None:
    return None if text is None else Decimal(text)


def target_of(opportunity: OpportunityResponse, partner_name: str) -> Target:
    """Turn an opportunity as an applicant reads it into the engine's target.

    Args:
        opportunity (OpportunityResponse): The opportunity.
        partner_name (str): Its partner's name.

    Returns:
        Target: The engine input.
    """
    financial = opportunity.financial
    money = None
    if financial is not None:
        money = Money(
            low=_decimal(financial.min),
            high=_decimal(financial.max),
            currency=financial.currency,
            subject=financial.subject,
            basis=financial.basis,
            months=financial.months,
            scope=financial.scope,
        )
    return Target(
        opportunity_id=str(opportunity.id),
        version_id=str(opportunity.current_version_id),
        number=opportunity.number,
        partner_party_id=str(opportunity.partner_party_id),
        partner_name=partner_name,
        title=opportunity.title,
        active=opportunity.status == "ACTIVE",
        accepted_stages=tuple(opportunity.accepted_stages),
        sectors=tuple(opportunity.sectors),
        keywords=tuple(opportunity.keywords),
        relationship_forms=tuple(opportunity.relationship_forms),
        financial=money,
        requirements=tuple(
            {
                **row.model_dump(
                    include={
                        "label",
                        "field",
                        "operator",
                        "value",
                        "mandatory",
                        "applies_at",
                        "verification_mode",
                        "reason",
                    }
                ),
                "id": str(row.id),
            }
            for row in opportunity.requirements
        ),
        availability=opportunity.target_availability.model_dump(),
    )


async def _evidence(
    session: AsyncSession, owner: UUID, versions: list[InventionVersionResponse]
) -> dict[str, tuple[dict[str, str], ...]]:
    """Evaluate each fact's linked file, by fact key; another party's file counts as absent."""
    linked = [(fact.key, fact.document_version_id) for version in versions for fact in version.facts]
    linked = [(key, version_id) for key, version_id in linked if key and version_id]
    results = await evidence_results(session, owner, [version_id for _, version_id in linked])
    documents: dict[str, list[dict[str, str]]] = {}
    for key, version_id in linked:
        documents.setdefault(key, []).append(
            results.get(version_id, {"DOCUMENT_PRESENT": "UNKNOWN", "REVIEWER_CONFIRMED": "UNKNOWN"})
        )
    return {key: tuple(files) for key, files in documents.items()}


def _invention_fields(versions: list[InventionVersionResponse]) -> dict[str, Any]:
    first = versions[0] if versions else None
    return {
        "stage": first.stage if first else None,
        "sector": first.sector if first else "",
        "keywords": tuple(word for version in versions for word in version.keywords),
        "facts": tuple((fact.key, fact.timing) for version in versions for fact in version.facts if fact.key),
        "authority": tuple(
            claim.status for version in versions for claim in version.claims if claim.kind == "authority"
        ),
    }


class MatchingService:
    """Evaluates an owned source against every other partner's active opportunities."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind to the request.

        Args:
            session (AsyncSession): The request's session.
        """
        self.session = session
        self.repository = SqlAlchemyMatchingRepository(session)

    async def source_of(
        self, principal: Principal, source_type: str, source_id: UUID
    ) -> tuple[Source, str, list[UUID]]:
        """Build the engine's source from what the acting party owns.

        Args:
            principal (Principal): Who is signed in.
            source_type (str): ``SUPPORT_REQUEST`` or ``FUNDING_REQUEST``.
            source_id (UUID): The source.

        Returns:
            tuple[Source, str, list[UUID]]: The engine input, a title to show, and the invention versions it reads.

        Raises:
            NotFoundError: When the acting party does not own it.
            CapabilityUnavailableError: For a raise when company funding is off.
        """
        owner = principal.active_party_id
        if source_type == "SUPPORT_REQUEST":
            request, version_id = await NeedsService(self.session).source(principal, source_id)
            versions = [await version_view(self.session, version_id)]
            budget = request.budget
            money = None
            if budget is not None:
                money = Money(
                    low=_decimal(budget.min),
                    high=_decimal(budget.max),
                    currency=budget.currency,
                    basis=budget.basis,
                    months=request.months,
                    scope=budget.scope or request.scope,
                )
            source = Source(
                type=source_type,
                id=str(request.id),
                version=request.version,
                relationship=request.relationship_form,
                budget=money,
                accepts_partial=request.accepts_partial,
                documents=await _evidence(self.session, owner, versions),
                **_invention_fields(versions),
            )
            return source, request.invention_title, [version_id]
        settings = get_settings()
        if "company_funding" not in select_capabilities(settings.composition, settings.composition_overrides):
            raise CapabilityUnavailableError()
        raise_, version_ids = await FundingService(self.session).source(principal, source_id)
        versions = [await version_view(self.session, version_id) for version_id in version_ids]
        source = Source(
            type=source_type,
            id=str(raise_.id),
            version=raise_.version,
            relationship="EQUITY" if raise_.financing_form == "equity" else None,
            entity="IDENTIFIED" if raise_.subject_type == "EXISTING_ENTITY" else "PROPOSED",
            contribution=Money(
                low=_decimal(raise_.desired_min), high=_decimal(raise_.desired_max), currency=raise_.currency
            ),
            accepts_partial=raise_.accepts_partial,
            documents=await _evidence(self.session, owner, versions),
            **_invention_fields(versions),
        )
        return source, raise_.subject_label, version_ids

    async def run(self, principal: Principal, request: MatchRequest) -> MatchRunResponse:
        """Evaluate the source against each active opportunity separately, then order and persist the run.

        Args:
            principal (Principal): Who is signed in.
            request (MatchRequest): The source.

        Returns:
            MatchRunResponse: The stored run.
        """
        check_context(principal, request.acting_party_id)
        source, title, _ = await self.source_of(principal, request.source_type, request.source_id)
        opportunities = await IntakeService(self.session).active_targets(principal.active_party_id)
        names = await party_names(self.session, list({item.partner_party_id for item in opportunities}))
        results = [evaluate(source, target_of(item, names.get(item.partner_party_id, ""))) for item in opportunities]
        shown, excluded = rank(results)
        inputs = asdict(source)
        run = await self.repository.save_run(
            MatchRunRecord(
                actor_party_id=principal.active_party_id,
                source_type=source.type,
                source_id=request.source_id,
                source_version=source.version,
                source_title=title,
                engine=ENGINE,
                policy_versions=POLICY_VERSIONS,
                inputs={
                    **{key: value for key, value in inputs.items() if key not in ("budget", "contribution")},
                    "budget": _money_json(source.budget),
                    "contribution": _money_json(source.contribution),
                    "targets": [result["opportunity_version_id"] for result in results],
                },
            ),
            [(True, result) for result in shown] + [(False, result) for result in excluded],
        )
        return MatchRunResponse(
            run_id=run.id,
            created_at=run.created_at,
            engine=run.engine,
            policy_versions=run.policy_versions,
            source=MatchSource(type=source.type, id=request.source_id, version=source.version, title=title),  # type: ignore[arg-type]
            results=[MatchResultResponse.model_validate(result) for result in shown],
            excluded=[MatchResultResponse.model_validate(result) for result in excluded],
        )

    async def read(self, principal: Principal, run_id: UUID) -> MatchRunResponse:
        """Read a stored run of the acting party.

        Args:
            principal (Principal): Who is signed in.
            run_id (UUID): The run.

        Returns:
            MatchRunResponse: The run as it was computed.

        Raises:
            NotFoundError: When it is another party's run.
        """
        found = await self.repository.run(run_id)
        if found is None or found[0].actor_party_id != principal.active_party_id:
            raise NotFoundError()
        run, rows = found
        return MatchRunResponse(
            run_id=run.id,
            created_at=run.created_at,
            engine=run.engine,
            policy_versions=run.policy_versions,
            source=MatchSource(
                type=run.source_type,  # type: ignore[arg-type]
                id=run.source_id,
                version=run.source_version,
                title=run.source_title,
            ),
            results=[MatchResultResponse.model_validate(row.result) for row in rows if row.shown],
            excluded=[MatchResultResponse.model_validate(row.result) for row in rows if not row.shown],
        )


def _money_json(money: Money | None) -> dict[str, Any] | None:
    if money is None:
        return None
    return {
        **asdict(money),
        "low": None if money.low is None else str(money.low),
        "high": None if money.high is None else str(money.high),
    }
