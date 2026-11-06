"""Data-quality notices. They rank apart from observations and never claim a device is off."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.assets.model.models import TransportStatus
from app.assets.service.service import SiteSnapshot
from app.energy.model.schema import SummaryResponse
from app.insights.service.copy import _date, number

PARTIAL_BELOW = "0.900"


def _clock(instant: datetime, zone: ZoneInfo) -> str:
    return instant.astimezone(zone).strftime("%H.%M")


def _gap(start: datetime, end: datetime, zone: ZoneInfo) -> str:
    local_start, local_end = start.astimezone(zone), end.astimezone(zone)
    if (local_end - local_start) <= timedelta(days=1) and local_start.date() == (
        local_end - timedelta(seconds=1)
    ).date():
        return f"{_date(str(local_start.date()))} {_clock(start, zone)}–{_clock(end, zone)}"
    last = (local_end - timedelta(seconds=1)).date()
    return f"{_date(str(local_start.date()))} – {_date(str(last))}"


def notices(
    summary: SummaryResponse, snapshot: SiteSnapshot, latest: dict, now: datetime, timezone: str
) -> list[dict[str, str | None]]:
    """List scope, partial-coverage and stale-source notices for a period.

    Args:
        summary (SummaryResponse): The period's summary.
        snapshot (SiteSnapshot): The site's asset model.
        latest (dict): Latest completed reading end by source ID.
        now (datetime): Site time.
        timezone (str): Site timezone.

    Returns:
        list[dict[str, str | None]]: Notices with ID, kind, asset, title and body.
    """
    zone = ZoneInfo(timezone)
    out: list[dict[str, str | None]] = []
    if summary.scope.issues:
        out.append(
            {
                "id": "scope",
                "kind": "scope",
                "asset_id": None,
                "title": "Total gabungan belum dapat dihitung",
                "body": " ".join(issue.message for issue in summary.scope.issues),
            }
        )
    for row in summary.assets:
        if row.coverage is not None and row.coverage < PARTIAL_BELOW:
            gaps = " ".join(f"Data {_gap(gap.start, gap.end, zone)} belum tersedia." for gap in row.gaps[:3])
            percent = number(str(round(float(row.coverage) * 100, 1)))
            out.append(
                {
                    "id": f"partial:{row.asset_id}",
                    "kind": "partial",
                    "asset_id": str(row.asset_id),
                    "title": f"Sebagian data belum tersedia · {row.name}",
                    "body": f"Kelengkapan data: {percent}% periode. {gaps}".strip(),
                }
            )
    asset_by_source = {binding.source_id: binding.asset_id for binding in snapshot.bindings}
    names = {asset.id: asset.name for asset in snapshot.assets}
    for source in snapshot.sources:
        last = latest.get(source.id)
        cadence = timedelta(seconds=source.cadence_seconds or 3600)
        if source.transport_status is not TransportStatus.SIMULATED_LIVE or last is None or now - last <= 2 * cadence:
            continue
        asset_id = asset_by_source.get(source.id)
        out.append(
            {
                "id": f"stale:{source.id}",
                "kind": "stale",
                "asset_id": str(asset_id) if asset_id else None,
                "title": f"Data belum diperbarui · {names.get(asset_id, source.label)}",
                "body": f"Pembacaan terakhir {_date(str(last.astimezone(zone).date()))} {_clock(last, zone)}"
                f" (interval {int(cadence.total_seconds() // 3600)} jam). Ini bukan tanda perangkat mati.",
            }
        )
    return out
