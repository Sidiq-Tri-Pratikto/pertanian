"""Matched baseline for one asset: aligned slots from one query, then the pure comparison."""

from datetime import timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.assets.model.models import AssetModel
from app.assets.service.service import AssetService, SiteSnapshot
from app.baseline.model.schema import ComparisonResponse, ComparisonWindowResponse
from app.baseline.service.compare import (
    MAX_PERIOD,
    Comparison,
    ComparisonState,
    Slot,
    WindowSlots,
    compare,
)
from app.energy.model.schema import GapResponse
from app.energy.repository.base_repository import SlotRepository
from app.energy.service.authority import resolve_authority
from app.energy.service.format import kwh, percent, ratio
from app.energy.service.intervals import union
from app.energy.service.periods import Window, local_midnight
from app.energy.service.summary import EnergyService, PeriodQuery, window_response
from app.identity.model.models import PrincipalModel
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock

WEEKS = 3


class BaselineService:
    """Compares a period with the same local weekdays and times in the previous three weeks."""

    def __init__(self, slots: SlotRepository, energy: EnergyService, assets: AssetService) -> None:
        """Bind to slot reads and the shared window rules.

        Args:
            slots (SlotRepository): Whole readings.
            energy (EnergyService): Window resolution.
            assets (AssetService): Asset model.
        """
        self.slots = slots
        self.energy = energy
        self.assets = assets

    async def asset_comparison(
        self, asset_id: UUID, principal: PrincipalModel, query: PeriodQuery
    ) -> ComparisonResponse:
        """Compare an owned asset's period with its matched baseline.

        Args:
            asset_id (UUID): The asset.
            principal (PrincipalModel): The acting principal.
            query (PeriodQuery): The period.

        Returns:
            ComparisonResponse: The comparison.
        """
        asset, site = await self.assets.owned_asset(asset_id, principal)
        window = self.energy.window(site, query)
        comparison = await self.compare_asset(site, await self.assets.snapshot(site), asset, window)
        return comparison_response(comparison, window)

    async def compare_asset(
        self, site: SiteModel, snapshot: SiteSnapshot, asset: AssetModel, window: Window
    ) -> Comparison:
        """Build aligned windows and compare them. Insights and history reuse this.

        Args:
            site (SiteModel): The resolved site.
            snapshot (SiteSnapshot): Its asset model.
            asset (AssetModel): The asset.
            window (Window): The current window.

        Returns:
            Comparison: The result.
        """
        elapsed = window.elapsed
        if elapsed <= timedelta(0):
            return Comparison(ComparisonState.UNAVAILABLE, "Periode ini belum memiliki waktu yang sudah berlalu.")
        if window.end - window.start > MAX_PERIOD + timedelta(hours=1):  # A DST week may be one hour longer.
            return Comparison(
                ComparisonState.UNAVAILABLE, "Belum dapat dibandingkan: pilih periode paling lama 7 hari."
            )
        starts = [local_midnight(window.start_date - timedelta(weeks=k), window.timezone) for k in range(WEEKS + 1)]
        spans = [(start, start + elapsed) for start in starts]
        bindings = [binding for binding in snapshot.bindings if binding.asset_id == asset.id]
        authority = resolve_authority(bindings, spans[-1][0], spans[0][1])
        if any(part.start < hi and lo < part.end for part in authority.conflicts for lo, hi in spans):
            return Comparison(ComparisonState.UNAVAILABLE, "Belum dapat dibandingkan: sumber acuan belum dipilih.")
        parts = [(part.source_id, (part.start, part.end)) for part in authority.parts]
        resolution = {source.id: source.resolution_mwh for source in snapshot.sources}
        windows = [WindowSlots(k, start, end) for k, (start, end) in enumerate(spans)]
        zone = ZoneInfo(window.timezone)
        for reading in await self.slots.whole_readings(parts, spans, site_clock(site)):
            local = reading.start.astimezone(zone)
            day = (local.date() - (window.start_date - timedelta(weeks=reading.window))).days
            seconds = int((reading.end - reading.start).total_seconds())
            key = (day, local.time().replace(tzinfo=None), local.fold, seconds, reading.kind)
            windows[reading.window].slots[key] = Slot(
                reading.start, reading.end, reading.energy_mwh, resolution[parts[reading.part][0]]
            )
        return compare(windows[0], windows[1:])


def comparison_response(comparison: Comparison, window: Window) -> ComparisonResponse:
    """Render a comparison with every window, its numbers and the actual common mask.

    Args:
        comparison (Comparison): The comparison.
        window (Window): The requested window.

    Returns:
        ComparisonResponse: The response.
    """

    def render(slots: WindowSlots) -> ComparisonWindowResponse:
        eligible = slots.index == 0 or slots.index in comparison.eligible
        has_mask = bool(comparison.mask) and eligible and comparison.baseline_mwh is not None
        local_start = window.start_date - timedelta(weeks=slots.index)
        return ComparisonWindowResponse(
            weeks_before=slots.index,
            start_date=local_start,
            end_date=local_start + (window.end_date - window.start_date),
            start=slots.start,
            end=slots.end,
            measured_kwh=kwh(slots.measured_mwh),
            mask_kwh=kwh(comparison.mask_sum(slots)) if has_mask else None,
            coverage=ratio(slots.coverage),
            eligible=eligible,
        )

    baseline = comparison.baseline_mwh
    delta = comparison.delta_mwh
    current = comparison.current
    mask = union([(current.slots[key].start, current.slots[key].end) for key in comparison.mask]) if current else []
    return ComparisonResponse(
        state=comparison.state,
        reason=comparison.reason,
        window=window_response(window),
        current=render(current) if current else None,
        historical=[render(slots) for slots in comparison.historical],
        baseline_kwh=None if baseline is None else kwh(baseline),
        mad_kwh=None if comparison.mad_mwh is None else kwh(comparison.mad_mwh),
        delta_kwh=None if delta is None else kwh(delta),
        percent=percent(delta, baseline) if delta is not None and baseline else None,
        resolution_kwh=None if comparison.resolution_mwh is None else kwh(comparison.resolution_mwh),
        mask_coverage=None if comparison.mask_coverage is None else ratio(comparison.mask_coverage),
        common_mask=[GapResponse(start=start, end=end) for start, end in mask] if baseline is not None else [],
    )
