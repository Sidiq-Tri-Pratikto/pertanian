"""The assembled parser: file-level answers first, then one row at a time."""

import io
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from app.imports.model.models import (
    IntervalBasis,
    MeaningAnswers,
    MeaningQuestion,
    ParsedFile,
    PowerMeaning,
    QuestionKind,
    RowReason,
    RowResult,
    RowStatus,
    StructuralError,
    StructuralReason,
    ValueKind,
)
from app.imports.service.parser import iter_rows, parse

type ParseText = Callable[..., tuple[ParsedFile, list[RowResult]]]

AT_28 = '﻿waktu;alat;wh\r\n2026-10-20 00:00;"Lampu; Gudang";12,5\r\n\r\n2026-10-20 01:00;"Lampu; Gudang";1.250,5\r\n'
EXPLICIT = (
    "interval_start,interval_end,asset,energy_wh\n"
    "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,10\n"
    "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Kulkas,50\n"
)


def test_read_timestamp_aliases_mean_interval_energy(parse_text: ParseText) -> None:
    """
    Condition:
    - ``timestamp,perangkat,energi_wh`` with naive times and no answers (US1 scenario 1).

    Expected:
    - Aliases resolve, values mean interval Wh, and rows wait for answers with their value kept.
    """
    parsed, rows = parse_text("timestamp,perangkat,energi_wh\n2026-10-20 00:00,Router,10\n2026-10-20 01:00,Router,10\n")
    assert parsed.ok
    assert parsed.value_kinds == [ValueKind.INTERVAL_ENERGY]
    assert (rows[0].kind, rows[0].unit, rows[0].value_milli) == (ValueKind.INTERVAL_ENERGY, "Wh", 10000)
    assert (rows[0].asset_name, rows[0].stream_key) == ("Router", "router")
    assert rows[0].status is RowStatus.PENDING


def test_read_explicit_intervals_are_used(parse_text: ParseText) -> None:
    """
    Condition:
    - The explicit-interval block from PRD §10.2 (US1 scenario 2).

    Expected:
    - Rows are parsed with those bounds in UTC, basis ``explicit``, and no question asks for a duration.
    """
    parsed, rows = parse_text(EXPLICIT)
    assert parsed.questions == []
    assert parsed.asset_names == ["Router", "Kulkas"]
    assert [row.status for row in rows] == [RowStatus.PARSED, RowStatus.PARSED]
    assert rows[0].interval_start == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
    assert rows[0].interval_end == datetime(2026, 10, 19, 18, 0, tzinfo=UTC)
    assert rows[0].interval_basis is IntervalBasis.EXPLICIT
    assert (rows[0].raw_start, rows[0].raw_end) == ("2026-10-20T00:00:00+07:00", "2026-10-20T01:00:00+07:00")


def test_read_bom_semicolons_quotes_and_decimal_commas_keep_values_and_names(parse_text: ParseText) -> None:
    """
    Condition:
    - A BOM, semicolons, CRLF, a blank line, a quoted name holding the delimiter and decimal commas (US1 scenario 3).

    Expected:
    - Raw values and names are unchanged, values are exact, and the blank line is counted.
    """
    parsed, rows = parse_text(AT_28)
    assert (parsed.delimiter, parsed.had_bom, parsed.blank_lines, parsed.total_rows) == (";", True, 1, 2)
    assert parsed.asset_names == ["Lampu; Gudang"]
    assert [row.raw_value for row in rows] == ["12,5", "1.250,5"]
    assert [row.value_milli for row in rows] == [12500, 1250500]
    assert rows[1].asset_name == "Lampu; Gudang"


def test_read_cumulative_column_uses_the_counter_path(parse_text: ParseText) -> None:
    """
    Condition:
    - ``cumulative_wh`` with offset timestamps (US1 scenario 4).

    Expected:
    - Rows are counter points with a capture time and no interval; never interval energy.
    """
    parsed, rows = parse_text(
        "timestamp,perangkat,cumulative_wh\n2026-10-20T00:00:00+07:00,Mesin,100\n2026-10-20T01:00:00+07:00,Mesin,130\n"
    )
    assert parsed.value_kinds == [ValueKind.COUNTER]
    assert rows[0].kind is ValueKind.COUNTER
    assert rows[0].status is RowStatus.PARSED
    assert rows[0].measured_at == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
    assert (rows[0].interval_start, rows[0].interval_end, rows[0].interval_basis) == (None, None, None)


def test_read_extra_columns_land_in_ignored_columns(parse_text: ParseText) -> None:
    """
    Condition:
    - A ``catatan`` column beside the known ones.

    Expected:
    - It is reported as ignored, and the row reads normally.
    """
    parsed, rows = parse_text(
        "interval_start,interval_end,asset,catatan,energy_wh\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,rusak,10\n"
    )
    assert parsed.headers == ["interval_start", "interval_end", "asset", "catatan", "energy_wh"]
    assert parsed.ignored_columns == ["catatan"]
    assert rows[0].value_milli == 10000


@pytest.mark.parametrize(
    ("delimiter", "raw"), [(",", "10"), (",", "10.0"), (",", "10.000"), (";", "10"), (";", "10,000")]
)
def test_read_canonical_value_is_one_text_for_every_spelling(parse_text: ParseText, delimiter: str, raw: str) -> None:
    """
    Condition:
    - One number in several spellings.

    Expected:
    - ``value`` formats to ``10.000`` each time, so a reimport is no revision in 006.
    """
    header = delimiter.join(["interval_start", "interval_end", "asset", "wh"])
    row = delimiter.join(["2026-10-20T00:00:00+07:00", "2026-10-20T01:00:00+07:00", "A", raw])
    _, rows = parse_text(f"{header}\n{row}\n")
    assert format(rows[0].value, "f") == "10.000"
    assert rows[0].raw_value == raw


def test_read_is_repeatable_and_leaves_the_source_open() -> None:
    """
    Condition:
    - One source parsed twice and read twice.

    Expected:
    - Equal output each time, and the caller's source stays open.
    """
    source = io.BytesIO(EXPLICIT.encode())
    first, second = parse(source, site_timezone="Asia/Jakarta"), parse(source, site_timezone="Asia/Jakarta")
    assert first == second
    assert list(iter_rows(source, first)) == list(iter_rows(source, first))
    assert not source.closed


def test_read_rows_arrive_one_at_a_time() -> None:
    """
    Condition:
    - One row taken from a file, and the generator closed early.

    Expected:
    - Row 1 arrives with a correct number, and the source stays open.
    """
    source = io.BytesIO(EXPLICIT.encode())
    parsed = parse(source, site_timezone="Asia/Jakarta")
    rows = iter_rows(source, parsed)
    first = next(rows)
    assert (first.data_row, first.file_line) == (1, 2)
    rows.close()
    assert not source.closed


POWER_MEANING_MESSAGE = "Konfirmasi arti kolom daya: rata-rata selama interval atau daya sesaat."
POWER_BLOCKED_MESSAGE = (
    "Daya sesaat tidak dapat diubah menjadi energi. Impor diblokir; "
    "gunakan data energi interval atau daya rata-rata interval."
)
VALUE_KIND_MESSAGE = (
    "Berkas memiliki lebih dari satu kolom nilai. Pilih satu jenis nilai; nilai energi dan daya tidak dijumlahkan."
)
DURATION_RANGE_MESSAGE = "Panjang interval harus bilangan bulat 1–1440 menit."
AVERAGE = MeaningAnswers(power_meaning=PowerMeaning.AVERAGE)
CONFIRMED = MeaningAnswers(timezone_confirmed=True)
OFFSET_START = "2026-10-20T00:00:00+07:00"
OFFSET_END = "2026-10-20T00:30:00+07:00"


def _kinds(parsed: ParsedFile) -> list[QuestionKind]:
    return [question.kind for question in parsed.questions]


def _offset_rows(hours: list[int], name: str = "a") -> str:
    return "".join(f"2026-10-20T{hour:02}:00:00+07:00,{name},1\n" for hour in hours)


@pytest.mark.parametrize("header", ["average_power_w", "daya_w", "watt", "daya", "power_w"])
def test_meaning_every_power_alias_waits_for_a_confirmed_meaning(parse_text: ParseText, header: str) -> None:
    """
    Condition:
    - Any average-power alias with no answer (US2 scenario 1, D19).

    Expected:
    - One question with the exact text. Rows stay pending with their value kept.
    """
    parsed, rows = parse_text(f"interval_start,interval_end,asset,{header}\n{OFFSET_START},{OFFSET_END},Pompa,100\n")
    assert parsed.questions == [MeaningQuestion(kind=QuestionKind.POWER_MEANING, message=POWER_MEANING_MESSAGE)]
    assert rows[0].status is RowStatus.PENDING
    assert (rows[0].kind, rows[0].unit, rows[0].value_milli) == (ValueKind.AVERAGE_POWER, "W", 100000)


def test_meaning_instantaneous_power_stays_blocked(parse_text: ParseText) -> None:
    """
    Condition:
    - The user says the power column is instantaneous.

    Expected:
    - The blocked message stays as a question and rows stay pending. It never integrates, and no other kind appears.
    """
    parsed, rows = parse_text(
        f"interval_start,interval_end,asset,power_w\n{OFFSET_START},{OFFSET_END},Pompa,100\n",
        answers=MeaningAnswers(power_meaning=PowerMeaning.INSTANTANEOUS),
    )
    assert parsed.questions == [MeaningQuestion(kind=QuestionKind.POWER_MEANING, message=POWER_BLOCKED_MESSAGE)]
    assert rows[0].status is RowStatus.PENDING
    assert rows[0].kind is ValueKind.AVERAGE_POWER


def test_meaning_average_power_reads_once_confirmed(parse_text: ParseText) -> None:
    """
    Condition:
    - The user confirms an interval average.

    Expected:
    - No question, rows parsed in watts. The parser never converts to energy; that is 006's.
    """
    parsed, rows = parse_text(
        f"interval_start,interval_end,asset,power_w\n{OFFSET_START},{OFFSET_END},Pompa,100\n", answers=AVERAGE
    )
    assert parsed.questions == []
    assert (rows[0].status, rows[0].unit, rows[0].value_milli) == (RowStatus.PARSED, "W", 100000)
    assert rows[0].interval_end - rows[0].interval_start == timedelta(minutes=30)


@pytest.mark.parametrize(
    ("second_header", "second_kind"),
    [("average_power_w", ValueKind.AVERAGE_POWER), ("cumulative_wh", ValueKind.COUNTER)],
)
def test_meaning_competing_value_columns_wait_for_a_choice(
    parse_text: ParseText, second_header: str, second_kind: ValueKind
) -> None:
    """
    Condition:
    - Two value roles and no valid answer (US2 scenario 2, D17).

    Expected:
    - A ``value_kind`` question with exact text, and pending rows that read neither column.
    """
    parsed, rows = parse_text(f"timestamp,asset,energy_wh,{second_header}\n{OFFSET_START},A,10,20\n")
    assert parsed.value_kinds == [ValueKind.INTERVAL_ENERGY, second_kind]
    assert parsed.questions[0] == MeaningQuestion(kind=QuestionKind.VALUE_KIND, message=VALUE_KIND_MESSAGE)
    assert (rows[0].status, rows[0].kind, rows[0].value_milli) == (RowStatus.PENDING, None, None)


def test_meaning_answer_reads_only_the_chosen_column(parse_text: ParseText) -> None:
    """
    Condition:
    - Two value columns, each holding bad text in the row the other column is good.

    Expected:
    - Each answer reads its own column only, so the other column's text is no error.
    """
    text = (
        "interval_start,interval_end,asset,energy_wh,average_power_w\n"
        f"{OFFSET_START},{OFFSET_END},A,10,dua\n"
        f"{OFFSET_START},{OFFSET_END},B,dua,20\n"
    )
    _, energy = parse_text(text, answers=MeaningAnswers(value_kind=ValueKind.INTERVAL_ENERGY))
    assert (energy[0].status, energy[0].kind, energy[0].value_milli) == (
        RowStatus.PARSED,
        ValueKind.INTERVAL_ENERGY,
        10000,
    )
    assert energy[1].status is RowStatus.INVALID
    _, power = parse_text(
        text, answers=MeaningAnswers(value_kind=ValueKind.AVERAGE_POWER, power_meaning=PowerMeaning.AVERAGE)
    )
    assert power[0].status is RowStatus.INVALID
    assert (power[1].status, power[1].kind, power[1].value_milli) == (RowStatus.PARSED, ValueKind.AVERAGE_POWER, 20000)


def test_meaning_answer_chooses_between_energy_and_counter(parse_text: ParseText) -> None:
    """
    Condition:
    - Energy and counter columns, each holding bad text in the row the other is good.

    Expected:
    - Each answer reads its own column, with counter rows as points and energy rows as intervals.
    """
    text = (
        "timestamp,asset,energy_wh,cumulative_wh\n"
        "2026-10-20T00:00:00+07:00,A,10,dua\n"
        "2026-10-20T01:00:00+07:00,A,dua,20\n"
        "2026-10-20T02:00:00+07:00,A,30,40\n"
    )
    _, energy = parse_text(text, answers=MeaningAnswers(value_kind=ValueKind.INTERVAL_ENERGY))
    assert [row.status for row in energy] == [RowStatus.PARSED, RowStatus.INVALID, RowStatus.PARSED]
    assert (energy[0].kind, energy[0].value_milli, energy[0].measured_at) == (ValueKind.INTERVAL_ENERGY, 10000, None)
    parsed, counter = parse_text(text, answers=MeaningAnswers(value_kind=ValueKind.COUNTER))
    assert parsed.cadences == {}
    assert parsed.questions == []
    assert [row.status for row in counter] == [RowStatus.INVALID, RowStatus.PARSED, RowStatus.PARSED]
    assert (counter[1].kind, counter[1].value_milli, counter[1].interval_start) == (ValueKind.COUNTER, 20000, None)


def test_meaning_choosing_power_then_asks_what_power_means(parse_text: ParseText) -> None:
    """
    Condition:
    - The user chooses the power column but has not said what it means.

    Expected:
    - The choice is settled and the power question opens.
    """
    parsed, rows = parse_text(
        f"interval_start,interval_end,asset,energy_wh,power_w\n{OFFSET_START},{OFFSET_END},A,10,20\n",
        answers=MeaningAnswers(value_kind=ValueKind.AVERAGE_POWER),
    )
    assert _kinds(parsed) == [QuestionKind.POWER_MEANING]
    assert rows[0].status is RowStatus.PENDING


def test_meaning_answer_naming_an_absent_kind_leaves_the_question_open(parse_text: ParseText) -> None:
    """
    Condition:
    - Energy and power columns, answered with a counter.

    Expected:
    - The ``value_kind`` question stays, and rows stay pending.
    """
    parsed, rows = parse_text(
        f"interval_start,interval_end,asset,energy_wh,power_w\n{OFFSET_START},{OFFSET_END},A,10,20\n",
        answers=MeaningAnswers(value_kind=ValueKind.COUNTER),
    )
    assert _kinds(parsed) == [QuestionKind.VALUE_KIND]
    assert rows[0].kind is None


def test_meaning_naive_times_wait_for_the_timezone(parse_text: ParseText) -> None:
    """
    Condition:
    - Naive timestamps and no confirmation (US2 scenario 3).

    Expected:
    - The exact question, ``has_naive_timestamps``, pending rows with no instant, and the raw time kept.
    """
    parsed, rows = parse_text("timestamp,asset,wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n")
    assert parsed.has_naive_timestamps is True
    assert parsed.questions == [
        MeaningQuestion(
            kind=QuestionKind.TIMEZONE,
            message="Waktu tanpa zona waktu. Konfirmasi bahwa waktu dibaca sebagai Asia/Jakarta.",
        )
    ]
    assert rows[0].status is RowStatus.PENDING
    assert (rows[0].interval_start, rows[0].interval_end, rows[0].measured_at) == (None, None, None)
    assert rows[0].raw_start == "2026-10-20 00:00"


def test_meaning_confirmed_timezone_gives_utc_instants(parse_text: ParseText) -> None:
    """
    Condition:
    - The same naive file after confirmation.

    Expected:
    - No question, and rows parsed in UTC with the inferred duration.
    """
    parsed, rows = parse_text("timestamp,asset,wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n", answers=CONFIRMED)
    assert parsed.questions == []
    assert rows[0].status is RowStatus.PARSED
    assert rows[0].interval_start == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
    assert rows[0].interval_end == datetime(2026, 10, 19, 18, 0, tzinfo=UTC)
    assert rows[0].interval_basis is IntervalBasis.INFERRED


def test_meaning_site_timezone_changes_both_the_question_and_the_instant(parse_text: ParseText) -> None:
    """
    Condition:
    - A naive file read with ``Asia/Makassar`` as the site's timezone.

    Expected:
    - The question names that zone, and confirmed rows use its offset, never a hard-coded one.
    """
    text = "timestamp,asset,wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n"
    parsed, _ = parse_text(text, site_timezone="Asia/Makassar")
    assert parsed.questions[0].message.endswith("dibaca sebagai Asia/Makassar.")
    _, rows = parse_text(text, site_timezone="Asia/Makassar", answers=CONFIRMED)
    assert rows[0].interval_start == datetime(2026, 10, 19, 16, 0, tzinfo=UTC)


def test_meaning_offset_times_ask_nothing(parse_text: ParseText) -> None:
    """
    Condition:
    - Regular offset timestamps with no answers.

    Expected:
    - No question, and rows parsed with their explicit instant.
    """
    parsed, rows = parse_text("timestamp,asset,wh\n" + _offset_rows([0, 1, 2]))
    assert parsed.has_naive_timestamps is False
    assert parsed.questions == []
    assert [row.status for row in rows] == [RowStatus.PARSED] * 3


def test_meaning_naive_end_beside_an_offset_start_still_asks(parse_text: ParseText) -> None:
    """
    Condition:
    - An offset ``interval_start`` and a naive ``interval_end`` (D15).

    Expected:
    - The timezone question is asked and the row waits, then resolves once confirmed.
    """
    text = f"interval_start,interval_end,asset,wh\n{OFFSET_START},2026-10-20 00:30,A,1\n"
    parsed, rows = parse_text(text)
    assert parsed.has_naive_timestamps is True
    assert _kinds(parsed) == [QuestionKind.TIMEZONE]
    assert rows[0].status is RowStatus.PENDING
    _, confirmed = parse_text(text, answers=CONFIRMED)
    assert confirmed[0].status is RowStatus.PARSED
    assert confirmed[0].interval_end == datetime(2026, 10, 19, 17, 30, tzinfo=UTC)
    assert confirmed[0].interval_basis is IntervalBasis.EXPLICIT


@pytest.mark.parametrize(
    "rows_text",
    [_offset_rows([0]), _offset_rows([0, 1]) + "2026-10-20T01:15:00+07:00,a,1\n2026-10-20T03:00:00+07:00,a,1\n"],
    ids=["one_row", "irregular"],
)
def test_meaning_stream_without_a_cadence_needs_a_duration(parse_text: ParseText, rows_text: str) -> None:
    """
    Condition:
    - A timestamp-only stream with one row or with irregular gaps (US2 scenario 4).

    Expected:
    - A question naming the stream, a None cadence, and pending rows.
    """
    parsed, rows = parse_text("timestamp,asset,wh\n" + rows_text)
    assert parsed.cadences == {"a": None}
    assert parsed.questions == [
        MeaningQuestion(
            kind=QuestionKind.INTERVAL_DURATION,
            message=(
                "Interval tidak dapat disimpulkan untuk: a (satu baris atau jarak tidak teratur). Isi panjang interval."
            ),
            streams=("a",),
        )
    ]
    assert {row.status for row in rows} == {RowStatus.PENDING}


def test_meaning_declared_duration_gives_one_interval_per_timestamp(parse_text: ParseText) -> None:
    """
    Condition:
    - A one-row stream with a declared 60 minutes.

    Expected:
    - ``[t, t+60m)`` with basis ``declared`` and no question.
    """
    parsed, rows = parse_text(
        "timestamp,asset,wh\n" + _offset_rows([0]), answers=MeaningAnswers(interval_minutes={"a": 60})
    )
    assert parsed.questions == []
    assert rows[0].status is RowStatus.PARSED
    assert rows[0].interval_start == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
    assert rows[0].interval_end == datetime(2026, 10, 19, 18, 0, tzinfo=UTC)
    assert rows[0].interval_basis is IntervalBasis.DECLARED


@pytest.mark.parametrize("minutes", [0, -1, 1441])
def test_meaning_declared_duration_out_of_range_stays_a_question(parse_text: ParseText, minutes: int) -> None:
    """
    Condition:
    - A declared duration outside 1 to 1440 minutes.

    Expected:
    - The exact range message naming the stream, and rows stay pending. It never falls back to a cadence.
    """
    parsed, rows = parse_text(
        "timestamp,asset,wh\n" + _offset_rows([0, 1, 2]), answers=MeaningAnswers(interval_minutes={"a": minutes})
    )
    assert parsed.questions == [
        MeaningQuestion(kind=QuestionKind.INTERVAL_DURATION, message=DURATION_RANGE_MESSAGE, streams=("a",))
    ]
    assert {row.status for row in rows} == {RowStatus.PENDING}


@pytest.mark.parametrize("minutes", [1, 1440])
def test_meaning_declared_duration_accepts_its_bounds(parse_text: ParseText, minutes: int) -> None:
    """
    Condition:
    - A declared duration at either end of the range.

    Expected:
    - It applies, with no question.
    """
    parsed, rows = parse_text(
        "timestamp,asset,wh\n" + _offset_rows([0]), answers=MeaningAnswers(interval_minutes={"a": minutes})
    )
    assert parsed.questions == []
    assert rows[0].interval_end - rows[0].interval_start == timedelta(minutes=minutes)


def test_meaning_explicit_bounds_never_ask_for_a_duration(parse_text: ParseText) -> None:
    """
    Condition:
    - One row with explicit bounds.

    Expected:
    - No question and no cadence, because nothing needs inferring.
    """
    parsed, rows = parse_text(f"interval_start,interval_end,asset,wh\n{OFFSET_START},{OFFSET_END},A,1\n")
    assert parsed.questions == []
    assert parsed.cadences == {}
    assert rows[0].status is RowStatus.PARSED


def _two_sources() -> str:
    quarter = "".join(f"2026-10-20T00:{minute:02}:00+07:00,Mesin,S1,1\n" for minute in range(0, 60, 15))
    hours = [*range(12), 20]
    hourly = "".join(f"2026-10-20T{hour:02}:00:00+07:00,Pompa,S2,1\n" for hour in hours)
    return "timestamp,asset,source,wh\n" + quarter + hourly


def test_meaning_each_source_keeps_its_own_cadence(parse_text: ParseText) -> None:
    """
    Condition:
    - Sources S1 every 15 minutes and S2 hourly with one long gap (US2 scenario 5).

    Expected:
    - Each keeps its cadence, every row including the last spans it, and the gap stays uncovered.
    """
    parsed, rows = parse_text(_two_sources())
    assert parsed.cadences == {"s1": timedelta(minutes=15), "s2": timedelta(hours=1)}
    assert parsed.questions == []
    for row in rows:
        expected = timedelta(minutes=15) if row.stream_key == "s1" else timedelta(hours=1)
        assert row.interval_end - row.interval_start == expected
        assert row.interval_basis is IntervalBasis.INFERRED
    s2 = [row for row in rows if row.stream_key == "s2"]
    before_gap, last = s2[-2], s2[-1]
    assert before_gap.interval_end == before_gap.interval_start + timedelta(hours=1)
    assert before_gap.interval_end < last.interval_start


def test_meaning_declaring_one_stream_leaves_the_others_alone(parse_text: ParseText) -> None:
    """
    Condition:
    - A third one-row stream, with 60 minutes declared for it alone (D20).

    Expected:
    - That stream uses 60 minutes, and the 15-minute source stays at 15.
    """
    parsed, rows = parse_text(
        _two_sources() + "2026-10-20T00:00:00+07:00,Lain,C,1\n", answers=MeaningAnswers(interval_minutes={"c": 60})
    )
    assert parsed.questions == []
    assert parsed.cadences["c"] is None
    by_stream = {row.stream_key: row for row in rows}
    assert by_stream["c"].interval_end - by_stream["c"].interval_start == timedelta(minutes=60)
    assert by_stream["c"].interval_basis is IntervalBasis.DECLARED
    assert by_stream["s1"].interval_end - by_stream["s1"].interval_start == timedelta(minutes=15)
    assert by_stream["s1"].interval_basis is IntervalBasis.INFERRED


def test_meaning_stream_key_ignores_case_and_falls_back_to_the_asset(parse_text: ParseText) -> None:
    """
    Condition:
    - One stream spelled in several ways, and a blank source cell.

    Expected:
    - Spellings join one stream, and a blank source uses the asset name.
    """
    parsed, rows = parse_text(
        "timestamp,asset,source,wh\n"
        "2026-10-20T00:00:00+07:00,A,S1,1\n"
        "2026-10-20T01:00:00+07:00,A, s1 ,1\n"
        "2026-10-20T02:00:00+07:00,A,S1,1\n"
        "2026-10-20T00:00:00+07:00,Pompa,,1\n"
        "2026-10-20T01:00:00+07:00,POMPA,,1\n"
    )
    assert parsed.cadences == {"s1": timedelta(hours=1), "pompa": timedelta(hours=1)}
    assert [row.stream_key for row in rows] == ["s1", "s1", "s1", "pompa", "pompa"]
    assert [row.asset_name for row in rows][3:] == ["Pompa", "POMPA"]


def test_meaning_counters_stay_points_with_no_cadence(parse_text: ParseText) -> None:
    """
    Condition:
    - Timestamp-only counter readings, including a decrease (US2 scenario 6).

    Expected:
    - No cadence and no duration question. Each row is a capture time and an unchanged reading.
    """
    parsed, rows = parse_text(
        "timestamp,asset,cumulative_wh\n"
        "2026-10-20T00:00:00+07:00,Mesin,100\n"
        "2026-10-20T01:00:00+07:00,Mesin,130\n"
        "2026-10-20T02:00:00+07:00,Mesin,5\n"
    )
    assert parsed.cadences == {}
    assert parsed.questions == []
    assert [row.value_milli for row in rows] == [100000, 130000, 5000]
    assert rows[0].measured_at == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
    assert rows[0].interval_start is None


def test_meaning_cadence_uses_instants_across_a_clock_change(parse_text: ParseText) -> None:
    """
    Condition:
    - Hourly naive rows through New York's 2026-03-08 jump, before and after confirmation (D21).

    Expected:
    - Wall clocks disagree until confirmed. Once confirmed, the cadence is one hour and every interval is an hour.
    """
    text = "timestamp,asset,wh\n" + "".join(f"2026-03-08 {hour:02}:00,a,1\n" for hour in (0, 1, 3, 4))
    unconfirmed, _ = parse_text(text, site_timezone="America/New_York")
    assert unconfirmed.cadences == {"a": None}
    confirmed, rows = parse_text(text, site_timezone="America/New_York", answers=CONFIRMED)
    assert confirmed.cadences == {"a": timedelta(hours=1)}
    assert [row.interval_end - row.interval_start for row in rows] == [timedelta(hours=1)] * 4
    assert rows[1].interval_end == rows[2].interval_start


def test_meaning_nonexistent_and_ambiguous_times_are_row_errors_once_confirmed(parse_text: ParseText) -> None:
    """
    Condition:
    - A gap time and a fold time, in explicit bounds, once New York is confirmed.

    Expected:
    - Each is one invalid row with its reason. The file is not rejected and no time is guessed.
    """
    parsed, rows = parse_text(
        "interval_start,interval_end,asset,wh\n"
        "2026-03-08 02:30,2026-03-08 04:00,A,1\n"
        "2026-11-01 00:30,2026-11-01 01:30,A,1\n",
        site_timezone="America/New_York",
        answers=CONFIRMED,
    )
    assert parsed.ok
    assert [row.error.reason for row in rows] == [RowReason.TIME_NONEXISTENT, RowReason.TIME_AMBIGUOUS]
    assert [row.error.field for row in rows] == ["interval_start", "interval_end"]


def test_meaning_rows_with_bad_values_still_count_toward_cadence(parse_text: ParseText) -> None:
    """
    Condition:
    - Hourly rows where one has a negative value, one a bad value, one an extra column (D21).

    Expected:
    - The hourly cadence holds: a removed row would open a false two-hour gap.
    """
    parsed, rows = parse_text(
        "timestamp,asset,wh\n"
        "2026-10-20T00:00:00+07:00,a,1\n"
        "2026-10-20T01:00:00+07:00,a,-1\n"
        "2026-10-20T02:00:00+07:00,a,1\n"
        "2026-10-20T03:00:00+07:00,a,dua\n"
        "2026-10-20T04:00:00+07:00,a,1,x\n"
        "2026-10-20T05:00:00+07:00,a,1\n"
    )
    assert parsed.cadences == {"a": timedelta(hours=1)}
    assert [row.status for row in rows] == [
        RowStatus.PARSED,
        RowStatus.INVALID,
        RowStatus.PARSED,
        RowStatus.INVALID,
        RowStatus.INVALID,
        RowStatus.PARSED,
    ]


def test_meaning_questions_come_in_the_stated_order(parse_text: ParseText) -> None:
    """
    Condition:
    - A one-row naive file with two value columns, then the same file with power chosen.

    Expected:
    - ``value_kind``, ``timezone``, ``interval_duration``; then ``power_meaning``, ``timezone``, ``interval_duration``.
    """
    text = "timestamp,asset,energy_wh,power_w\n2026-10-20 00:00,A,1,2\n"
    parsed, _ = parse_text(text)
    assert _kinds(parsed) == [QuestionKind.VALUE_KIND, QuestionKind.TIMEZONE, QuestionKind.INTERVAL_DURATION]
    chosen, _ = parse_text(text, answers=MeaningAnswers(value_kind=ValueKind.AVERAGE_POWER))
    assert _kinds(chosen) == [QuestionKind.POWER_MEANING, QuestionKind.TIMEZONE, QuestionKind.INTERVAL_DURATION]


ENERGY_HEADER = "timestamp,asset,energy_wh\n"
START = "2026-10-20T00:00:00+07:00"
LATER = "2026-10-20T01:00:00+07:00"
BAD_ROW_TABLE = [
    (
        "timestamp,asset,wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,12,5\n",
        {},
        RowReason.COLUMN_COUNT,
        (2, 3, "baris"),
        "Baris data 2, baris: jumlah kolom 4 tidak sama dengan header (3). Koma desimal harus diberi tanda kutip, "
        'misalnya "12,5".',
    ),
    (
        "timestamp;asset;wh\n2026-10-20 00:00;A;1;2\n",
        {},
        RowReason.COLUMN_COUNT,
        (1, 2, "baris"),
        "Baris data 1, baris: jumlah kolom 4 tidak sama dengan header (3).",
    ),
    (
        f"timestamp,asset,wh\n{START}, ,1\n",
        {},
        RowReason.ASSET_EMPTY,
        (1, 2, "asset"),
        "Baris data 1, asset: nama perangkat kosong.",
    ),
    (
        f"timestamp,Perangkat,wh\n{START},{'X' * 61},1\n",
        {},
        RowReason.ASSET_TOO_LONG,
        (1, 2, "Perangkat"),
        "Baris data 1, Perangkat: nama lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.",
    ),
    (
        f"timestamp,asset,source,wh\n{START},A,{'S' * 61},1\n",
        {},
        RowReason.SOURCE_TOO_LONG,
        (1, 2, "source"),
        "Baris data 1, source: nama sumber lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.",
    ),
    (
        "timestamp,asset,wh\n2026-02-30,A,1\n",
        {},
        RowReason.TIME_FORMAT,
        (1, 2, "timestamp"),
        "Baris data 1, timestamp: format waktu tidak dikenali. "
        "Gunakan 2026-10-20 00:00 atau 2026-10-20T00:00:00+07:00.",
    ),
    (
        "timestamp,asset,wh\n2026-02-30 00:00,A,1\n",
        {},
        RowReason.TIME_IMPOSSIBLE,
        (1, 2, "timestamp"),
        "Baris data 1, timestamp: tanggal atau jam tidak ada (2026-02-30 00:00).",
    ),
    (
        "timestamp,asset,wh\n2026-03-08 02:30,A,1\n",
        {"site_timezone": "America/New_York", "answers": CONFIRMED},
        RowReason.TIME_NONEXISTENT,
        (1, 2, "timestamp"),
        "Baris data 1, timestamp: waktu lokal 2026-03-08 02:30 tidak ada di zona America/New_York. "
        "Tambahkan offset atau perbaiki waktunya.",
    ),
    (
        "timestamp,asset,wh\n2026-11-01 01:30,A,1\n",
        {"site_timezone": "America/New_York", "answers": CONFIRMED},
        RowReason.TIME_AMBIGUOUS,
        (1, 2, "timestamp"),
        "Baris data 1, timestamp: waktu lokal 2026-11-01 01:30 terjadi dua kali di zona America/New_York. "
        "Tambahkan offset untuk memilih salah satunya.",
    ),
    (
        f"interval_start,interval_end,asset,wh\n{LATER},{START},A,1\n",
        {},
        RowReason.INTERVAL_REVERSED,
        (1, 2, "interval_end"),
        "Baris data 1, interval_end: akhir interval harus setelah awal interval.",
    ),
    (
        f"timestamp,asset,wh\n{START},A, \n",
        {},
        RowReason.VALUE_EMPTY,
        (1, 2, "wh"),
        "Baris data 1, wh: nilai kosong. Isi angka 0 atau lebih; kosong tidak dianggap 0.",
    ),
    (
        f"timestamp;asset;wh\n{START};A;12.5\n",
        {},
        RowReason.VALUE_AMBIGUOUS,
        (1, 2, "wh"),
        'Baris data 1, wh: angka "12.5" ambigu pada berkas titik koma. Gunakan koma desimal, misalnya 12,5.',
    ),
    (
        f'timestamp,asset,wh\n{START},A,"1,250"\n',
        {},
        RowReason.VALUE_AMBIGUOUS_COMMA,
        (1, 2, "wh"),
        'Baris data 1, wh: angka "1,250" ambigu pada berkas koma. Gunakan titik desimal, misalnya 1.25, '
        "atau tulis tanpa pemisah ribuan, misalnya 1250.",
    ),
    (
        f"timestamp,asset,wh\n{START},A,dua\n",
        {},
        RowReason.VALUE_NOT_NUMBER,
        (1, 2, "wh"),
        'Baris data 1, wh: "dua" bukan angka.',
    ),
    (
        f"timestamp,asset,wh\n{START},A,1.2345\n",
        {},
        RowReason.VALUE_TOO_PRECISE,
        (1, 2, "wh"),
        "Baris data 1, wh: gunakan paling banyak 3 angka desimal.",
    ),
    (
        f"timestamp,asset,wh\n{START},A,9223372036854775.808\n",
        {},
        RowReason.VALUE_TOO_LARGE,
        (1, 2, "wh"),
        'Baris data 1, wh: angka "9223372036854775.808" terlalu besar. Periksa nilai dan satuannya.',
    ),
    (
        ENERGY_HEADER + "".join(f"2026-10-20 0{hour}:00,A,1\n" for hour in range(6)) + "2026-10-20 06:00,A,-1\n",
        {},
        RowReason.NEGATIVE,
        (7, 8, "energy_wh"),
        "Baris data 7, energy_wh: gunakan angka 0 atau lebih.",
    ),
]


@pytest.mark.parametrize(
    ("text", "options", "reason", "position", "message"),
    BAD_ROW_TABLE,
    ids=[entry[2].value for entry in BAD_ROW_TABLE],
)
def test_wrong_row_names_its_row_field_and_correction(
    parse_text: ParseText,
    text: str,
    options: dict[str, object],
    reason: RowReason,
    position: tuple[int, int, str],
    message: str,
) -> None:
    """
    Condition:
    - One row failing for each reason in the Messages table.

    Expected:
    - It is invalid, with the stable reason, position and exact message. Earlier rows are not affected.
    """
    _, rows = parse_text(text, **options)
    row = next(row for row in rows if row.status is RowStatus.INVALID)
    assert row.error.reason is reason
    assert (row.error.data_row, row.error.file_line, row.error.field) == position
    assert (row.data_row, row.file_line) == position[:2]
    assert row.error.message == message


def test_wrong_table_covers_every_row_reason() -> None:
    """
    Condition:
    - The bad-input table above.

    Expected:
    - It holds every reason, so a new reason cannot ship untested.
    """
    assert {entry[2] for entry in BAD_ROW_TABLE} == set(RowReason)


def test_wrong_impossible_dates_never_roll_into_march(parse_text: ParseText) -> None:
    """
    Condition:
    - ``2026-02-30`` with and without a clock (US3 scenario 3).

    Expected:
    - Both are rejected, with no instant set on the row.
    """
    _, rows = parse_text("timestamp,asset,wh\n2026-02-30,A,1\n2026-02-30 00:00,A,1\n", answers=CONFIRMED)
    assert [row.error.reason for row in rows] == [RowReason.TIME_FORMAT, RowReason.TIME_IMPOSSIBLE]
    assert [row.interval_start for row in rows] == [None, None]


def test_wrong_header_appears_as_written(parse_text: ParseText) -> None:
    """
    Condition:
    - A mixed-case header with spaces around it.

    Expected:
    - The message names it as written after strip.
    """
    _, rows = parse_text(f"timestamp,asset, Energy_WH \n{START},A,-1\n")
    assert rows[0].error.field == "Energy_WH"
    assert rows[0].error.message == "Baris data 1, Energy_WH: gunakan angka 0 atau lebih."


@pytest.mark.parametrize("name", ["X" * 60, "\U0001f600" * 60], ids=["ascii", "emoji"])
def test_wrong_sixty_characters_pass_counted_in_code_points(parse_text: ParseText, name: str) -> None:
    """
    Condition:
    - A 60-character name, where 60 emoji would be 120 UTF-16 units (D22).

    Expected:
    - It passes unchanged, matching ``assets.name``'s ``char_length`` limit.
    """
    _, rows = parse_text(f"timestamp,asset,wh\n{START},{name},1\n{LATER},{name},1\n")
    assert rows[0].status is RowStatus.PARSED
    assert rows[0].asset_name == name


def test_wrong_sixty_character_source_passes_and_name_is_not_truncated(parse_text: ParseText) -> None:
    """
    Condition:
    - A 60-character source beside a 61-character name.

    Expected:
    - The source passes its check and the row fails on the name, with nothing truncated to fit.
    """
    _, rows = parse_text(f"timestamp,asset,source,wh\n{START},{'X' * 61},{'S' * 60},1\n")
    assert rows[0].error.reason is RowReason.ASSET_TOO_LONG
    assert rows[0].asset_name is None
    _, good = parse_text(f"timestamp,asset,source,wh\n{START},A,{'S' * 60},1\n{LATER},A,{'S' * 60},1\n")
    assert good[0].status is RowStatus.PARSED
    assert good[0].stream_key == "s" * 60


@pytest.mark.parametrize("name", ["=SUM(A1)", "+62811", "-1+1", "@cmd", "<script>"])
def test_wrong_formula_looking_name_stays_plain_text(parse_text: ParseText, name: str) -> None:
    """
    Condition:
    - A name a spreadsheet or browser could execute.

    Expected:
    - It returns verbatim, in the row and in ``asset_names``: rendering it safely is the caller's job.
    """
    parsed, rows = parse_text(f"timestamp,asset,wh\n{START},{name},1\n{LATER},{name},1\n")
    assert parsed.asset_names == [name]
    assert rows[0].asset_name == name
    assert rows[0].status is RowStatus.PARSED


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        (f"{START},A", RowReason.COLUMN_COUNT),
        ("kemarin, ,dua", RowReason.ASSET_EMPTY),
        (f"kemarin,{'X' * 61},dua", RowReason.ASSET_TOO_LONG),
        ("kemarin,A,dua", RowReason.TIME_FORMAT),
        (f"{START},A,", RowReason.VALUE_EMPTY),
    ],
)
def test_wrong_first_failure_wins_in_the_prototype_order(parse_text: ParseText, line: str, reason: RowReason) -> None:
    """
    Condition:
    - A row with several things wrong.

    Expected:
    - Only the first in L748–L767's order is reported.
    """
    _, rows = parse_text(f"timestamp,asset,wh\n{line}\n")
    assert rows[0].error.reason is reason


def test_wrong_equal_bounds_are_reversed(parse_text: ParseText) -> None:
    """
    Condition:
    - An interval whose end equals its start, with the same instant written in two offsets.

    Expected:
    - ``interval_reversed``: instants are compared, not text.
    """
    _, rows = parse_text(f"interval_start,interval_end,asset,wh\n{START},2026-10-19T17:00:00Z,A,1\n")
    assert rows[0].error.reason is RowReason.INTERVAL_REVERSED


def test_wrong_offset_end_after_a_later_written_start_is_not_reversed(parse_text: ParseText) -> None:
    """
    Condition:
    - An end whose text sorts earlier but whose instant is later.

    Expected:
    - The row is parsed.
    """
    _, rows = parse_text(f"interval_start,interval_end,asset,wh\n{START},2026-10-19T18:00:00Z,A,1\n")
    assert rows[0].status is RowStatus.PARSED


def test_wrong_reversed_naive_bounds_report_before_the_zone_is_confirmed(parse_text: ParseText) -> None:
    """
    Condition:
    - Two naive bounds, reversed, with the zone unconfirmed. Both share a zone, so they are comparable.

    Expected:
    - ``interval_reversed`` now, rather than after the user answers a question that cannot help.
    """
    _, rows = parse_text("interval_start,interval_end,asset,wh\n2026-10-20 01:00,2026-10-20 00:00,A,1\n")
    assert rows[0].error.reason is RowReason.INTERVAL_REVERSED


def test_wrong_mixed_bounds_wait_because_they_are_not_comparable(parse_text: ParseText) -> None:
    """
    Condition:
    - An offset start and a naive end with the zone unconfirmed, whose wall clocks look reversed.

    Expected:
    - The row waits: the naive end has no instant to compare yet.
    """
    _, rows = parse_text(f"interval_start,interval_end,asset,wh\n{START},2026-10-19 23:00,A,1\n")
    assert rows[0].status is RowStatus.PENDING


def test_wrong_value_errors_report_while_the_zone_is_unconfirmed(parse_text: ParseText) -> None:
    """
    Condition:
    - A naive row with a negative value and no confirmation.

    Expected:
    - The value error is reported now. ``pending`` applies only where no error was found.
    """
    _, rows = parse_text("timestamp,asset,wh\n2026-10-20 00:00,A,-1\n")
    assert rows[0].status is RowStatus.INVALID
    assert rows[0].error.reason is RowReason.NEGATIVE


def test_wrong_empty_value_is_never_read_as_zero(parse_text: ParseText) -> None:
    """
    Condition:
    - An empty value beside a valid zero, in the same stream.

    Expected:
    - The empty one is invalid with no value. The zero is a valid reading of zero.
    """
    _, rows = parse_text(f"timestamp,asset,wh\n{START},A,\n{LATER},A,0\n")
    assert (rows[0].status, rows[0].value_milli) == (RowStatus.INVALID, None)
    assert (rows[1].status, rows[1].value_milli) == (RowStatus.PARSED, 0)


def test_wrong_end_beyond_the_calendar_is_impossible(parse_text: ParseText) -> None:
    """
    Condition:
    - A timestamp at the calendar's last hour, whose interval end falls past year 9999.

    Expected:
    - ``time_impossible`` on that row, not an ``OverflowError``.
    """
    _, rows = parse_text(
        "timestamp,asset,wh\n9999-12-31T23:00:00Z,A,1\n", answers=MeaningAnswers(interval_minutes={"a": 120})
    )
    assert rows[0].error.reason is RowReason.TIME_IMPOSSIBLE
    assert rows[0].error.message == "Baris data 1, timestamp: tanggal atau jam tidak ada (9999-12-31T23:00:00Z)."


def test_wrong_blank_lines_name_the_file_line_when_it_differs(parse_text: ParseText) -> None:
    """
    Condition:
    - Two blank lines before the seventh data row (US3 scenario 2).

    Expected:
    - ``Baris data 7 (baris file 10)`` counts the header line, and data row 1 needs no parenthesis.
    """
    rows_text = "".join(f"2026-10-20 0{hour}:00,A,1\n" for hour in range(6))
    _, rows = parse_text(f"{ENERGY_HEADER}\n\n{rows_text}2026-10-20 06:00,A,-1\n")
    assert rows[-1].error.message == "Baris data 7 (baris file 10), energy_wh: gunakan angka 0 atau lebih."
    assert (rows[-1].data_row, rows[-1].file_line) == (7, 10)


def test_wrong_spec_example_of_a_distinct_file_line(parse_text: ParseText) -> None:
    """
    Condition:
    - One blank line before the seventh data row, with the header on line 1.

    Expected:
    - The spec's message: ``Baris data 7 (baris file 9)``.
    """
    rows_text = "".join(f"2026-10-20 0{hour}:00,A,1\n" for hour in range(3))
    later_text = "".join(f"2026-10-20 0{hour}:00,A,1\n" for hour in range(3, 6))
    _, rows = parse_text(f"{ENERGY_HEADER}{rows_text}\n{later_text}2026-10-20 06:00,A,-1\n")
    assert rows[-1].error.message == "Baris data 7 (baris file 9), energy_wh: gunakan angka 0 atau lebih."


def test_wrong_quoted_newline_numbering_matches_the_prototype(parse_text: ParseText) -> None:
    """
    Condition:
    - A quoted newline in row 1, then a blank line, then row 2.

    Expected:
    - ``Baris data 1, wh`` and ``Baris data 2 (baris file 5), wh``, the prototype's output.
    """
    _, rows = parse_text('timestamp,asset,wh\n2026-10-20 00:00,"A\nB",-1\n\n2026-10-20 01:00,C,-1\n')
    assert [row.error.message for row in rows] == [
        "Baris data 1, wh: gunakan angka 0 atau lebih.",
        "Baris data 2 (baris file 5), wh: gunakan angka 0 atau lebih.",
    ]


def test_wrong_leading_blank_lines_move_the_header_too(parse_text: ParseText) -> None:
    """
    Condition:
    - The header on line 3, and data row 1 on line 4.

    Expected:
    - No parenthesis: the line equals data row plus header line.
    """
    parsed, rows = parse_text(f"\n\n{ENERGY_HEADER}2026-10-20 00:00,A,-1\n")
    assert (parsed.header_line, parsed.blank_lines) == (3, 2)
    assert rows[0].file_line == 4
    assert rows[0].error.message == "Baris data 1, energy_wh: gunakan angka 0 atau lebih."


def test_wrong_mixed_line_endings_count_one_line_each(parse_text: ParseText) -> None:
    """
    Condition:
    - ``\\r\\n``, ``\\n`` and ``\\r`` in one file, with a blank line.

    Expected:
    - Each counts one line, so the last row is on file line 5.
    """
    _, rows = parse_text(
        "timestamp,asset,wh\r\n2026-10-20 00:00,A,1\n\r2026-10-20 01:00,A,1\r2026-10-20 02:00,A,-1\n",
    )
    assert [row.file_line for row in rows] == [2, 4, 5]
    assert rows[-1].error.message == "Baris data 3 (baris file 5), wh: gunakan angka 0 atau lebih."


def test_wrong_bare_carriage_return_inside_quotes_counts_one_line(parse_text: ParseText) -> None:
    """
    Condition:
    - A bare ``\\r`` inside a quoted name (D9). L594 counts only ``\\n`` there.

    Expected:
    - The next row's file line counts it.
    """
    _, rows = parse_text('timestamp,asset,wh\n2026-10-20 00:00,"A\rB",1\n2026-10-20 01:00,C,-1\n')
    assert rows[0].asset_name == "A\rB"
    assert rows[1].file_line == 4
    assert rows[1].error.message == "Baris data 2 (baris file 4), wh: gunakan angka 0 atau lebih."


STRUCTURAL_TABLE = [
    (b"", StructuralReason.EMPTY_INPUT, "Berkas atau tempelan kosong. Pilih berkas CSV atau tempel isi CSV."),
    (b"x" * (10 * 1024 * 1024 + 1), StructuralReason.TOO_LARGE, "Ukuran 10,1 MiB melebihi batas 10 MiB."),
    (
        b"timestamp,asset,wh\ncaf\xe9,A,1\n",
        StructuralReason.NOT_UTF8,
        "Berkas bukan teks UTF-8. Simpan ulang sebagai CSV UTF-8 lalu coba lagi.",
    ),
    (
        b"a,b;c\n",
        StructuralReason.DELIMITER_AMBIGUOUS,
        "Pemisah kolom ambigu: header memakai koma dan titik koma. "
        'Gunakan salah satu, misalnya "timestamp;perangkat;energi_wh".',
    ),
    (
        b"abc\n",
        StructuralReason.SINGLE_COLUMN,
        "Header hanya memiliki satu kolom. Pisahkan kolom dengan koma atau titik koma.",
    ),
    (
        b'timestamp,asset,wh\n"x,A,1\n',
        StructuralReason.QUOTE_UNCLOSED,
        "Tanda kutip tidak ditutup mulai baris file 2.",
    ),
    (
        b'timestamp,asset,wh\n"x"y,A,1\n',
        StructuralReason.QUOTE_MALFORMED,
        "Tanda kutip tidak valid pada baris file 2. Tutup tanda kutip tepat sebelum pemisah kolom.",
    ),
    (
        b"timestamp,asset,energy_wh,wh\n2026-10-20 00:00,A,1,1\n",
        StructuralReason.DUPLICATE_ROLE,
        'Kolom "energy_wh" dan "wh" memiliki arti yang sama. Hapus salah satunya.',
    ),
    (
        b"timestamp,interval_start,interval_end,asset,wh\n2026-10-20 00:00,a,b,A,1\n",
        StructuralReason.COMPETING_TIME_COLUMNS,
        'Kolom "timestamp" dan "interval_start" sama-sama menyatakan waktu. '
        "Gunakan timestamp saja atau pasangan interval_start dan interval_end.",
    ),
    (
        b"timestamp,wh\n2026-10-20 00:00,1\n",
        StructuralReason.MISSING_ASSET,
        "Kolom perangkat tidak ditemukan. Gunakan header asset, perangkat, mesin, device, nama atau alat.",
    ),
    (
        b"asset,wh\nA,1\n",
        StructuralReason.MISSING_TIME,
        "Kolom waktu tidak ditemukan. Gunakan timestamp (atau waktu/tanggal) "
        "atau pasangan interval_start dan interval_end.",
    ),
    (
        b"timestamp,asset\n2026-10-20 00:00,A\n",
        StructuralReason.MISSING_VALUE,
        "Kolom nilai tidak ditemukan. Gunakan energy_wh/energi_wh, average_power_w/daya_w, atau cumulative_wh.",
    ),
    (
        b"interval_start,interval_end,asset,cumulative_wh\na,b,A,1\n",
        StructuralReason.COUNTER_NEEDS_TIMESTAMP,
        "Kolom cumulative_wh memerlukan kolom timestamp titik waktu.",
    ),
    (
        b"timestamp,asset,wh\n" + b"2026-10-20 00:00,A,1\n" * 150_001,
        StructuralReason.TOO_MANY_ROWS,
        "150001 baris data melebihi batas 150.000 baris.",
    ),
    (b"timestamp,asset,wh\n\n", StructuralReason.NO_DATA_ROWS, "Tidak ada baris data setelah header."),
]


def _parse_bytes(data: bytes) -> ParsedFile:
    return parse(io.BytesIO(data), site_timezone="Asia/Jakarta")


@pytest.mark.parametrize(
    ("data", "reason", "message"),
    STRUCTURAL_TABLE,
    ids=[reason.value for _, reason, _ in STRUCTURAL_TABLE],
)
def test_wrong_structure_gives_its_reason_and_exact_message(
    data: bytes, reason: StructuralReason, message: str
) -> None:
    """
    Condition:
    - One file failing for each reason in the structural table.

    Expected:
    - The file is not ok, and its only structural error has the stable reason and exact message.
    """
    parsed = _parse_bytes(data)
    assert parsed.ok is False
    assert [(error.reason, error.message) for error in parsed.structural_errors] == [(reason, message)]


def test_wrong_structural_table_covers_every_reason() -> None:
    """
    Condition:
    - The structural table above.

    Expected:
    - It holds every reason, so a new reason cannot ship untested.
    """
    assert {entry[1] for entry in STRUCTURAL_TABLE} == set(StructuralReason)


def test_wrong_quote_error_carries_its_file_line() -> None:
    """
    Condition:
    - An unclosed quote on line 2.

    Expected:
    - The error's ``file_line`` is 2, for the caller's own use.
    """
    assert _parse_bytes(b'timestamp,asset,wh\n"x,A,1\n').structural_errors[0].file_line == 2


def _padded(size: int) -> bytes:
    start = b"timestamp,asset,wh\n2026-10-20T00:00:00+07:00,A,1\n"
    return start + b"\n" * (size - len(start))


def test_wrong_exactly_ten_mib_is_within_the_limit() -> None:
    """
    Condition:
    - A file of exactly 10,485,760 bytes, padded with blank lines.

    Expected:
    - No structural error, and the padding is counted as blank lines.
    """
    parsed = _parse_bytes(_padded(10 * 1024 * 1024))
    assert parsed.structural_errors == []
    assert parsed.total_rows == 1


@pytest.mark.parametrize(
    ("size", "message"),
    [
        (10 * 1024 * 1024 + 1, "Ukuran 10,1 MiB melebihi batas 10 MiB."),
        (11 * 1024 * 1024, "Ukuran 11 MiB melebihi batas 10 MiB."),
        (11 * 1024 * 1024 + 1, "Ukuran 11,1 MiB melebihi batas 10 MiB."),
    ],
)
def test_wrong_size_message_rounds_up_so_it_never_reads_as_within_the_limit(size: int, message: str) -> None:
    """
    Condition:
    - A file just over the limit, exactly 11 MiB, and just over that (D23).

    Expected:
    - The message rounds up to one decimal with a decimal comma, and a whole number has none.
    """
    parsed = _parse_bytes(b"\n" * size)
    assert [error.message for error in parsed.structural_errors] == [message]


def test_wrong_oversize_file_reports_size_before_decoding() -> None:
    """
    Condition:
    - An oversize file that is also invalid UTF-8.

    Expected:
    - Size is reported, because the check runs before any decoding.
    """
    parsed = _parse_bytes(b"\xff" * (10 * 1024 * 1024 + 1))
    assert [error.reason for error in parsed.structural_errors] == [StructuralReason.TOO_LARGE]


def test_wrong_row_limit_counts_nonblank_rows_only() -> None:
    """
    Condition:
    - Exactly 150,000 data rows, with blank lines among them.

    Expected:
    - No structural error: blank lines are not data rows.
    """
    parsed = _parse_bytes(b"timestamp,asset,wh\n\n" + b"2026-10-20T00:00:00+07:00,A,1\n\n" * 150_000)
    assert parsed.structural_errors == []
    assert (parsed.total_rows, parsed.blank_lines) == (150_000, 150_001)


def test_wrong_row_limit_reports_the_true_count() -> None:
    """
    Condition:
    - 150,500 data rows.

    Expected:
    - The message states the true count, because counting continues past the limit.
    """
    parsed = _parse_bytes(b"timestamp,asset,wh\n" + b"2026-10-20 00:00,A,1\n" * 150_500)
    assert [error.message for error in parsed.structural_errors] == ["150500 baris data melebihi batas 150.000 baris."]
    assert parsed.total_rows == 150_500


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (b'foo,bar\n"x', StructuralReason.QUOTE_UNCLOSED),
        (b'foo,bar\n"x"y,1\n', StructuralReason.QUOTE_MALFORMED),
        (b"foo,bar\ncaf\xe9,1\n", StructuralReason.NOT_UTF8),
    ],
)
def test_wrong_quote_and_decode_errors_replace_all_others(data: bytes, reason: StructuralReason) -> None:
    """
    Condition:
    - Unknown headers, and a quote or decode failure later in the file.

    Expected:
    - Only that failure: the columns cannot be trusted when the text itself is unreadable (L656).
    """
    assert [error.reason for error in _parse_bytes(data).structural_errors] == [reason]


def test_wrong_header_errors_are_all_reported_together() -> None:
    """
    Condition:
    - Unknown headers and no data rows.

    Expected:
    - Every error at once, in order, so the user fixes the file in one go.
    """
    assert [error.reason for error in _parse_bytes(b"foo,bar\n").structural_errors] == [
        StructuralReason.MISSING_ASSET,
        StructuralReason.MISSING_TIME,
        StructuralReason.MISSING_VALUE,
        StructuralReason.NO_DATA_ROWS,
    ]


def test_wrong_row_error_is_not_a_structural_error(parse_text: ParseText) -> None:
    """
    Condition:
    - A file whose only fault is one bad value (FR-005).

    Expected:
    - No structural error and no question. The fault is on the row alone.
    """
    parsed, rows = parse_text(f"interval_start,interval_end,asset,wh\n{START},{LATER},A,-1\n")
    assert parsed.structural_errors == []
    assert parsed.questions == []
    assert rows[0].error is not None


def test_wrong_question_makes_no_row_error(parse_text: ParseText) -> None:
    """
    Condition:
    - A file whose only open matter is the timezone (FR-005).

    Expected:
    - A question and no structural error, with rows pending and carrying no error.
    """
    parsed, rows = parse_text("timestamp,asset,wh\n2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n")
    assert parsed.structural_errors == []
    assert [question.kind for question in parsed.questions] == [QuestionKind.TIMEZONE]
    assert [row.error for row in rows] == [None, None]


def test_wrong_structural_errors_ask_nothing_and_yield_no_rows(parse_text: ParseText) -> None:
    """
    Condition:
    - A naive file that also has a structural error.

    Expected:
    - No questions, since an answer cannot help, and ``iter_rows`` yields nothing.
    """
    parsed, rows = parse_text("timestamp,asset,energy_wh,wh\n2026-10-20 00:00,A,1,1\n")
    assert isinstance(parsed.structural_errors[0], StructuralError)
    assert parsed.questions == []
    assert rows == []


def test_wrong_source_changed_between_passes_raises_as_a_bug() -> None:
    """
    Condition:
    - A caller replaces the file's content between ``parse`` and ``iter_rows``.

    Expected:
    - ``RuntimeError`` with fixed text, reaching the registered fallback. Rows are never silently cut short.
    """
    source = io.BytesIO(f"interval_start,interval_end,asset,wh\n{START},{LATER},A,1\n".encode())
    parsed = parse(source, site_timezone="Asia/Jakarta")
    source.seek(0)
    source.truncate()
    source.write(b'interval_start,interval_end,asset,wh\n"x')
    with pytest.raises(RuntimeError, match="^The source changed between the two passes.$"):
        list(iter_rows(source, parsed))


def test_wrong_parser_logs_nothing(parse_text: ParseText, caplog: pytest.LogCaptureFixture) -> None:
    """
    Condition:
    - A fake secret in a name, in a valid row and in invalid rows, with logging at its lowest level.

    Expected:
    - Nothing is logged at all. The value is the caller's data and reaches no other surface.
    """
    secret = "Bearer RAHASIA-PALSU-123"
    caplog.set_level(logging.DEBUG)
    parse_text(f"timestamp,asset,wh\n{START},{secret},1\n{LATER},{secret},{secret}\nkemarin,{secret},-1\n")
    assert caplog.records == []
    assert secret not in caplog.text
