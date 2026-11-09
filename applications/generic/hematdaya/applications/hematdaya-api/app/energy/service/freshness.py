"""Freshness v1 from effective authority and valid completed captures."""

from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from app.assets.model.models import AssetModel, BindingModel, SourceModel, SourceOrigin, TransportStatus
from app.energy.model.schema import CaptureRangeResponse, FreshnessState, SourceFreshnessResponse
from app.energy.repository.base_repository import CaptureQuery, EnergyRepository
from app.energy.service.authority import AuthorityPart, resolve_authority
from app.energy.service.periods import Window


def recurring_state(now: datetime, last: datetime | None, cadence: int | None) -> FreshnessState:
    """Use a strict two-interval threshold, only with known cadence and a completed capture."""
    if cadence is None or cadence <= 0 or last is None or last > now:
        return "unknown"
    return "stale" if (now - last).total_seconds() > 2 * cadence else "current"


async def source_freshness(
    repository: EnergyRepository,
    selected: list[AssetModel],
    bindings: list[BindingModel],
    sources: list[SourceModel],
    window: Window,
    now: datetime,
) -> list[SourceFreshnessResponse]:
    """Describe effective streams for selected assets, batching their capture ranges.

    Recurring captures must be inside the current uninterrupted authority segment. Historical readings
    may overlap the report boundaries because the same interval can contribute to adjacent reports.
    """
    names = {asset.id: asset.name for asset in selected}
    by_asset: dict[UUID, list[BindingModel]] = defaultdict(list)
    for binding in bindings:
        if binding.asset_id in names:
            by_asset[binding.asset_id].append(binding)
    by_source = {source.id: source for source in sources}
    rows: dict[tuple[UUID, UUID], str] = {}
    reads: list[tuple[tuple[UUID, UUID], CaptureQuery]] = []

    def add(asset_id: UUID, part: AuthorityPart, kind: str, *, read: bool = False) -> None:
        key = (asset_id, part.source_id)
        rows[key] = kind
        if read:
            reads.append(
                (
                    key,
                    CaptureQuery(part.source_id, (part.start, part.end), kind == "historical", kind == "live_counter"),
                )
            )

    for asset_id, parts in by_asset.items():
        current = resolve_authority(parts, min(part.effective_from for part in parts), now + timedelta(microseconds=1))
        for part in current.parts:
            source = by_source[part.source_id]
            if (
                part.end > now
                and source.origin is not SourceOrigin.IMPORT
                and source.transport_status is not TransportStatus.HISTORICAL
            ):
                if source.transport_status is TransportStatus.LIVE:
                    add(asset_id, part, "live_counter", read=True)
                else:
                    recurring = source.transport_status is TransportStatus.SIMULATED_LIVE
                    add(asset_id, part, "recurring" if recurring else "unknown", read=recurring)
        for part in current.conflicts:
            if part.end > now:
                add(asset_id, part, "unresolved")

        history = resolve_authority(parts, window.start, window.effective_end)
        for part in history.parts:
            source = by_source[part.source_id]
            if source.origin is SourceOrigin.IMPORT or source.transport_status is TransportStatus.HISTORICAL:
                add(asset_id, part, "historical", read=True)
        for part in history.conflicts:
            source = by_source[part.source_id]
            key = (asset_id, part.source_id)
            if key not in rows and (
                source.origin is SourceOrigin.IMPORT or source.transport_status is TransportStatus.HISTORICAL
            ):
                add(asset_id, part, "unresolved")

    captures = await repository.capture_ranges([query for _, query in reads], now) if reads else {}
    by_binding: dict[tuple[UUID, UUID], list[tuple[datetime, datetime, datetime]]] = defaultdict(list)
    for index, capture in captures.items():
        by_binding[reads[index][0]].append(capture)
    result: list[SourceFreshnessResponse] = []
    for (asset_id, source_id), kind in rows.items():
        source = by_source[source_id]
        cadence = source.cadence_seconds
        cadence = cadence if cadence is not None and cadence > 0 else None
        spans = by_binding[(asset_id, source_id)]
        last = max((capture for _, _, capture in spans), default=None)
        historical_range = None
        state: FreshnessState = "unknown"
        if kind in ("recurring", "live_counter"):
            state = recurring_state(now, last, cadence)
        elif kind == "historical" and spans:
            state = "historical"
            historical_range = CaptureRangeResponse(
                start=min(start for start, _, _ in spans), end=max(end for _, end, _ in spans)
            )
        result.append(
            SourceFreshnessResponse(
                source_id=source_id,
                label=source.label,
                asset_id=asset_id,
                origin=source.origin,
                state=state,
                last_capture_at=last,
                cadence_seconds=cadence,
                policy_version=1,
                historical_range=historical_range,
            )
        )
    # Bindings and source IDs are generated independently on each demo creation.
    return sorted(result, key=lambda row: (names[row.asset_id], row.label, str(row.asset_id), str(row.source_id)))
