"""The prototype's parser assertions, in Python, with the same messages. See the table in tasks.md (SC-001)."""

from collections.abc import Callable
from datetime import timedelta

from app.assets.model.models import MeasurementKind
from app.imports.model.models import (
    MeaningAnswers,
    ParsedFile,
    PowerMeaning,
    QuestionKind,
    RowReason,
    RowResult,
    RowStatus,
    StructuralReason,
    ValueKind,
)
from app.measurements.model.models import ReadingInput
from app.measurements.service.normalize import CounterPoint, counter_deltas, normalize

type ParseText = Callable[..., tuple[ParsedFile, list[RowResult]]]

AT_28 = (
    '\ufeffwaktu;alat;wh\r\n2026-10-20 00:00;"Lampu; Gudang";12,5\r\n\r\n2026-10-20 01:00;"Lampu; Gudang";1.250,5\r\n'
)


def test_at_26_timestamp_block_from_the_prd(parse_text: ParseText) -> None:
    """
    Condition:
    - The first CSV block in PRD §10.2. ``domain.test.js`` has no AT-26 test, so this one is new.

    Expected:
    - Aliases resolve and values mean interval Wh.
    """
    parsed, rows = parse_text("timestamp,perangkat,energi_wh\n2026-10-20 00:00,Router,10\n2026-10-20 01:00,Router,10\n")
    assert parsed.ok
    assert parsed.ignored_columns == []
    assert parsed.value_kinds == [ValueKind.INTERVAL_ENERGY]
    assert parsed.asset_names == ["Router"]
    assert [row.value_milli for row in rows] == [10000, 10000]


def test_at_26_explicit_block_from_the_prd(parse_text: ParseText) -> None:
    """
    Condition:
    - The second CSV block in PRD §10.2, with header case changed.

    Expected:
    - Aliases match case-insensitively, and rows are parsed with no question.
    """
    parsed, rows = parse_text(
        "INTERVAL_START,Interval_End,Asset,ENERGY_WH\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Router,10\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,Kulkas,50\n"
    )
    assert parsed.questions == []
    assert parsed.asset_names == ["Router", "Kulkas"]
    assert [(row.status, row.value_milli) for row in rows] == [(RowStatus.PARSED, 10000), (RowStatus.PARSED, 50000)]


def test_at_28_semicolons_decimal_commas_quotes_bom_crlf_blank_line(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L230–L233.

    Expected:
    - Delimiter, names and the blank line as the prototype reads them, and values 12,500 and 1,250,500.
    """
    parsed, rows = parse_text(
        '﻿waktu;alat;wh\r\n2026-10-20 00:00;"Lampu; Gudang";12,5\r\n\r\n2026-10-20 01:00;"Lampu; Gudang";1.250,5\r\n'
    )
    assert parsed.ok
    assert parsed.delimiter == ";"
    assert parsed.asset_names == ["Lampu; Gudang"]
    assert parsed.blank_lines == 1
    assert [row.value_milli for row in rows] == [12500, 1250500]


def test_at_28_decimal_comma_in_a_comma_file_needs_quotes(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L234–L235: the same number quoted, then unquoted, in a comma file.

    Expected:
    - The quoted value reads as 12.5. The unquoted one is invalid for its column count, never read as 12.
    """
    _, rows = parse_text('timestamp,asset,energy_wh\n2026-10-20 00:00,A,"12,5"\n2026-10-20 01:00,A,12,5\n')
    assert rows[0].value_milli == 12500
    assert rows[1].status is RowStatus.INVALID
    assert rows[1].error.reason is RowReason.COLUMN_COUNT
    assert rows[1].value_milli is None


AT_27A = (
    "interval_start,interval_end,asset,average_power_w\n2026-10-20T00:00:00+07:00,2026-10-20T00:30:00+07:00,Pompa,100\n"
)


def test_at_28_confirmed_rows_are_parsed(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L232–L233: the semicolon file once the timezone is confirmed.

    Expected:
    - Both rows are accepted, as the prototype's two accepted readings are.
    """
    parsed, rows = parse_text(
        AT_28,
        answers=MeaningAnswers(timezone_confirmed=True),
    )
    assert parsed.questions == []
    assert [(row.status, row.value_milli) for row in rows] == [(RowStatus.PARSED, 12500), (RowStatus.PARSED, 1250500)]


def test_at_27a_power_is_blocked_until_confirmed(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L127–L129: ``average_power_w`` with no answer.

    Expected:
    - A ``power_meaning`` question with the full message, and pending rows. ``blocked`` itself is 025's.
    """
    parsed, rows = parse_text(AT_27A)
    assert [question.kind for question in parsed.questions] == [QuestionKind.POWER_MEANING]
    assert parsed.questions[0].message == "Konfirmasi arti kolom daya: rata-rata selama interval atau daya sesaat."
    assert rows[0].status is RowStatus.PENDING


def test_at_27a_instantaneous_power_says_it_cannot_become_energy(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L130: the user says the power is instantaneous.

    Expected:
    - The message holds ``sesaat tidak dapat``, in full, and rows stay pending.
    """
    parsed, rows = parse_text(AT_27A, answers=MeaningAnswers(power_meaning=PowerMeaning.INSTANTANEOUS))
    assert parsed.questions[0].message == (
        "Daya sesaat tidak dapat diubah menjadi energi. Impor diblokir; "
        "gunakan data energi interval atau daya rata-rata interval."
    )
    assert rows[0].status is RowStatus.PENDING


def test_at_27a_average_power_for_thirty_minutes_is_fifty_wh(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L131–L132: 100 W for 30 minutes, confirmed as an average, fed into 006's ``normalize``.

    Expected:
    - No questions, and 50,000 mWh. The parser itself keeps watts; only 006 converts.
    """
    parsed, rows = parse_text(AT_27A, answers=MeaningAnswers(power_meaning=PowerMeaning.AVERAGE))
    assert parsed.questions == []
    row = rows[0]
    assert (row.value_milli, row.unit) == (100000, "W")
    assert row.interval_end - row.interval_start == timedelta(minutes=30)
    reading = ReadingInput(
        value=row.value, unit=row.unit, interval_start=row.interval_start, interval_end=row.interval_end
    )
    assert normalize(reading, MeasurementKind.AVERAGE_POWER).energy_mwh == 50000


def test_at_27b_counter_with_a_reset_gives_thirty_wh(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L136–L141: counter 100, 130, 5 Wh, fed into 006's ``counter_deltas``.

    Expected:
    - Three points and no duration question. One delta of 30,000 mWh, never negative and never 125,000.
    """
    parsed, rows = parse_text(
        "timestamp,perangkat,cumulative_wh\n"
        "2026-10-20 00:00,Mesin,100\n2026-10-20 01:00,Mesin,130\n2026-10-20 02:00,Mesin,5\n",
        answers=MeaningAnswers(timezone_confirmed=True),
    )
    assert parsed.questions == []
    assert [row.status for row in rows] == [RowStatus.PARSED] * 3
    deltas = counter_deltas([CounterPoint(row.measured_at, row.value_milli) for row in rows], None)
    assert [delta.energy_mwh for delta in deltas] == [30000]


def test_at_31_one_row_stream_needs_a_duration(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L247–L250: one timestamp-only row, then with 60 minutes declared.

    Expected:
    - An ``interval_duration`` question, then none and a parsed row.
    """
    text = "timestamp,asset,energy_wh\n2026-10-20 00:00,A,1\n"
    parsed, _ = parse_text(text, answers=MeaningAnswers(timezone_confirmed=True))
    assert [question.kind for question in parsed.questions] == [QuestionKind.INTERVAL_DURATION]
    declared, rows = parse_text(text, answers=MeaningAnswers(timezone_confirmed=True, interval_minutes={"a": 60}))
    assert declared.questions == []
    assert rows[0].status is RowStatus.PARSED


def test_at_31_irregular_stream_has_no_cadence(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L251–L252.

    Expected:
    - Cadence None.
    """
    parsed, _ = parse_text(
        "timestamp,asset,energy_wh\n"
        "2026-10-20 00:00,A,1\n2026-10-20 01:00,A,1\n2026-10-20 01:15,A,1\n2026-10-20 03:00,A,1\n"
    )
    assert parsed.cadences == {"a": None}


def test_at_31_one_long_gap_keeps_the_cadence(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L253–L254: hourly rows with one four-hour gap.

    Expected:
    - Cadence one hour.
    """
    hours = [0, 1, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    parsed, _ = parse_text(
        "timestamp,asset,energy_wh\n" + "".join(f"2026-10-20 {hour:02}:00,A,1\n" for hour in hours),
    )
    assert parsed.cadences == {"a": timedelta(hours=1)}


def _bad_values(bad: int) -> str:
    rows = (f"2026-10-20 {index:02}:00,Router,{'-1' if index < bad else '10'}\n" for index in range(10))
    return "timestamp,perangkat,energi_wh\n" + "".join(rows)


def test_at_30_first_error_message(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L224: ten rows, the first two negative.

    Expected:
    - The first error's exact message. Counts and thresholds are 025's.
    """
    _, rows = parse_text(_bad_values(2), answers=MeaningAnswers(timezone_confirmed=True))
    errors = [row.error for row in rows if row.error is not None]
    assert errors[0].message == "Baris data 1, energi_wh: gunakan angka 0 atau lebih."
    assert len(errors) == 2


def test_at_29_bad_header_is_rejected(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L239: headers with no known alias.

    Expected:
    - The file is not ok, with actionable messages.
    """
    parsed, rows = parse_text("foo,bar\n1,2\n")
    assert parsed.ok is False
    assert [error.reason for error in parsed.structural_errors] == [
        StructuralReason.MISSING_ASSET,
        StructuralReason.MISSING_TIME,
        StructuralReason.MISSING_VALUE,
    ]
    assert rows == []


def test_at_29_impossible_date_and_non_number_are_actionable(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L240–L243: an impossible date on row 1 and ``dua`` on row 2.

    Expected:
    - Both are row errors with exact messages, and the other rows stay valid.
    """
    _, rows = parse_text(
        "timestamp,asset,energy_wh\n"
        "2026-02-30 00:00,A,1\n"
        "2026-10-20 01:00,A,dua\n"
        "2026-10-20 02:00,A,1\n"
        "2026-10-20 03:00,A,1\n"
        "2026-10-20 04:00,A,1\n",
        answers=MeaningAnswers(timezone_confirmed=True),
    )
    assert [row.error.message for row in rows if row.error is not None] == [
        "Baris data 1, timestamp: tanggal atau jam tidak ada (2026-02-30 00:00).",
        'Baris data 2, energy_wh: "dua" bukan angka.',
    ]
    assert [row.status for row in rows[2:]] == [RowStatus.PARSED] * 3


def test_at_32_long_name_is_invalid_and_not_truncated(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L258–L261: a 61-character name.

    Expected:
    - One invalid row with the exact ``tidak dipotong`` message.
    """
    long = "X" * 61
    _, rows = parse_text(
        f"interval_start,interval_end,asset,energy_wh\n2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,{long},1\n"
    )
    assert [row.status for row in rows] == [RowStatus.INVALID]
    assert rows[0].error.message == (
        "Baris data 1, asset: nama lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya."
    )


def test_at_32_row_limit_is_reported(parse_text: ParseText) -> None:
    """
    Condition:
    - ``domain.test.js`` L262–L263: 150,001 rows.

    Expected:
    - The exact ``150.000`` message.
    """
    parsed, rows = parse_text("timestamp,asset,energy_wh\n" + "2026-10-20 00:00,A,1\n" * 150_001)
    assert [error.message for error in parsed.structural_errors] == ["150001 baris data melebihi batas 150.000 baris."]
    assert rows == []
