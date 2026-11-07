"""Assumptions listed before confirmation, with exact text and order."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from app.imports.model.models import MeaningAnswers, PowerMeaning, RowStatus
from app.imports.service.assumptions import build_assumptions
from app.imports.service.classify import file_columns, stage_row

NOW = datetime(2030, 1, 1, tzinfo=UTC)
TIMEZONE = "Asia/Jakarta"
DELIMITER_COMMA = "Pemisah kolom: koma; titik sebagai desimal, koma desimal hanya dalam tanda kutip."
DELIMITER_SEMICOLON = "Pemisah kolom: titik koma; koma sebagai desimal."
TIMESTAMP_INFERRED = (
    "Timestamp adalah awal interval; setiap baris mencakup interval yang disimpulkan per sumber, "
    "termasuk baris terakhir. Jeda panjang tetap menjadi data kosong."
)
TIMESTAMP_DECLARED = (
    "Timestamp adalah awal interval; setiap baris mencakup interval yang disimpulkan atau diisi per sumber, "
    "termasuk baris terakhir. Jeda panjang tetap menjadi data kosong."
)
NAIVE = "Waktu tanpa offset dibaca sebagai Asia/Jakarta."
POWER = "Daya rata-rata interval × durasi = energi (100 W selama 30 menit = 50 Wh)."
BOM = "BOM UTF-8 dilewati."


def _assumptions(
    parse_text: Callable, text: str | bytes, *, answers: MeaningAnswers | None = None, now: datetime = NOW
) -> list[str]:
    parsed, rows = parse_text(text, answers=answers or MeaningAnswers(timezone_confirmed=True))
    columns = file_columns(parsed)
    staged = [stage_row(row, columns) for row in rows if row.status is RowStatus.PARSED]
    return build_assumptions(parsed, staged, now=now, timezone=TIMEZONE)


def test_explicit_offsets_state_only_the_delimiter(parse_text: Callable) -> None:
    """
    Condition:
    - Explicit intervals with offsets, in a plain comma file.

    Expected:
    - Only the delimiter is assumed.
    """
    text = "interval_start,interval_end,asset,energy_wh\n2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,A,1\n"

    assert _assumptions(parse_text, text) == [DELIMITER_COMMA]


def test_every_row_of_the_table_in_order(parse_text: Callable) -> None:
    """
    Condition:
    - A BOM, a semicolon file, naive timestamps, confirmed average power, an extra column and a blank line, with a
      row ending after the workspace's product time.

    Expected:
    - Each assumption appears with its exact text, in the table's order.
    """
    text = (
        "\ufefftimestamp;asset;daya_w;catatan;lokasi\n"
        "2026-10-20 00:00;A;100;x;y\n"
        "\n"
        "2026-10-20 01:00;A;100;x;y\n"
        "2026-10-20 02:00;A;100;x;y\n"
    )
    answers = MeaningAnswers(timezone_confirmed=True, power_meaning=PowerMeaning.AVERAGE)
    now = datetime(2026, 10, 19, 17, 30, tzinfo=UTC)

    assert _assumptions(parse_text, text, answers=answers, now=now) == [
        TIMESTAMP_INFERRED,
        NAIVE,
        POWER,
        BOM,
        DELIMITER_SEMICOLON,
        "Kolom tidak dipakai: catatan, lokasi.",
        "1 baris kosong tidak dihitung sebagai baris data.",
        "3 baris berakhir setelah waktu ruang kerja 20 Oktober 2026 00.30; baris itu belum dihitung pada ringkasan.",
    ]


def test_a_declared_duration_changes_the_timestamp_text(parse_text: Callable) -> None:
    """
    Condition:
    - A stream in the file has a declared duration.

    Expected:
    - The timestamp assumption says durations were inferred or filled in.
    """
    text = "timestamp,asset,energy_wh\n2026-10-20T00:00:00+07:00,A,1\n"

    found = _assumptions(parse_text, text, answers=MeaningAnswers(interval_minutes={"a": 60}))

    assert found[0] == TIMESTAMP_DECLARED


def test_a_duration_for_a_stream_outside_the_file_changes_nothing(parse_text: Callable) -> None:
    """
    Condition:
    - A declared duration names a stream the file does not hold.

    Expected:
    - The timestamp assumption keeps its inferred text.
    """
    text = "timestamp,asset,energy_wh\n2026-10-20T00:00:00+07:00,A,1\n2026-10-20T01:00:00+07:00,A,1\n"

    found = _assumptions(parse_text, text, answers=MeaningAnswers(interval_minutes={"lain": 60}))

    assert found[0] == TIMESTAMP_INFERRED


def test_unconfirmed_power_is_not_stated_as_average(parse_text: Callable) -> None:
    """
    Condition:
    - A power file whose meaning is unanswered, then answered as instantaneous.

    Expected:
    - The average-power assumption stays out, because nobody confirmed it.
    """
    text = "interval_start,interval_end,asset,daya_w\n2026-10-20T00:00:00+07:00,2026-10-20T00:30:00+07:00,A,100\n"

    assert POWER not in _assumptions(parse_text, text, answers=MeaningAnswers())
    assert POWER not in _assumptions(parse_text, text, answers=MeaningAnswers(power_meaning=PowerMeaning.INSTANTANEOUS))


def test_counter_at_27b_states_the_decrease_and_the_first_reading(parse_text: Callable) -> None:
    """
    Condition:
    - AT-27b's counter: 100, 130 and 5 Wh in Asia/Jakarta.

    Expected:
    - The reset interval is ``tidak diketahui``, and the first reading is an anchor. A counter states no interval.
    """
    text = (
        "timestamp,perangkat,cumulative_wh\n"
        "2026-10-20 00:00,Mesin,100\n2026-10-20 01:00,Mesin,130\n2026-10-20 02:00,Mesin,5\n"
    )

    assert _assumptions(parse_text, text) == [
        NAIVE,
        DELIMITER_COMMA,
        "Penghitung Mesin kembali ke nilai lebih kecil pada 20 Oktober 2026 02.00: "
        "interval 20 Oktober 2026 01.00–02.00 tidak diketahui (segmen baru).",
        "Pembacaan pertama Mesin menjadi titik awal penghitung, bukan energi.",
    ]


def test_counter_notes_are_grouped_per_stream(parse_text: Callable) -> None:
    """
    Condition:
    - Two counter streams in one file, the second with rows out of time order.

    Expected:
    - Each stream's notes stay together in first-seen order, and points are read in time order.
    """
    text = (
        "timestamp,asset,cumulative_wh\n"
        "2026-10-20T00:00:00+07:00,Satu,1\n"
        "2026-10-20T02:00:00+07:00,Dua,7\n"
        "2026-10-20T01:00:00+07:00,Dua,9\n"
    )

    assert _assumptions(parse_text, text)[1:] == [
        "Pembacaan pertama Satu menjadi titik awal penghitung, bukan energi.",
        "Penghitung Dua kembali ke nilai lebih kecil pada 20 Oktober 2026 02.00: "
        "interval 20 Oktober 2026 01.00–02.00 tidak diketahui (segmen baru).",
        "Pembacaan pertama Dua menjadi titik awal penghitung, bukan energi.",
    ]


@pytest.mark.parametrize(
    ("start", "end", "gap"),
    [
        ("2026-10-20T01:00:00", "2026-10-20T02:00:00", "20 Oktober 2026 01.00–02.00"),
        ("2026-10-20T22:00:00", "2026-10-21T00:00:00", "20 Oktober 2026 22.00–24.00"),
        ("2026-10-20T00:00:00", "2026-10-21T00:00:00", "20 Oktober 2026"),
        ("2026-10-19T00:00:00", "2026-10-21T00:00:00", "19–20 Oktober 2026"),
        ("2026-09-30T00:00:00", "2026-10-02T00:00:00", "30 September–1 Oktober 2026"),
        ("2026-12-31T00:00:00", "2027-01-02T00:00:00", "31 Desember 2026–1 Januari 2027"),
        ("2026-10-20T22:00:00", "2026-10-21T02:00:00", "20 Oktober 2026 22.00–21 Oktober 2026 02.00"),
    ],
    ids=["same_day", "to_midnight", "one_day", "same_month", "across_months", "across_years", "cross_day"],
)
def test_counter_gap_forms_match_the_prototype(parse_text: Callable, start: str, end: str, gap: str) -> None:
    """
    Condition:
    - A counter reset across each shape of ``fmtGap`` in ``domain.js``.

    Expected:
    - The gap renders as the prototype does.
    """
    text = f"timestamp,asset,cumulative_wh\n{start}+07:00,A,9\n{end}+07:00,A,1\n"

    assert f"interval {gap} tidak diketahui" in _assumptions(parse_text, text)[1]


def test_counter_with_a_single_reading_states_its_anchor(parse_text: Callable) -> None:
    """
    Condition:
    - D25: a one-row counter file.

    Expected:
    - The first-reading assumption is stated.
    """
    text = "timestamp,asset,cumulative_wh\n2026-10-20T00:00:00+07:00,A,1\n"

    assert _assumptions(parse_text, text)[-1] == "Pembacaan pertama A menjadi titik awal penghitung, bukan energi."


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 10, 19, 17, 59, 59, tzinfo=UTC), True),
        (datetime(2026, 10, 19, 18, tzinfo=UTC), False),
    ],
    ids=["one_row_ends_after_now", "ending_exactly_at_now_counts"],
)
def test_rows_after_product_time_follow_the_read_rule(parse_text: Callable, now: datetime, expected: bool) -> None:
    """
    Condition:
    - One interval ends at 01.00 WIB, and product time is just before that, or exactly that.

    Expected:
    - It is listed only when it ends after now, as reads include an interval ending exactly at now.
    """
    text = "interval_start,interval_end,asset,energy_wh\n2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,A,1\n"

    found = _assumptions(parse_text, text, now=now)

    assert any("berakhir setelah waktu ruang kerja" in item for item in found) is expected


def test_a_long_list_of_ignored_columns_is_bounded(parse_text: Callable) -> None:
    """
    Condition:
    - An ignored header of 100,000 characters.

    Expected:
    - The assumption stays bounded and still ends with its closing text.
    """
    text = f"interval_start,interval_end,asset,energy_wh,{'x' * 100_000}\n"
    text += "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,A,1,y\n"

    found = _assumptions(parse_text, text)[1]

    assert found.startswith("Kolom tidak dipakai: xxx")
    assert len(found) <= 500
