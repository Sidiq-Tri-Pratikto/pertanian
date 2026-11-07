"""Harmless, reversible feedback on one evidence revision."""

from datetime import UTC, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.feedback.model.models import FeedbackAction, FeedbackStateModel, Visibility
from app.feedback.model.schema import FeedbackResponse
from app.feedback.repository.base_repository import FeedbackRepository
from app.feedback.service.errors import FeedbackKeyConflictError
from app.identity.model.models import PrincipalModel
from app.insights.service.service import InsightService
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock


def next_local_midnight(site: SiteModel) -> datetime:
    """Return the next local midnight on the site clock: virtual for a demo, wall otherwise.

    Args:
        site (SiteModel): The site.

    Returns:
        datetime: That instant in UTC.
    """
    zone = ZoneInfo(site.timezone)
    today = site_clock(site).astimezone(zone).date()
    return datetime.combine(today + timedelta(days=1), time(), tzinfo=zone).astimezone(UTC)


class FeedbackService:
    """Applies feedback once per key. Writes only feedback tables: no measurement, asset or source changes."""

    def __init__(self, repository: FeedbackRepository, *, insights: InsightService) -> None:
        """Bind to storage and the insight owner check.

        Args:
            repository (FeedbackRepository): Feedback storage.
            insights (InsightService): Ownership and revision membership.
        """
        self.repository = repository
        self.insights = insights

    async def apply(
        self, insight_id: UUID, principal: PrincipalModel, revision: int, action: FeedbackAction, key: str
    ) -> FeedbackResponse:
        """Apply an action, or replay the original outcome of the same key and payload.

        Args:
            insight_id (UUID): The insight.
            principal (PrincipalModel): The acting principal.
            revision (int): The revision the owner saw.
            action (FeedbackAction): The action.
            key (str): The client's ``Idempotency-Key``.

        Returns:
            FeedbackResponse: The confirmed state.

        Raises:
            FeedbackKeyConflictError: When the key was used for another insight, revision or action.
        """
        site = await self.insights.owned_revision(insight_id, principal, revision)  # Ownership before any replay.
        if not await self.repository.claim(principal.id, key, insight_id, revision, action):
            existing = await self.repository.operation(principal.id, key)
            if (existing.insight_id, existing.revision, existing.action) != (insight_id, revision, action):
                raise FeedbackKeyConflictError()
            assert existing.response is not None  # Committed together with its claim.
            return FeedbackResponse.model_validate(existing.response)
        current = next(
            (state for state in await self.repository.states(principal.id, [insight_id]) if state.revision == revision),
            FeedbackStateModel(
                insight_id=insight_id, revision=revision, rating=None, visibility=Visibility.VISIBLE, until=None
            ),
        )
        state = _next_state(current, action, site)
        await self.repository.save(principal.id, state)
        response = FeedbackResponse(action=action, **state.model_dump())
        await self.repository.complete(principal.id, key, response.model_dump(mode="json"))
        return response


def _next_state(state: FeedbackStateModel, action: FeedbackAction, site: SiteModel) -> FeedbackStateModel:
    match action:
        case FeedbackAction.USEFUL | FeedbackAction.NOT_RELEVANT:
            return state.model_copy(update={"rating": action.value})
        case FeedbackAction.HIDE:
            return state.model_copy(update={"visibility": Visibility.HIDDEN, "until": None})
        case FeedbackAction.SNOOZE:
            return state.model_copy(update={"visibility": Visibility.SNOOZED, "until": next_local_midnight(site)})
        case FeedbackAction.RESTORE:
            return state.model_copy(update={"visibility": Visibility.VISIBLE, "until": None})
