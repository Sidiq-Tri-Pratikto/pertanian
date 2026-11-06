"""Day and hour buckets in the site's local calendar, from the same rules as the summary."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo

from app.assets.service.service import AssetService
from app.energy.model.schema import HighestBucketResponse, HistoryBucketResponse, HistoryResponse
from app.energy.repository.base_repository import EnergyRepository
from app.energy.service.format import kwh, ratio
from app.energy.service.intervals import length
from app.energy.service.measure import AssetBucket, measure
from app.energy.service.periods import RangeTooLargeError, Window, local_midnight
from app.energy.service.summary import EnergyService, PeriodQuery, window_response
from app.identity.model.models import PrincipalModel
from app.sites.service.clock import site_clock

MAX_BUCKETS = 1000


class Granularity(StrEnum):
    """Bucket size."""

    DAY = "day"
    HOUR = "hour"


def local_buckets(window: Window, granularity: Granularity) -> list[tuple[datetime, datetime]]:
    """Return the window's buckets with exact UTC bounds.

    Hours step through the actual UTC duration of each local day, so a daylight-saving day has 23 or 25.

    Args:
        window (Window): The window.
        granularity (Granularity): Day or hour.

    Returns:
        list[tuple[datetime, datetime]]: Half-open buckets in order.

    Raises:
        RangeTooLargeError: For more than 1,000 buckets.
    """
    days = (window.end_date - window.start_date).days + 1
    starts = [local_midnight(window.start_date + timedelta(days=i), window.timezone) for i in range(days + 1)]
    if granularity is Granularity.DAY:
        buckets = list(zip(starts, starts[1:], strict=False))
    else:
        hours = sum(int((end - start) / timedelta(hours=1)) for start, end in zip(starts, starts[1:], strict=False))
        if hours > MAX_BUCKETS:
            raise RangeTooLargeError()
        buckets = []
        for day_start, day_end in zip(starts, starts[1:], strict=False):
            cursor = day_start
            while cursor < day_end:
                buckets.append((cursor, min(cursor + timedelta(hours=1), day_end)))
                cursor += timedelta(hours=1)
    if len(buckets) > MAX_BUCKETS:
        raise RangeTooLargeError()
    return buckets


class HistoryService:
    """Bucketed asset history. Gaps stay gaps, and no code path fills or interpolates a bucket."""

    def __init__(self, repository: EnergyRepository, energy: EnergyService, assets: AssetService) -> None:
        """Bind to aggregation and the window rules the summary uses.

        Args:
            repository (EnergyRepository): Aggregation.
            energy (EnergyService): Window resolution.
            assets (AssetService): Asset model.
        """
        self.repository = repository
        self.energy = energy
        self.assets = assets

    async def asset_history(
        self, asset_id: UUID, principal: PrincipalModel, query: PeriodQuery, granularity: Granularity
    ) -> HistoryResponse:
        """Return an owned asset's buckets with state, coverage and the highest complete bucket.

        Args:
            asset_id (UUID): The asset.
            principal (PrincipalModel): The acting principal.
            query (PeriodQuery): The period.
            granularity (Granularity): Day or hour.

        Returns:
            HistoryResponse: The series.
        """
        asset, site = await self.assets.owned_asset(asset_id, principal)
        window = self.energy.window(site, query)
        buckets = local_buckets(window, granularity)
        now = site_clock(site)
        elapsed = [(start, min(end, now)) for start, end in buckets if start < now]
        snapshot = await self.assets.snapshot(site)
        measured = await measure(self.repository, [asset], snapshot.bindings, snapshot.sources, elapsed, now)
        zone = ZoneInfo(site.timezone)
        rows: list[HistoryBucketResponse] = []
        complete: list[tuple[int, datetime]] = []
        origins: set[str] = set()
        resolution: int | None = None
        for index, (start, end) in enumerate(buckets):
            local = start.astimezone(zone)
            offset = local.strftime("%z")
            fields = {
                "start": start.astimezone(UTC),
                "end": end.astimezone(UTC),
                "local_date": local.date(),
                "local_time": local.strftime("%H:%M") if granularity is Granularity.HOUR else None,
                "utc_offset": f"{offset[:3]}:{offset[3:]}",
                "energy_kwh": None,
                "unavailable_reason": None,
                "coverage": None,
            }
            if start >= now:
                rows.append(HistoryBucketResponse(**fields, state="future"))
                continue
            result = measured.get((asset.id, index), AssetBucket())
            span = (min(end, now) - start).total_seconds()
            if result.conflict is not None or result.unallocatable:
                reason = "source_conflict" if result.conflict is not None else "insufficient_resolution"
                rows.append(HistoryBucketResponse(**fields | {"unavailable_reason": reason}, state="unavailable"))
                continue
            coverage = length(result.covered) / span
            if not result.covered:
                rows.append(HistoryBucketResponse(**fields | {"coverage": ratio(0)}, state="missing"))
                continue
            origins |= result.origins
            if result.resolution_mwh is not None:
                resolution = max(resolution or 0, result.resolution_mwh)
            state = "measured" if coverage >= 1 else "partial"
            if state == "measured":
                complete.append((result.energy_mwh, start))
            rows.append(
                HistoryBucketResponse(
                    **fields | {"energy_kwh": kwh(result.energy_mwh), "coverage": ratio(coverage)}, state=state
                )
            )
        highest = min(complete, key=lambda item: (-item[0], item[1])) if complete else None
        return HistoryResponse(
            window=window_response(window),
            bucket=granularity.value,
            origins=sorted(origins),
            resolution_mwh=resolution,
            highest_bucket=HighestBucketResponse(start=highest[1].astimezone(UTC)) if highest else None,
            buckets=rows,
        )
