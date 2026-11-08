"""Per-asset, per-bucket energy and coverage from resolved authority. Summary and history share it."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.assets.model.models import AssetModel, BindingModel, SourceModel
from app.energy.repository.base_repository import EnergyRepository, Span
from app.energy.service.authority import AssetAuthority, resolve_asset_authorities
from app.energy.service.intervals import allocate, union
from app.measurements.model.models import Quality


@dataclass
class AssetBucket:
    """What one asset recorded in one bucket."""

    energy_mwh: int = 0
    covered: list[Span] = field(default_factory=list)
    latest_end: datetime | None = None
    allocated: bool = False
    unallocatable: bool = False
    conflict: dict[UUID, int] | None = None
    origins: set[str] = field(default_factory=set)
    resolution_mwh: int | None = None


async def measure(
    repository: EnergyRepository,
    assets: list[AssetModel],
    bindings: list[BindingModel],
    sources: list[SourceModel],
    buckets: list[Span],
    now: datetime,
    *,
    authorities: dict[UUID, AssetAuthority] | None = None,
) -> dict[tuple[UUID, int], AssetBucket]:
    """Measure each asset in each bucket from its effective authority.

    Readings count only where their source speaks for the asset. A reading crossing a binding or bucket
    boundary is allocated uniformly within its interval, flagged as an estimate, unless it is a long counter
    span, which supports no narrower period. Unresolved candidates are measured per source, never summed.

    Args:
        repository (EnergyRepository): SQL aggregation.
        assets (list[AssetModel]): Assets to measure.
        bindings (list[BindingModel]): Their bindings.
        sources (list[SourceModel]): The site's sources.
        buckets (list[Span]): Half-open buckets in order.
        now (datetime): Site time.
        authorities (dict[UUID, AssetAuthority] | None): Authority already resolved for the bucket window.

    Returns:
        dict[tuple[UUID, int], AssetBucket]: Results keyed by (asset ID, bucket index).
    """
    results: dict[tuple[UUID, int], AssetBucket] = defaultdict(AssetBucket)
    if not buckets:
        return results
    if authorities is None:
        authorities = resolve_asset_authorities([asset.id for asset in assets], bindings, buckets[0][0], buckets[-1][1])
    source_by_id = {source.id: source for source in sources}
    parts: list[tuple[UUID, Span]] = []
    meta: list[tuple[UUID, bool]] = []  # (asset, counts toward the asset value)
    for asset_id, authority in authorities.items():
        for part in authority.parts:
            parts.append((part.source_id, (part.start, part.end)))
            meta.append((asset_id, True))
        for candidate in authority.conflicts:
            parts.append((candidate.source_id, (candidate.start, candidate.end)))
            meta.append((asset_id, False))
            for index, (lo, hi) in enumerate(buckets):
                if candidate.start < hi and lo < candidate.end:
                    results[(asset_id, index)].conflict = results[(asset_id, index)].conflict or {}

    whole, straddlers = await repository.aggregate(parts, buckets, now)
    contributions = [(item.part, item.bucket, item.energy_mwh, item.covered, item.latest_end, False) for item in whole]
    for item in straddlers:
        if item.quality == Quality.LONG_GAP:
            results[(meta[item.part][0], item.bucket)].unallocatable = True
            continue
        energy = allocate(item.energy_mwh, item.interval, item.fragment)
        contributions.append((item.part, item.bucket, energy, [item.fragment], item.interval[1], True))

    for part_index, bucket, energy, covered, latest, allocated in contributions:
        asset_id, counts = meta[part_index]
        source_id = parts[part_index][0]
        result = results[(asset_id, bucket)]
        if not counts:
            assert result.conflict is not None
            result.conflict[source_id] = result.conflict.get(source_id, 0) + energy
            continue
        source = source_by_id[source_id]
        result.energy_mwh += energy
        result.covered = union([*result.covered, *covered])
        result.latest_end = max(filter(None, (result.latest_end, latest)))
        result.allocated = result.allocated or allocated
        result.origins.add(source.origin.value)
        if source.resolution_mwh is not None:
            result.resolution_mwh = max(result.resolution_mwh or 0, source.resolution_mwh)
    return results
