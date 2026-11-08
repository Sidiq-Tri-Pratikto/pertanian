"""Consistent scope reads and atomic application of a reviewed proposal."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from app.assets.model.models import BindingModel, RelationKind
from app.assets.service.service import AssetService, SiteSnapshot
from app.audit.service.service import AuditService
from app.core.errors.base import NotFoundError, RequestInvalidError
from app.energy.model.schema import SummaryResponse
from app.energy.service.authority import binding_active_at, resolve_asset_authorities, shared_source_pairs
from app.energy.service.periods import Window, resolve_window
from app.energy.service.summary import EnergyService, scope_issue_response
from app.identity.model.models import PrincipalModel
from app.scope.model.models import AggregationSelectionModel
from app.scope.model.schema import (
    ChooseAuthorityRequest,
    ConfirmScopeRequest,
    ResolvedScopePeriod,
    ScopeBindingResponse,
    ScopePreviewResponse,
    ScopeProposalRequest,
    ScopeRelationResponse,
    ScopeSelectionResponse,
)
from app.scope.service.errors import ScopeConflictError, ScopeStaleError
from app.scope.service.proposal import (
    AmbiguousAuthorityError,
    AuthorityChange,
    DisjointChange,
    plan_authority,
    plan_disjoint,
)
from app.scope.service.selection import SelectionService
from app.scope.service.validity import IssueType, ScopeIssue, containment_closure, scope_issues
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock
from app.sites.service.service import SiteService

_ARCHIVED_SELECTION = "Aset yang diarsipkan tidak dapat ditambahkan ke cakupan. Pilih aset yang masih aktif."


@dataclass
class Projection:
    """A proposed snapshot and the edits that would produce it."""

    snapshot: SiteSnapshot
    authority: list[AuthorityChange]
    disjoint: list[DisjointChange]


def _resolved_period(window: Window) -> ResolvedScopePeriod:
    return ResolvedScopePeriod(timezone=window.timezone, start_date=window.start_date, end_date=window.end_date)


def _binding_responses(snapshot: SiteSnapshot, bindings: list[BindingModel]) -> list[ScopeBindingResponse]:
    labels = {source.id: source.label for source in snapshot.sources}
    return [
        ScopeBindingResponse(
            binding_id=binding.id,
            source_id=binding.source_id,
            asset_id=binding.asset_id,
            label=labels[binding.source_id],
            authoritative=binding.authoritative,
            effective_from=binding.effective_from,
            effective_to=binding.effective_to,
        )
        for binding in sorted(bindings, key=lambda row: (row.asset_id, row.effective_from, row.source_id, row.id))
    ]


class ScopeService:
    """Review and confirm site selections using the existing energy calculator."""

    def __init__(
        self,
        selections: SelectionService,
        sites: SiteService,
        assets: AssetService,
        energy: EnergyService,
        audit: AuditService,
    ) -> None:
        """Bind scope and the services sharing its transaction."""
        self.selections = selections
        self.sites = sites
        self.assets = assets
        self.energy = energy
        self.audit = audit

    async def get(self, site_id: UUID, principal: PrincipalModel) -> ScopeSelectionResponse:
        """Read confirmed membership and current authority while holding an owned read lock."""
        site = await self.sites.get_owned(site_id, principal, for_share=True)
        now = site_clock(site)
        selection = await self.selections.get(site.id)
        return self._confirmed(site, await self.assets.snapshot(site), selection, now)

    async def preview(
        self, site_id: UUID, principal: PrincipalModel, proposal: ScopeProposalRequest
    ) -> ScopePreviewResponse:
        """Evaluate a complete proposal without writing anything."""
        site = await self.sites.get_owned(site_id, principal, for_share=True)
        now = site_clock(site)
        window = self._window(site, proposal, now)
        selection = await self.selections.get(site.id)
        snapshot = await self.assets.snapshot(site)
        projection = self._project(site, snapshot, selection, proposal)
        result = await self._evaluate(site, window, projection, selection, proposal, now)
        members = set(proposal.selected_asset_ids)
        return ScopePreviewResponse(
            selection_revision=selection.revision if selection else 0,
            binding_revision=site.binding_revision,
            summary=result,
            candidates=_binding_responses(
                snapshot,
                [
                    row
                    for row in snapshot.bindings
                    if row.asset_id in members
                    and row.effective_from < window.end
                    and (row.effective_to is None or window.start < row.effective_to)
                ],
            ),
        )

    async def confirm(
        self, site_id: UUID, principal: PrincipalModel, proposal: ConfirmScopeRequest
    ) -> ScopeSelectionResponse:
        """Revalidate and apply the proposal under the owned write lock and both revision fences."""
        site = await self.sites.lock_owned(site_id, principal)
        now = site_clock(site)
        selection = await self.selections.get(site.id)
        revision = selection.revision if selection else 0
        window = self._window(site, proposal, now)
        if (
            proposal.expected_selection_revision != revision
            or proposal.expected_binding_revision != site.binding_revision
            or proposal.resolved_period != _resolved_period(window)
        ):
            raise ScopeStaleError()

        projection = self._project(site, await self.assets.snapshot(site), selection, proposal)
        result = await self._evaluate(site, window, projection, selection, proposal, now)
        if result.scope.issues:
            raise ScopeConflictError(result.scope.issues)

        members = sorted(proposal.selected_asset_ids)
        reviewed_period = _resolved_period(window).model_dump(mode="json")
        if selection is None or selection.asset_ids != members:
            selection = AggregationSelectionModel(site_id=site.id, asset_ids=members, revision=revision + 1)
            await self.selections.replace(selection)
            await self.audit.record(
                site_id=site.id,
                actor_principal_id=principal.id,
                action="scope.selection_changed",
                subject_type="aggregation_selection",
                subject_id=site.id,
                detail={
                    "selection_revision": selection.revision,
                    "selected_asset_ids": [str(member) for member in members],
                    "effect": "site_wide",
                    "reviewed_period": reviewed_period,
                },
            )
        if projection.authority or projection.disjoint:
            await self._apply_edits(site, principal, projection, reviewed_period)
            site = site.model_copy(update={"binding_revision": site.binding_revision + 1})
        return self._confirmed(site, projection.snapshot, selection, now)

    @staticmethod
    def _window(site: SiteModel, proposal: ScopeProposalRequest, now: datetime) -> Window:
        return resolve_window(site.timezone, now, **proposal.period.model_dump())

    async def _evaluate(
        self,
        site: SiteModel,
        window: Window,
        projection: Projection,
        selection: AggregationSelectionModel | None,
        proposal: ScopeProposalRequest,
        now: datetime,
    ) -> SummaryResponse:
        result = await self.energy.evaluate(site, window, projection.snapshot, proposal.selected_asset_ids, now)
        result.selection_revision = selection.revision if selection else None
        result.binding_revision = site.binding_revision
        return result

    @staticmethod
    def _project(
        site: SiteModel,
        snapshot: SiteSnapshot,
        selection: AggregationSelectionModel | None,
        proposal: ScopeProposalRequest,
    ) -> Projection:
        by_id = {asset.id: asset for asset in snapshot.assets}
        members = set(proposal.selected_asset_ids)
        pairs = sorted(pair.canonical() for pair in proposal.disjoint_confirmations)
        requested = members | {action.asset_id for action in proposal.authority_actions}
        requested.update(asset_id for pair in pairs for asset_id in pair)
        bound_sources = {(binding.asset_id, binding.source_id) for binding in snapshot.bindings}
        if not requested <= by_id.keys() or any(
            (action.asset_id, action.source_id) not in bound_sources
            for action in proposal.authority_actions
            if isinstance(action, ChooseAuthorityRequest)
        ):
            raise NotFoundError()
        previous = set(selection.asset_ids) if selection else set()
        if any(by_id[asset_id].archived_at is not None for asset_id in members - previous):
            raise RequestInvalidError(_ARCHIVED_SELECTION)

        names = {asset_id: asset.name for asset_id, asset in by_id.items()}
        contains = containment_closure(snapshot.containment)
        rejected = [
            ScopeIssue(type=IssueType.PARENT_CHILD, asset_ids=[parent, child])
            for first, second in pairs
            for parent, child in ((first, second), (second, first))
            if (parent, child) in contains
        ]
        if rejected:
            raise ScopeConflictError(
                [scope_issue_response(issue, names) for issue in rejected], field="disjoint_confirmations"
            )

        authority = []
        for action in proposal.authority_actions:
            if not isinstance(action, ChooseAuthorityRequest):
                continue
            try:
                change = plan_authority(
                    [binding for binding in snapshot.bindings if binding.asset_id == action.asset_id],
                    action.source_id,
                    action.effective_from,
                )
            except AmbiguousAuthorityError as error:
                issue = ScopeIssue(type=IssueType.SOURCE_CONFLICT, asset_ids=[action.asset_id])
                raise ScopeConflictError([scope_issue_response(issue, names)], field="authority_actions") from error
            if change is not None:
                authority.append(change)
        disjoint = plan_disjoint(site.id, snapshot.relations, pairs)
        bindings = {row.id: row for row in snapshot.bindings}
        for change in authority:
            bindings.update((row.id, row) for row in [*change.updated, *change.inserted])
        removed = {row_id for change in disjoint for row_id in change.removed}
        relations = [
            *(row for row in snapshot.relations if row.id not in removed),
            *(change.added for change in disjoint if change.added is not None),
        ]
        return Projection(
            snapshot.model_copy(update={"bindings": list(bindings.values()), "relations": relations}),
            authority,
            disjoint,
        )

    async def _apply_edits(
        self, site: SiteModel, principal: PrincipalModel, projection: Projection, reviewed_period: dict
    ) -> None:
        await self.assets.apply_binding_edits(
            site,
            [row for change in projection.authority for row in change.updated],
            [row for change in projection.authority for row in change.inserted],
        )
        await self.assets.apply_relation_edits(
            site,
            [row_id for change in projection.disjoint for row_id in change.removed],
            [change.added for change in projection.disjoint if change.added is not None],
        )
        await self.sites.advance_binding_revision(site)
        revision = site.binding_revision + 1
        for change in projection.authority:
            await self.audit.record(
                site_id=site.id,
                actor_principal_id=principal.id,
                action="scope.authority_changed",
                subject_type="asset",
                subject_id=change.asset_id,
                affected_from=change.start,
                affected_to=change.end,
                detail={
                    "binding_revision": revision,
                    "source_id": str(change.source_id),
                    "reviewed_period": reviewed_period,
                },
            )
        for change in projection.disjoint:
            await self.audit.record(
                site_id=site.id,
                actor_principal_id=principal.id,
                action="scope.disjoint_confirmed",
                subject_type="asset_pair",
                subject_id=change.pair[0],
                detail={
                    "binding_revision": revision,
                    "asset_ids": [str(asset_id) for asset_id in change.pair],
                    "effect": "site_wide",
                    "reviewed_period": reviewed_period,
                },
            )

    @staticmethod
    def _confirmed(
        site: SiteModel, snapshot: SiteSnapshot, selection: AggregationSelectionModel | None, now: datetime
    ) -> ScopeSelectionResponse:
        names = {asset.id: asset.name for asset in snapshot.assets}
        active = {asset.id for asset in snapshot.assets if asset.archived_at is None}
        selected = selection.asset_ids if selection else sorted(active)
        selected_ids = set(selected)
        eligible = [asset.id for asset in snapshot.assets if asset.id in active and asset.id in selected_ids]
        current = resolve_asset_authorities(sorted(active), snapshot.bindings, now, now + timedelta(microseconds=1))
        authorities = {asset_id: current[asset_id] for asset_id in eligible}
        issues = scope_issues(
            eligible,
            snapshot.containment,
            snapshot.relations,
            {asset_id for asset_id, authority in authorities.items() if authority.conflicts},
            shared_source_pairs(authorities),
        )
        candidates = [row for row in snapshot.bindings if row.asset_id in active and binding_active_at(row, now)]
        explicit_assets = {row.asset_id for row in candidates if row.authoritative}
        authority_pairs = {
            (asset_id, part.source_id) for asset_id, authority in current.items() for part in authority.parts
        }
        relations = {(row.from_asset_id, row.to_asset_id, row.kind) for row in snapshot.relations}
        relations.update((parent, child, RelationKind.CONTAINS) for parent, child in snapshot.containment)
        return ScopeSelectionResponse(
            selected_asset_ids=selected,
            selection_revision=selection.revision if selection else 0,
            binding_revision=site.binding_revision,
            issues=[scope_issue_response(issue, names) for issue in issues],
            relations=[
                ScopeRelationResponse(from_asset_id=first, to_asset_id=second, kind=kind)
                for first, second, kind in sorted(relations)
            ],
            authority=_binding_responses(
                snapshot,
                [
                    row
                    for row in candidates
                    if (row.asset_id, row.source_id) in authority_pairs
                    and (row.authoritative or row.asset_id not in explicit_assets)
                ],
            ),
            candidates=_binding_responses(snapshot, candidates),
        )
