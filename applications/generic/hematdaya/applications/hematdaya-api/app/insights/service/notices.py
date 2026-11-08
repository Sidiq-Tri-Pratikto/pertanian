"""Data-quality notices. They rank apart from observations and never claim a device is off."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.assets.service.service import SiteSnapshot
from app.core.locale import Locale, locale, wants_bilingual_copy
from app.energy.model.schema import SummaryResponse
from app.energy.service.summary import scope_issue_message
from app.insights.model.schema import NoticeResponse
from app.insights.service.copy import _date, number

PARTIAL_BELOW = "0.900"


def _clock(instant: datetime, zone: ZoneInfo) -> str:
    return instant.astimezone(zone).strftime("%H.%M")


def _gap(start: datetime, end: datetime, zone: ZoneInfo, language: Locale) -> str:
    local_start, local_end = start.astimezone(zone), end.astimezone(zone)
    if (local_end - local_start) <= timedelta(days=1) and local_start.date() == (
        local_end - timedelta(seconds=1)
    ).date():
        return f"{_date(str(local_start.date()), language)} {_clock(start, zone)}–{_clock(end, zone)}"
    last = (local_end - timedelta(seconds=1)).date()
    return f"{_date(str(local_start.date()), language)} – {_date(str(last), language)}"


def _cadence(seconds: int, language: Locale) -> str:
    if language == "en":
        value, unit = (
            (seconds // 3600, "hour")
            if seconds % 3600 == 0
            else ((seconds // 60, "minute") if seconds % 60 == 0 else (seconds, "second"))
        )
        return f"{value} {unit}{'s' if value != 1 else ''}"
    if seconds % 3600 == 0:
        return f"{seconds // 3600} jam"
    if seconds % 60 == 0:
        return f"{seconds // 60} menit"
    return f"{seconds} detik"


def _localized_notices(
    summary: SummaryResponse, snapshot: SiteSnapshot, timezone: str, language: Locale
) -> list[dict[str, str | None]]:
    """List scope, partial-coverage and stale-source notices for a period.

    Args:
        summary (SummaryResponse): The period's summary.
        snapshot (SiteSnapshot): The site's asset model.
        timezone (str): Site timezone.

    Returns:
        list[dict[str, str | None]]: Notices with ID, kind, asset, title and body.
    """
    zone = ZoneInfo(timezone)
    out: list[dict[str, str | None]] = []
    names = {asset.id: asset.name for asset in snapshot.assets}
    if summary.scope.issues:
        out.append(
            {
                "id": "scope",
                "kind": "scope",
                "asset_id": None,
                "title": "Combined total unavailable" if language == "en" else "Total gabungan belum dapat dihitung",
                "body": " ".join(scope_issue_message(issue, names, language) for issue in summary.scope.issues),
            }
        )
    for row in summary.assets:
        if row.coverage is not None and row.coverage < PARTIAL_BELOW:
            spans = [_gap(gap.start, gap.end, zone, language) for gap in row.gaps[:3]]
            gaps = " ".join(
                f"Data unavailable for {span}." if language == "en" else f"Data {span} belum tersedia."
                for span in spans
            )
            percent = number(str(round(float(row.coverage) * 100, 1)), language)
            out.append(
                {
                    "id": f"partial:{row.asset_id}",
                    "kind": "partial",
                    "asset_id": str(row.asset_id),
                    "title": f"Some data is unavailable · {row.name}"
                    if language == "en"
                    else f"Sebagian data belum tersedia · {row.name}",
                    "body": (
                        f"Data covers {percent}% of the period. {gaps}"
                        if language == "en"
                        else f"Kelengkapan data: {percent}% periode. {gaps}"
                    ).strip(),
                }
            )
    seen = set()
    for source in summary.source_freshness:
        last, cadence = source.last_capture_at, source.cadence_seconds
        if source.state != "stale" or last is None or cadence is None or source.source_id in seen:
            continue
        seen.add(source.source_id)
        date = _date(str(last.astimezone(zone).date()), language)
        time = _clock(last, zone)
        interval = _cadence(cadence, language)
        name = names.get(source.asset_id, source.label)
        title = f"Source data is stale · {name}" if language == "en" else f"Data belum diperbarui · {name}"
        body = (
            f"Last reading: {date} {time} ({interval} interval). The equipment status is unknown."
            if language == "en"
            else f"Pembacaan terakhir {date} {time} (interval {interval}). Ini bukan tanda perangkat mati."
        )
        out.append(
            {
                "id": f"stale:{source.source_id}",
                "kind": "stale",
                "asset_id": str(source.asset_id),
                "title": title,
                "body": body,
            }
        )
    return out


def notices(summary: SummaryResponse, snapshot: SiteSnapshot, timezone: str) -> list[NoticeResponse]:
    """Render notice variants from the same summary and source snapshot."""
    indonesian = _localized_notices(summary, snapshot, timezone, "id")
    if not wants_bilingual_copy():
        return [NoticeResponse.model_validate(item) for item in indonesian]
    english = _localized_notices(summary, snapshot, timezone, "en")
    return [
        NoticeResponse.model_validate(
            {
                **(en if locale() == "en" else id_),
                "copy_by_locale": {
                    "id": {"title": id_["title"], "body": id_["body"]},
                    "en": {"title": en["title"], "body": en["body"]},
                },
            }
        )
        for id_, en in zip(indonesian, english, strict=True)
    ]
