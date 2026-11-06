"""Set-based seeding of a scenario plan through the shared ingestion path."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.assets.model.models import MeasurementKind, SourceModel
from app.assets.service.service import AssetService
from app.demo.fixtures import FIXTURE_START
from app.demo.scenarios import ScenarioPlan
from app.measurements.model.models import ReadingInput
from app.measurements.service.service import IngestService
from app.sites.model.models import SiteModel
from app.sites.service.service import SiteService


async def seed(
    plan: ScenarioPlan,
    site: SiteModel,
    *,
    sites: SiteService,
    assets: AssetService,
    ingest: IngestService,
    received_at: datetime,
) -> None:
    """Create a plan's assets, sources, bindings and relations, then ingest its readings, in the caller's transaction.

    Readings go through the same ingestion service as any other source, one bulk insert per source.

    Args:
        plan (ScenarioPlan): The scenario.
        site (SiteModel): The locked demo site.
        sites (SiteService): Site revisions.
        assets (AssetService): Asset model.
        ingest (IngestService): Shared ingestion.
        received_at (datetime): Wall-clock seeding time.
    """
    if not plan.assets:
        return
    asset_ids: dict[str, UUID] = {}
    for spec in plan.assets:
        asset = await assets.add_asset(
            site,
            name=spec.name,
            scope_kind=spec.scope_kind,
            category=spec.category,
            location=spec.location,
            expected_use=spec.expected_use,
        )
        asset_ids[spec.key] = asset.id
    sources: dict[str, SourceModel] = {}
    for spec in plan.sources:
        source = await assets.create_source(
            site,
            label=spec.label,
            origin=spec.origin,
            measurement_kind=MeasurementKind.INTERVAL_ENERGY,
            cadence_seconds=spec.cadence_seconds,
            resolution_mwh=spec.resolution_mwh,
            transport_status=spec.transport_status,
        )
        sources[spec.key] = source
        await assets.add_binding(
            site,
            asset_id=asset_ids[spec.asset_key],
            source_id=source.id,
            effective_from=FIXTURE_START,
            authoritative=spec.authoritative,
        )
    for relation in plan.relations:
        await assets.relate(site, asset_ids[relation.from_key], asset_ids[relation.to_key], relation.kind)
    await sites.advance_binding_revision(site)

    by_source: dict[str, list[ReadingInput]] = defaultdict(list)
    for reading in plan.readings:
        by_source[reading.source_key].append(
            ReadingInput(value=Decimal(reading.wh), unit="Wh", interval_start=reading.start, interval_end=reading.end)
        )
    for key, readings in by_source.items():
        await ingest.ingest(
            site, sources[key], readings, received_at=received_at, provenance={"scenario_id": plan.scenario.id}
        )
