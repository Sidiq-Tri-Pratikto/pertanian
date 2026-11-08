"""What a preview takes as given, listed before the user confirms."""

from datetime import datetime, timedelta
from itertools import pairwise
from zoneinfo import ZoneInfo

from app.core.locale import MONTH_NAMES, Locale
from app.imports.model.models import ParsedFile, PowerMeaning, ValueKind
from app.imports.service.classify import StagedRow, bound_text, chosen_kind, row_span
from app.imports.service.columns import Role, resolve_columns

_MILLISECOND = timedelta(milliseconds=1)


def _date(moment: datetime, language: Locale) -> str:
    return f"{moment.day} {MONTH_NAMES[language][moment.month - 1]} {moment.year}"


def _time(moment: datetime) -> str:
    return f"{moment.hour:02}.{moment.minute:02}"


def _date_time(moment: datetime, language: Locale) -> str:
    return f"{_date(moment, language)} {_time(moment)}"


def _date_range(first: datetime, last: datetime, language: Locale) -> str:
    if first.date() == last.date():
        return _date(first, language)
    if (first.year, first.month) == (last.year, last.month):
        return f"{first.day}–{_date(last, language)}"
    if first.year == last.year:
        return f"{first.day} {MONTH_NAMES[language][first.month - 1]}–{_date(last, language)}"
    return f"{_date(first, language)}–{_date(last, language)}"


def _gap(start: datetime, end: datetime, zone: ZoneInfo, language: Locale) -> str:
    """Port of ``fmtGap`` in the prototype: both ends local, and the last instant decides the end's date."""
    first, after, last = start.astimezone(zone), end.astimezone(zone), (end - _MILLISECOND).astimezone(zone)
    if _time(first) == "00.00" and _time(after) == "00.00":
        return _date_range(first, last, language)
    if first.date() == last.date():
        closing = "24.00" if _time(after) == "00.00" else _time(after)
        return f"{_date(first, language)} {_time(first)}–{closing}"
    return f"{_date_time(first, language)}–{_date_time(after, language)}"


def _timestamp_note(parsed: ParsedFile) -> str:
    declared = any(stream in parsed.cadences for stream in parsed.answers.interval_minutes)
    covers = "interval yang disimpulkan atau diisi per sumber" if declared else "interval yang disimpulkan per sumber"
    return (
        f"Timestamp adalah awal interval; setiap baris mencakup {covers}, "
        "termasuk baris terakhir. Jeda panjang tetap menjadi data kosong."
    )


def _counter_notes(staged: list[StagedRow], zone: ZoneInfo, language: Locale) -> list[str]:
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
                time = _date_time(at.astimezone(zone), language)
                span = _gap(row_span(previous)[0], at, zone, language)
                notes.append(
                    f"The {current.asset_name} counter decreased at {time}. The interval {span} is unknown."
                    if language == "en"
                    else f"Penghitung {current.asset_name} kembali ke nilai lebih kecil pada {time}: "
                    f"interval {span} tidak diketahui (segmen baru)."
                )
        name = ordered[0].asset_name
        notes.append(
            f"The first {name} reading establishes the counter baseline."
            if language == "en"
            else f"Pembacaan pertama {name} menjadi titik awal penghitung, bukan energi."
        )
    return notes


def build_assumptions(
    parsed: ParsedFile, staged: list[StagedRow], *, now: datetime, timezone: str, language: Locale = "id"
) -> list[str]:
    """List what a preview assumes, in a fixed order.

    Args:
        parsed (ParsedFile): The file.
        staged (list[StagedRow]): The rows a commit would add.
        now (datetime): The site's product time, which reads stop at.
        timezone (str): The site's IANA timezone.
        language (Locale): Language of the display copy.

    Returns:
        list[str]: The assumptions.
    """
    zone = ZoneInfo(timezone)
    kind = chosen_kind(parsed)
    if language == "en":
        notes: list[str] = []
        if Role.TIMESTAMP in resolve_columns(parsed.headers).columns and kind is not ValueKind.COUNTER:
            notes.append("Timestamps mark interval starts. Long gaps stay missing.")
        if parsed.has_naive_timestamps:
            notes.append(f"Timestamps without an offset use {timezone}.")
        if kind is ValueKind.AVERAGE_POWER and parsed.answers.power_meaning is PowerMeaning.AVERAGE:
            notes.append("Average power × duration gives energy. For example, 100 W for 30 minutes gives 50 Wh.")
        if parsed.had_bom:
            notes.append("The UTF-8 byte order mark was skipped.")
        notes.append(
            "Columns use semicolons and decimals use commas."
            if parsed.delimiter == ";"
            else "Columns use commas. Use decimal points or quote values with a decimal comma."
        )
        if parsed.ignored_columns:
            notes.append(bound_text(f"Unused columns: {', '.join(parsed.ignored_columns)}."))
        if parsed.blank_lines:
            notes.append(f"Blank lines excluded from the data row count: {parsed.blank_lines}.")
        notes.extend(_counter_notes(staged, zone, language))
        after_now = sum(row_span(row)[1] > now for row in staged)
        if after_now:
            notes.append(f"{after_now} rows end after workspace time and are excluded from the summary.")
        return notes
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
    assumptions += _counter_notes(staged, zone, language)
    after_now = sum(row_span(row)[1] > now for row in staged)
    if after_now:
        assumptions.append(
            f"{after_now} baris berakhir setelah waktu ruang kerja {_date_time(now.astimezone(zone), language)}; "
            "baris itu belum dihitung pada ringkasan."
        )
    return assumptions
