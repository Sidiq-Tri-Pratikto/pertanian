"""What a preview takes as given, listed before the user confirms."""

from datetime import datetime, timedelta
from itertools import pairwise
from zoneinfo import ZoneInfo

from app.imports.model.models import ParsedFile, PowerMeaning, ValueKind
from app.imports.service.classify import StagedRow, bound_text, chosen_kind, row_span
from app.imports.service.columns import Role, resolve_columns

_MONTHS = (
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
)
_MILLISECOND = timedelta(milliseconds=1)


def _date(moment: datetime) -> str:
    return f"{moment.day} {_MONTHS[moment.month - 1]} {moment.year}"


def _time(moment: datetime) -> str:
    return f"{moment.hour:02}.{moment.minute:02}"


def _date_time(moment: datetime) -> str:
    return f"{_date(moment)} {_time(moment)}"


def _date_range(first: datetime, last: datetime) -> str:
    if first.date() == last.date():
        return _date(first)
    if (first.year, first.month) == (last.year, last.month):
        return f"{first.day}–{_date(last)}"
    if first.year == last.year:
        return f"{first.day} {_MONTHS[first.month - 1]}–{_date(last)}"
    return f"{_date(first)}–{_date(last)}"


def _gap(start: datetime, end: datetime, zone: ZoneInfo) -> str:
    """Port of ``fmtGap`` in the prototype: both ends local, and the last instant decides the end's date."""
    first, after, last = start.astimezone(zone), end.astimezone(zone), (end - _MILLISECOND).astimezone(zone)
    if _time(first) == "00.00" and _time(after) == "00.00":
        return _date_range(first, last)
    if first.date() == last.date():
        closing = "24.00" if _time(after) == "00.00" else _time(after)
        return f"{_date(first)} {_time(first)}–{closing}"
    return f"{_date_time(first)}–{_date_time(after)}"


def _timestamp_note(parsed: ParsedFile) -> str:
    declared = any(stream in parsed.cadences for stream in parsed.answers.interval_minutes)
    covers = "interval yang disimpulkan atau diisi per sumber" if declared else "interval yang disimpulkan per sumber"
    return (
        f"Timestamp adalah awal interval; setiap baris mencakup {covers}, "
        "termasuk baris terakhir. Jeda panjang tetap menjadi data kosong."
    )


def _counter_notes(staged: list[StagedRow], zone: ZoneInfo) -> list[str]:
    streams: dict[str, list[StagedRow]] = {}
    for row in staged:
        if row.kind is ValueKind.COUNTER:
            streams.setdefault(row.stream_key, []).append(row)
    notes: list[str] = []
    for rows in streams.values():
        ordered = sorted(rows, key=lambda row: row_span(row)[0])
        for previous, current in pairwise(ordered):
            if current.value_milli < previous.value_milli:
                at = row_span(current)[0]
                notes.append(
                    f"Penghitung {current.asset_name} kembali ke nilai lebih kecil pada "
                    f"{_date_time(at.astimezone(zone))}: interval {_gap(row_span(previous)[0], at, zone)} "
                    "tidak diketahui (segmen baru)."
                )
        notes.append(f"Pembacaan pertama {ordered[0].asset_name} menjadi titik awal penghitung, bukan energi.")
    return notes


def build_assumptions(parsed: ParsedFile, staged: list[StagedRow], *, now: datetime, timezone: str) -> list[str]:
    """List what a preview assumes, in a fixed order.

    Args:
        parsed (ParsedFile): The file.
        staged (list[StagedRow]): The rows a commit would add.
        now (datetime): The site's product time, which reads stop at.
        timezone (str): The site's IANA timezone.

    Returns:
        list[str]: The assumptions.
    """
    zone = ZoneInfo(timezone)
    kind = chosen_kind(parsed)
    assumptions: list[str] = []
    if Role.TIMESTAMP in resolve_columns(parsed.headers).columns and kind is not ValueKind.COUNTER:
        assumptions.append(_timestamp_note(parsed))
    if parsed.has_naive_timestamps:
        assumptions.append(f"Waktu tanpa offset dibaca sebagai {timezone}.")
    if kind is ValueKind.AVERAGE_POWER and parsed.answers.power_meaning is PowerMeaning.AVERAGE:
        assumptions.append("Daya rata-rata interval × durasi = energi (100 W selama 30 menit = 50 Wh).")
    if parsed.had_bom:
        assumptions.append("BOM UTF-8 dilewati.")
    assumptions.append(
        "Pemisah kolom: titik koma; koma sebagai desimal."
        if parsed.delimiter == ";"
        else "Pemisah kolom: koma; titik sebagai desimal, koma desimal hanya dalam tanda kutip."
    )
    if parsed.ignored_columns:
        assumptions.append(bound_text(f"Kolom tidak dipakai: {', '.join(parsed.ignored_columns)}."))
    if parsed.blank_lines:
        assumptions.append(f"{parsed.blank_lines} baris kosong tidak dihitung sebagai baris data.")
    assumptions += _counter_notes(staged, zone)
    after_now = sum(row_span(row)[1] > now for row in staged)
    if after_now:
        assumptions.append(
            f"{after_now} baris berakhir setelah waktu ruang kerja {_date_time(now.astimezone(zone))}; "
            "baris itu belum dihitung pada ringkasan."
        )
    return assumptions
