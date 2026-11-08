"""Insights evaluated on read, published as immutable evidence revisions."""

from datetime import date, datetime
from uuid import UUID, uuid4

from app.assets.service.service import AssetService
from app.baseline.service.compare import ComparisonState
from app.baseline.service.service import BaselineService
from app.core.clock import wall_now
from app.core.errors.base import NotFoundError
from app.core.locale import locale, wants_bilingual_copy
from app.energy.service.periods import Window, resolve_window
from app.energy.service.summary import EnergyService, PeriodQuery, window_response
from app.identity.model.models import PrincipalModel
from app.insights.model.models import (
    POLICY_ID,
    POLICY_VERSION,
    Candidate,
    InsightModel,
    InsightRevisionModel,
)
from app.insights.model.schema import (
    FeedbackStateResponse,
    HiddenInsightsResponse,
    InsightCopyResponse,
    InsightListResponse,
    InsightResponse,
    PolicyResponse,
)
from app.insights.repository.base_repository import InsightRepository
from app.insights.service.copy import insight_copy
from app.insights.service.notices import notices
from app.insights.service.rules import direction, evidence, evidence_hash
from app.insights.service.visibility import VisibilityReader
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock
from app.sites.service.service import SiteService

KIND = "change"


def render(insight: InsightModel, revision: InsightRevisionModel) -> InsightResponse:
    """Render one revision with its copy.

    Args:
        insight (InsightModel): The insight.
        revision (InsightRevisionModel): The revision.

    Returns:
        InsightResponse: The response.
    """
    indonesian = InsightCopyResponse(**insight_copy(revision.evidence))
    english = InsightCopyResponse(**insight_copy(revision.evidence, "en")) if wants_bilingual_copy() else None
    return InsightResponse(
        id=insight.id,
        revision=revision.revision,
        current_revision=insight.current_revision,
        kind=insight.kind,
        direction=revision.evidence["direction"],
        asset_id=insight.asset_id,
        active=insight.active and revision.revision == insight.current_revision,
        superseded=revision.superseded_at is not None,
        generated_at=revision.generated_at,
        policy=PolicyResponse(id=revision.policy_id, version=revision.policy_version),
        evidence=revision.evidence,
        text=english if locale() == "en" and english is not None else indonesian,
        text_by_locale={"id": indonesian, "en": english} if english is not None else None,
    )


def _hidden(item: InsightResponse, now: datetime) -> bool:
    feedback = item.feedback
    if feedback is None:
        return False
    return feedback.visibility == "hidden" or (
        feedback.visibility == "snoozed" and feedback.until is not None and feedback.until > now
    )


class InsightService:
    """Deterministic rules over the matched baseline. Reads re-evaluate, so corrections publish on the next read."""

    def __init__(
        self,
        repository: InsightRepository,
        *,
        sites: SiteService,
        assets: AssetService,
        energy: EnergyService,
        baseline: BaselineService,
        visibility: VisibilityReader | None = None,
    ) -> None:
        """Bind to storage and the services evidence comes from.

        Args:
            repository (InsightRepository): Insight storage.
            sites (SiteService): Ownership and the site lock.
            assets (AssetService): Asset model.
            energy (EnergyService): Windows and summaries.
            baseline (BaselineService): Matched baseline.
            visibility (VisibilityReader | None, optional): The owner's feedback. Defaults to None.
        """
        self.repository = repository
        self.visibility = visibility
        self.sites = sites
        self.assets = assets
        self.energy = energy
        self.baseline = baseline

    async def site_insights(self, site_id: UUID, principal: PrincipalModel, query: PeriodQuery) -> InsightListResponse:
        """Evaluate and publish an owned site's period, then return its active observations and notices.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.
            query (PeriodQuery): The period.

        Returns:
            InsightListResponse: Ranked observations, notices and counts.
        """
        site = await self.sites.get_owned(site_id, principal)
        result = await self.evaluate(site, self.energy.window(site, query))
        observations = await self._with_feedback(principal, result.observations)
        visible = [item for item in observations if not _hidden(item, site_clock(site))]
        return result.model_copy(update={"observations": visible, "hidden_count": len(observations) - len(visible)})

    async def hidden_insights(
        self, site_id: UUID, principal: PrincipalModel, query: PeriodQuery
    ) -> HiddenInsightsResponse:
        """Return the observations the owner hid or snoozed for a period.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.
            query (PeriodQuery): The period.

        Returns:
            HiddenInsightsResponse: Hidden and snoozed observations.
        """
        site = await self.sites.get_owned(site_id, principal)
        result = await self.evaluate(site, self.energy.window(site, query))
        observations = await self._with_feedback(principal, result.observations)
        return HiddenInsightsResponse(
            window=result.window, observations=[item for item in observations if _hidden(item, site_clock(site))]
        )

    async def owned_revision(self, insight_id: UUID, principal: PrincipalModel, revision: int) -> SiteModel:
        """Confirm the principal owns the insight and the revision belongs to it.

        Args:
            insight_id (UUID): The insight.
            principal (PrincipalModel): The acting principal.
            revision (int): The revision.

        Returns:
            SiteModel: The insight's site.

        Raises:
            NotFoundError: When the insight, its site or the revision is not the principal's.
        """
        insight = await self.repository.get(insight_id)
        if insight is None:
            raise NotFoundError()
        site = await self.sites.get_owned(insight.site_id, principal)
        if await self.repository.revision(insight_id, revision) is None:
            raise NotFoundError()
        return site

    async def _with_feedback(self, principal: PrincipalModel, items: list[InsightResponse]) -> list[InsightResponse]:
        if self.visibility is None or not items:
            return items
        views = await self.visibility.feedback(principal.id, [item.id for item in items])
        result = []
        for item in items:
            mine = views.get(item.id, [])
            own = next((view for view in mine if view.revision == item.revision), None)
            result.append(
                item.model_copy(
                    update={
                        "feedback": FeedbackStateResponse(**own.model_dump(exclude={"revision"})) if own else None,
                        "earlier_feedback": any(view.revision < item.revision for view in mine),
                    }
                )
            )
        return result

    async def get(self, insight_id: UUID, principal: PrincipalModel, revision: int | None) -> InsightResponse:
        """Return an insight: a frozen revision when asked, otherwise its current state after re-evaluation.

        Args:
            insight_id (UUID): The insight.
            principal (PrincipalModel): The acting principal.
            revision (int | None): A specific revision.

        Returns:
            InsightResponse: The revision.

        Raises:
            NotFoundError: When the insight, its site or the revision is not the principal's.
        """
        insight = await self.repository.get(insight_id)
        if insight is None:
            raise NotFoundError()
        site = await self.sites.get_owned(insight.site_id, principal)
        if revision is None:
            stored = await self.repository.revision(insight.id, insight.current_revision)
            assert stored is not None
            period = stored.evidence["period"]
            window = resolve_window(
                site.timezone,
                site_clock(site),
                start_date=date.fromisoformat(period["start_date"]),
                end_date=date.fromisoformat(period["end_date"]),
            )
            await self.evaluate(site, window)
            insight = await self.repository.get(insight_id)
            assert insight is not None
            revision = insight.current_revision
        frozen = await self.repository.revision(insight.id, revision)
        if frozen is None:
            raise NotFoundError()
        return (await self._with_feedback(principal, [render(insight, frozen)]))[0]

    async def evaluate(self, site: SiteModel, window: Window) -> InsightListResponse:
        """Apply the rules to every active asset and publish the outcome atomically.

        Args:
            site (SiteModel): The resolved site.
            window (Window): The period.

        Returns:
            InsightListResponse: The result.
        """
        site = await self.sites.lock(site.id)  # Serializes publication: one new revision per change.
        snapshot = await self.assets.snapshot(site)
        summary = await self.energy.summarize(site, window)
        origins = {row.asset_id: summary.origins for row in summary.assets}
        candidates: list[Candidate] = []
        learning = comparable = 0
        for asset in [asset for asset in snapshot.assets if asset.archived_at is None]:
            comparison = await self.baseline.compare_asset(site, snapshot, asset, window)
            learning += comparison.state is ComparisonState.LEARNING
            comparable += comparison.state in (ComparisonState.COMPARABLE, ComparisonState.DESCRIPTIVE)
            change = direction(comparison)
            if change is None:
                continue
            snapshot_evidence = evidence(comparison, window, asset, KIND, change, origins.get(asset.id, []))
            delta = comparison.delta_mwh
            assert delta is not None
            candidates.append(
                Candidate(
                    identity_key=f"{KIND}:{asset.id}:{window.start_date}:{window.end_date}",
                    kind=KIND,
                    asset_id=asset.id,
                    period_start=window.start,
                    period_end=window.end,
                    evidence=snapshot_evidence,
                    evidence_hash=evidence_hash(snapshot_evidence),
                    delta_mwh_sort=float(delta),
                )
            )
        published = await self._publish(site, window, candidates)
        # Additional kWh first, then recency, then stable ID. One read covers one period, so recency ties.
        published.sort(key=lambda item: (-item[1], str(item[0].id)))
        return InsightListResponse(
            window=window_response(window),
            observations=[response for response, _ in published],
            notices=notices(summary, snapshot, site.timezone),
            learning_count=learning,
            comparable_count=comparable,
        )

    async def _publish(
        self, site: SiteModel, window: Window, candidates: list[Candidate]
    ) -> list[tuple[InsightResponse, float]]:
        now = wall_now()
        existing = {
            insight.identity_key: insight
            for insight in await self.repository.in_period(site.id, KIND, window.start, window.end)
        }
        published: list[tuple[InsightResponse, float]] = []
        for candidate in candidates:
            insight = existing.pop(candidate.identity_key, None)
            current = (
                await self.repository.revision(insight.id, insight.current_revision) if insight is not None else None
            )
            if insight is not None and current is not None and current.evidence_hash == candidate.evidence_hash:
                if not insight.active:
                    await self.repository.set_state(insight.id, current_revision=insight.current_revision, active=True)
                    insight = insight.model_copy(update={"active": True})
                published.append((render(insight, current), candidate.delta_mwh_sort))
                continue
            number = 1 if insight is None else insight.current_revision + 1
            if insight is None:
                insight = InsightModel(
                    id=uuid4(),
                    site_id=site.id,
                    kind=candidate.kind,
                    asset_id=candidate.asset_id,
                    period_start=candidate.period_start,
                    period_end=candidate.period_end,
                    identity_key=candidate.identity_key,
                    current_revision=number,
                    active=True,
                )
                await self.repository.create(insight)
            else:
                await self.repository.supersede(insight.id, insight.current_revision, now)
                await self.repository.set_state(insight.id, current_revision=number, active=True)
                insight = insight.model_copy(update={"current_revision": number, "active": True})
            revision = InsightRevisionModel(
                insight_id=insight.id,
                revision=number,
                evidence=candidate.evidence,
                evidence_hash=candidate.evidence_hash,
                policy_id=POLICY_ID,
                policy_version=POLICY_VERSION,
                generated_at=now,
                superseded_at=None,
            )
            await self.repository.add_revision(revision)
            published.append((render(insight, revision), candidate.delta_mwh_sort))
        for retired in existing.values():
            if retired.active:  # No longer qualifies: retire once, keep its evidence readable.
                await self.repository.supersede(retired.id, retired.current_revision, now)
                await self.repository.set_state(retired.id, current_revision=retired.current_revision, active=False)
        return published
