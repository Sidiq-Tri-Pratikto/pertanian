"""Scope proposal and confirmation contracts."""

from datetime import date, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.assets.model.models import RelationKind
from app.energy.model.schema import ScopeIssueResponse, SummaryResponse
from app.energy.service.periods import Preset


class ScopePeriodRequest(BaseModel):
    """A preset or two inclusive local dates, resolved under the site lock."""

    model_config = ConfigDict(extra="forbid")

    preset: Preset | None = None
    start_date: date | None = None
    end_date: date | None = None


class ResolvedScopePeriod(BaseModel):
    """The local dates and timezone shown to the user in preview."""

    model_config = ConfigDict(extra="forbid")

    timezone: str = Field(min_length=1, max_length=128)
    start_date: date
    end_date: date


class ChooseAuthorityRequest(BaseModel):
    """Select an effective candidate as the source of truth."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["choose"]
    asset_id: UUID
    source_id: UUID
    effective_from: AwareDatetime


class SkipAuthorityRequest(BaseModel):
    """Leave the asset's current authority unchanged."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["skip"]
    asset_id: UUID


AuthorityAction = Annotated[ChooseAuthorityRequest | SkipAuthorityRequest, Field(discriminator="action")]


class ScopeAssetPair(BaseModel):
    """Two distinct assets. A disjoint confirmation ignores their order."""

    model_config = ConfigDict(extra="forbid")

    first_asset_id: UUID
    second_asset_id: UUID

    def canonical(self) -> tuple[UUID, UUID]:
        """Return the stable order used to identify an unordered pair."""
        return min(self.first_asset_id, self.second_asset_id), max(self.first_asset_id, self.second_asset_id)


class ScopeProposalRequest(BaseModel):
    """The complete proposal considered by preview and confirmation."""

    model_config = ConfigDict(extra="forbid")

    selected_asset_ids: list[UUID] = Field(min_length=1, max_length=100)
    period: ScopePeriodRequest
    authority_actions: list[AuthorityAction] = Field(default_factory=list, max_length=100)
    disjoint_confirmations: list[ScopeAssetPair] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_unique_items(self) -> Self:
        """Reject repeated membership, actions, and unordered pairs."""
        if len(set(self.selected_asset_ids)) != len(self.selected_asset_ids):
            raise ValueError("Repeated selection member")
        if len({action.asset_id for action in self.authority_actions}) != len(self.authority_actions):
            raise ValueError("Repeated authority action for asset")
        pairs = {pair.canonical() for pair in self.disjoint_confirmations}
        if len(pairs) != len(self.disjoint_confirmations) or any(first == second for first, second in pairs):
            raise ValueError("Repeated or self-referential disjoint pair")
        return self


class ConfirmScopeRequest(ScopeProposalRequest):
    """The reviewed proposal together with its resolved local period and both revision fences."""

    expected_selection_revision: int = Field(ge=0, strict=True)
    expected_binding_revision: int = Field(ge=0, strict=True)
    resolved_period: ResolvedScopePeriod


class ScopeBindingResponse(BaseModel):
    """One stored candidate, with its original half-open range and explicit authority flag."""

    binding_id: UUID
    source_id: UUID
    asset_id: UUID
    label: str
    authoritative: bool
    effective_from: datetime
    effective_to: datetime | None


class ScopeRelationResponse(BaseModel):
    """One relation between site assets, including directed containment."""

    from_asset_id: UUID
    to_asset_id: UUID
    kind: RelationKind


class ScopeSelectionResponse(BaseModel):
    """Confirmed membership and its validity at current site time."""

    selected_asset_ids: list[UUID]
    selection_revision: int
    binding_revision: int
    issues: list[ScopeIssueResponse]
    relations: list[ScopeRelationResponse]
    authority: list[ScopeBindingResponse]
    candidates: list[ScopeBindingResponse]


class ScopePreviewResponse(BaseModel):
    """The computed proposal, both base revisions, and candidates relevant to the period."""

    selection_revision: int
    binding_revision: int
    summary: SummaryResponse
    candidates: list[ScopeBindingResponse]
