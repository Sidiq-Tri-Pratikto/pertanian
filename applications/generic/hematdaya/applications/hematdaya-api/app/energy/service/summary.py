"""The core read: recorded energy for a period and scope, refusing any sum that could double count."""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from app.assets.model.models import AssetModel
from app.assets.service.service import AssetService, SiteSnapshot
from app.core.errors.sanitize import redact_text
from app.energy.model.schema import (
    AssetEnergyResponse,
    ConflictSourceResponse,
    CoverageResponse,
    ExcludedAssetResponse,
    GapResponse,
    ScopeAssetResponse,
    ScopeIssueResponse,
    ScopeResponse,
    SummaryResponse,
    WindowResponse,
)
from app.energy.repository.base_repository import EnergyRepository
from app.energy.service.authority import resolve_asset_authorities, shared_source_pairs
from app.energy.service.format import kwh, percent, ratio
from app.energy.service.freshness import source_freshness
from app.energy.service.intervals import complement, intersect, length
from app.energy.service.measure import AssetBucket, measure
from app.energy.service.periods import Preset, Window, resolve_window
from app.identity.model.models import PrincipalModel
from app.scope.service.selection import SelectionService
from app.scope.service.validity import IssueType, ScopeIssue, scope_issues
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock
from app.sites.service.service import SiteService

_ISSUE_TEXT = {
    IssueType.PARENT_CHILD: "{0} sudah mencakup {1}. Keduanya tidak dapat dijumlahkan.",
    IssueType.UNKNOWN_OVERLAP: "Belum diketahui apakah {0} dan {1} mengukur beban yang terpisah.",
    IssueType.UNCONFIRMED: "Belum ada bukti bahwa {0} dan {1} mengukur beban yang terpisah.",
    IssueType.SOURCE_CONFLICT: "{0} memiliki lebih dari satu sumber untuk beban yang sama. Pilih sumber acuan;"
    " nilainya tidak dijumlahkan.",
    IssueType.SHARED_SOURCE: "{0} dan {1} memakai sumber yang sama pada waktu yang bertumpang tindih.",
}


@dataclass(frozen=True)
class PeriodQuery:
    """A period as the client asked for it."""

    preset: Preset | None = None
    start_date: date | None = None
    end_date: date | None = None


def window_response(window: Window) -> WindowResponse:
    """Render a window.

    Args:
        window (Window): The window.

    Returns:
        WindowResponse: The response.
    """
    return WindowResponse(
        start=window.start,
        end=window.end,
        effective_end=window.effective_end,
        start_date=window.start_date,
        end_date=window.end_date,
        timezone=window.timezone,
        is_current=window.is_current,
    )


def scope_issue_response(issue: ScopeIssue, names: dict[UUID, str]) -> ScopeIssueResponse:
    """Describe the affected assets without echoing credential-like names."""
    return ScopeIssueResponse(
        type=issue.type,
        asset_ids=issue.asset_ids,
        message=_ISSUE_TEXT[issue.type].format(*(redact_text(names[asset_id]) for asset_id in issue.asset_ids)),
    )


class EnergyService:
    """Answers how much energy was recorded, with its completeness and the reasons anything is withheld."""

    def __init__(
        self,
        repository: EnergyRepository,
        sites: SiteService,
        assets: AssetService,
        selections: SelectionService,
    ) -> None:
        """Bind to SQL aggregation and the asset model.

        Args:
            repository (EnergyRepository): Aggregation.
            sites (SiteService): Ownership.
            assets (AssetService): Asset model.
            selections (SelectionService): Confirmed scope lookup.
        """
        self.repository = repository
        self.sites = sites
        self.assets = assets
        self.selections = selections

    async def site_summary(self, site_id: UUID, principal: PrincipalModel, query: PeriodQuery) -> SummaryResponse:
        """Summarize the confirmed scope of an owned site, defaulting to all active assets.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.
            query (PeriodQuery): The period.

        Returns:
            SummaryResponse: The summary.
        """
        site = await self.sites.get_owned(site_id, principal, for_share=True)
        now = site_clock(site)
        window = self.window(site, query, now=now)
        selection = await self.selections.get(site.id)
        body = await self.evaluate(
            site, window, await self.assets.snapshot(site), selection.asset_ids if selection else None, now
        )
        body.selection_revision = selection.revision if selection else None
        body.binding_revision = site.binding_revision
        return body

    async def asset_summary(self, asset_id: UUID, principal: PrincipalModel, query: PeriodQuery) -> SummaryResponse:
        """Summarize one owned asset; its total is its own value, such as a parent meter alone.

        Args:
            asset_id (UUID): The asset.
            principal (PrincipalModel): The acting principal.
            query (PeriodQuery): The period.

        Returns:
            SummaryResponse: The summary.
        """
        asset, site = await self.assets.owned_asset(asset_id, principal)
        now = site_clock(site)
        return await self.evaluate(
            site,
            self.window(site, query, now=now),
            await self.assets.snapshot(site),
            [asset.id],
            now,
            include_archived=True,
        )

    @staticmethod
    def window(site: SiteModel, query: PeriodQuery, *, now: datetime | None = None) -> Window:
        """Resolve a period against the site's clock and timezone.

        Args:
            site (SiteModel): The site.
            query (PeriodQuery): The period.
            now (datetime | None): An already captured site time.

        Returns:
            Window: The window.
        """
        return resolve_window(
            site.timezone,
            now or site_clock(site),
            preset=query.preset,
            start_date=query.start_date,
            end_date=query.end_date,
        )

    async def summarize(self, site: SiteModel, window: Window, asset_ids: list[UUID] | None = None) -> SummaryResponse:
        """Summarize an explicit internal scope, defaulting to every active asset."""
        return await self.evaluate(
            site,
            window,
            await self.assets.snapshot(site),
            asset_ids,
            site_clock(site),
            include_archived=asset_ids is not None,
        )

    async def evaluate(
        self,
        site: SiteModel,
        window: Window,
        snapshot: SiteSnapshot,
        asset_ids: list[UUID] | None,
        now: datetime,
        *,
        include_archived: bool = False,
    ) -> SummaryResponse:
        """Run the same calculator for confirmed reads and projected previews."""
        members = set(asset_ids) if asset_ids is not None else None
        selected = [
            asset
            for asset in snapshot.assets
            if (members is None or asset.id in members) and (include_archived or asset.archived_at is None)
        ]
        selected_ids = [asset.id for asset in selected]
        buckets = [(window.start, window.effective_end)] if window.elapsed.total_seconds() > 0 else []
        authorities = resolve_asset_authorities(selected_ids, snapshot.bindings, window.start, window.effective_end)
        measured = await measure(
            self.repository, selected, snapshot.bindings, snapshot.sources, buckets, now, authorities=authorities
        )
        results = {asset.id: measured.get((asset.id, 0), AssetBucket()) for asset in selected}
        conflicted = {asset_id for asset_id, authority in authorities.items() if authority.conflicts}
        issues = scope_issues(
            selected_ids, snapshot.containment, snapshot.relations, conflicted, shared_source_pairs(authorities)
        )
        names = {asset.id: asset.name for asset in snapshot.assets}
        labels = {source.id: source.label for source in snapshot.sources}

        counted = {
            asset_id: result
            for asset_id, result in results.items()
            if result.conflict is None and not result.unallocatable and result.covered
        }
        if issues:
            total, reason = None, "scope_conflict"
        elif not buckets:
            total, reason = None, "no_data"
        elif any(result.unallocatable for result in results.values()):
            total, reason = None, "insufficient_resolution"
        elif not counted:
            total, reason = None, "no_data"
        else:
            total, reason = sum(result.energy_mwh for result in counted.values()), None

        elapsed = window.elapsed.total_seconds()
        rows = [self._row(asset, results[asset.id], window, total, labels) for asset in selected]
        rows.sort(key=lambda row: (row[1] is None, -(row[1] or 0), row[0].name, str(row[0].asset_id)))
        coverages = [result for result in results.values() if result.conflict is None and not result.unallocatable]
        concurrent = None
        if elapsed and coverages and not conflicted:
            common = [(window.start, window.effective_end)]
            for result in coverages:
                common = intersect(common, result.covered)
            concurrent = ratio(length(common) / elapsed)
        latest = [result.latest_end for result in results.values() if result.latest_end is not None]
        return SummaryResponse(
            window=window_response(window),
            scope=ScopeResponse(
                valid=not issues,
                issues=[scope_issue_response(issue, names) for issue in issues],
                included=[ScopeAssetResponse(asset_id=asset.id, name=asset.name) for asset in selected],
                excluded=[
                    ExcludedAssetResponse(
                        asset_id=asset.id, name=asset.name, reason="archived" if asset.archived_at else "not_selected"
                    )
                    for asset in snapshot.assets
                    if asset.id not in selected_ids
                ],
            ),
            energy_kwh=None if total is None else kwh(total),
            energy_unavailable_reason=reason,
            coverage=CoverageResponse(
                minimum=ratio(min(length(r.covered) / elapsed for r in coverages)) if elapsed and coverages else None,
                concurrent=concurrent,
                allocated_estimate=any(result.allocated for result in results.values()),
            ),
            assets=[row[0] for row in rows],
            latest_measurement_at=max(latest) if latest else None,
            origins=sorted({origin for result in counted.values() for origin in result.origins}),
            revision=site.binding_revision + site.measurement_revision,
            source_freshness=await source_freshness(
                self.repository, selected, snapshot.bindings, snapshot.sources, window, now
            ),
        )

    @staticmethod
    def _row(
        asset: AssetModel, result: AssetBucket, window: Window, total: int | None, labels: dict[UUID, str]
    ) -> tuple[AssetEnergyResponse, int | None]:
        elapsed = window.elapsed.total_seconds()
        energy: int | None = None
        reason: str | None = None
        coverage: str | None = None
        gaps: list[GapResponse] = []
        conflict = None
        if result.conflict is not None:
            reason = "source_conflict"
            conflict = [
                ConflictSourceResponse(source_id=source_id, label=labels[source_id], energy_kwh=kwh(mwh))
                for source_id, mwh in sorted(result.conflict.items(), key=lambda item: labels[item[0]])
            ]
        elif result.unallocatable:
            reason = "insufficient_resolution"
        elif elapsed:
            coverage = ratio(length(result.covered) / elapsed)
            gaps = [
                GapResponse(start=start, end=end)
                for start, end in complement(result.covered, window.start, window.effective_end)
            ]
            if result.covered:
                energy = result.energy_mwh
            else:
                reason = "no_data"
        else:
            reason = "no_data"
        share = percent(energy, total) if energy is not None and total else None
        response = AssetEnergyResponse(
            asset_id=asset.id,
            name=asset.name,
            scope_kind=asset.scope_kind,
            energy_kwh=None if energy is None else kwh(energy),
            energy_unavailable_reason=reason,
            share_percent=share,
            coverage=coverage,
            gaps=gaps,
            conflict_sources=conflict,
        )
        return response, energy
