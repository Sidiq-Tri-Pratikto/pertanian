"""Counts and row classification, on the parser's real rows and 006's real normalization."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.assets.model.models import MeasurementKind
from app.imports.model.models import MeaningAnswers, ParsedFile, RowError, RowReason, RowResult
from app.imports.service import classify as classify_module
from app.imports.service.classify import RowCounts, StagedRow, file_columns, stage_row, summarize
from app.measurements.model.models import MeasurementRow, ReadingInput
from app.measurements.service.normalize import ReadingRejectedError, normalize

LENGKAPI = "Lengkapi pemetaan terlebih dahulu."
BERBEDA = (
    "Nilai berbeda ditemukan untuk sumber dan interval yang sama. Pilih sumber atau perbaiki data sebelum melanjutkan."
)
KOSONG = "Tidak ada baris valid yang dapat diimpor."
CONFIRMED = MeaningAnswers(timezone_confirmed=True)


def csv10(bad: int) -> str:
    """Build AT-30's file: ten hourly Router rows, the first ``bad`` of them negative."""
    lines = [f"2026-10-20 {hour:02}:00,Router,{'-1' if hour < bad else '10'}" for hour in range(10)]
    return "timestamp,perangkat,energi_wh\n" + "\n".join(lines) + "\n"


def _staged(parsed: ParsedFile, rows: list[RowResult]) -> list[StagedRow | RowError]:
    columns = file_columns(parsed)
    return [stage_row(row, columns) for row in rows if row.status.value == "parsed" or row.error is not None]


def _counts(**values: int) -> RowCounts:
    known = {"accepted": 0, "invalid": 0, "duplicate": 0, "conflict": 0, "pending": 0} | values
    return RowCounts(total=sum(known.values()), **known)


@pytest.mark.parametrize(("bad", "accepted"), [(2, 8), (3, 7)])
def test_counts_at_30_rows_reconcile(parse_text: Callable, bad: int, accepted: int) -> None:
    """
    Condition:
    - AT-30's file with two or three negative rows goes through the parser and staging.

    Expected:
    - Invalid rows become errors, the rest stage, and the sum is every data row.
    """
    parsed, rows = parse_text(csv10(bad), answers=CONFIRMED)

    staged = _staged(parsed, rows)

    assert sum(isinstance(row, RowError) for row in staged) == bad
    assert sum(isinstance(row, StagedRow) for row in staged) == accepted
    assert len(staged) == parsed.total_rows == 10


def test_counts_two_of_ten_invalid_need_acknowledgment() -> None:
    """
    Condition:
    - AT-30: 8 accepted and 2 invalid, with no open question.

    Expected:
    - Not blocked, and the eight rows import only after an explicit acknowledgment.
    """
    summary = summarize(_counts(accepted=8, invalid=2), open_questions=0)

    assert (summary.blocked, summary.block_reasons, summary.needs_acknowledgment) == (False, [], True)


def test_counts_three_of_ten_invalid_are_blocked() -> None:
    """
    Condition:
    - AT-30: 7 accepted and 3 invalid.

    Expected:
    - Blocked with the exact message, and no acknowledgment can lift it.
    """
    summary = summarize(_counts(accepted=7, invalid=3), open_questions=0)

    assert summary.blocked is True
    assert summary.block_reasons == ["Impor diblokir: 3 dari 10 baris tidak valid."]
    assert summary.needs_acknowledgment is False


@pytest.mark.parametrize(
    ("invalid", "accepted", "blocked"),
    [(1, 4, False), (1, 3, True), (20, 80, False), (21, 79, True), (1, 0, True)],
    ids=["1_of_5_passes", "1_of_4_blocks", "exactly_20_percent", "above_20_percent", "1_of_1"],
)
def test_counts_threshold_is_an_integer_comparison(invalid: int, accepted: int, blocked: bool) -> None:
    """
    Condition:
    - Invalid shares at and around one fifth of all rows.

    Expected:
    - ``invalid * 5 <= total`` passes, with no float rounding at the edge.
    """
    summary = summarize(_counts(accepted=accepted, invalid=invalid), open_questions=0)

    assert summary.blocked is blocked


def test_counts_clean_file_needs_nothing() -> None:
    """
    Condition:
    - Every row accepted.

    Expected:
    - Not blocked, and no acknowledgment is needed.
    """
    summary = summarize(_counts(accepted=10), open_questions=0)

    assert (summary.blocked, summary.needs_acknowledgment) == (False, False)


def test_counts_open_question_blocks() -> None:
    """
    Condition:
    - Every row accepted, but a question is open.

    Expected:
    - Blocked until the mapping is complete.
    """
    summary = summarize(_counts(accepted=10), open_questions=1)

    assert summary.block_reasons == [LENGKAPI]


def test_counts_pending_rows_block() -> None:
    """
    Condition:
    - Rows wait on an answer, with no question listed.

    Expected:
    - Blocked, so a pending row can never be committed.
    """
    summary = summarize(_counts(accepted=9, pending=1), open_questions=0)

    assert summary.block_reasons == [LENGKAPI]


def test_counts_skipped_rows_waive_nothing() -> None:
    """
    Condition:
    - 2 of 10 invalid, which alone may proceed, with a question open.

    Expected:
    - Blocked, and no acknowledgment is offered, so skipping rows cannot waive the question.
    """
    summary = summarize(_counts(accepted=8, invalid=2), open_questions=1)

    assert summary.blocked is True
    assert summary.needs_acknowledgment is False


def test_counts_nothing_usable_is_blocked() -> None:
    """
    Condition:
    - No accepted and no duplicate rows, and no other reason.

    Expected:
    - Blocked with its own message.
    """
    assert summarize(_counts(), open_questions=0).block_reasons == [KOSONG]


def test_counts_nothing_usable_stays_silent_beside_another_reason() -> None:
    """
    Condition:
    - No accepted and no duplicate rows, because all are conflicts.

    Expected:
    - Only the conflict reason shows.
    """
    assert summarize(_counts(conflict=4), open_questions=0).block_reasons == [BERBEDA]


def test_counts_duplicate_only_is_not_blocked() -> None:
    """
    Condition:
    - AT-33: every row repeats stored data.

    Expected:
    - A no-op, not an error.
    """
    summary = summarize(_counts(duplicate=10), open_questions=0)

    assert (summary.blocked, summary.block_reasons) == (False, [])


def test_counts_conflict_blocks_at_a_low_invalid_share() -> None:
    """
    Condition:
    - One conflict in a hundred rows, with no invalid rows.

    Expected:
    - Blocked even though the invalid share is zero.
    """
    assert summarize(_counts(accepted=99, conflict=1), open_questions=0).block_reasons == [BERBEDA]


def test_counts_reasons_come_in_their_fixed_order() -> None:
    """
    Condition:
    - A question, too many invalid rows and a conflict at once.

    Expected:
    - The three reasons, in the Block reasons table's order.
    """
    summary = summarize(_counts(invalid=3, conflict=1, pending=1, accepted=1), open_questions=1)

    assert summary.block_reasons == [LENGKAPI, "Impor diblokir: 3 dari 6 baris tidak valid.", BERBEDA]


def test_counts_stage_row_uses_normalized_identity(parse_text: Callable) -> None:
    """
    Condition:
    - One parsed row with an offset.

    Expected:
    - Its identity and energy come from 006's ``normalize``, and ``10`` and ``10.0`` stage as the same observation.
    """
    text = (
        "interval_start,interval_end,asset,energy_wh\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,A,10\n"
        "2026-10-20T00:00:00+07:00,2026-10-20T01:00:00+07:00,A,10.0\n"
    )
    parsed, rows = parse_text(text)

    first, second = _staged(parsed, rows)

    assert first.observation.identity_key == second.observation.identity_key
    assert first.observation.identity_key.startswith("i:interval_energy:")
    assert first.observation.energy_mwh == 10_000
    assert first.observation.raw_value == "10.000"
    assert first.observation.same_observation(second.observation)


def test_counts_stage_row_refuses_energy_above_bigint(parse_text: Callable) -> None:
    """
    Condition:
    - A power value the parser allows, whose energy over a long interval exceeds what BIGINT mWh can hold.

    Expected:
    - The row is invalid with ``value_too_large``, in the parser's message form.
    """
    text = (
        "interval_start,interval_end,asset,average_power_w\n"
        "2026-10-20T00:00:00+07:00,2026-11-20T00:00:00+07:00,A,9000000000000000\n"
    )
    parsed, rows = parse_text(text, answers=MeaningAnswers(power_meaning="average"))

    error = _staged(parsed, rows)[0]

    assert isinstance(error, RowError)
    assert error.reason is RowReason.VALUE_TOO_LARGE
    assert error.field == "average_power_w"
    assert error.message == (
        'Baris data 1, average_power_w: angka "9000000000000000" terlalu besar. Periksa nilai dan satuannya.'
    )


def test_counts_stage_row_keeps_energy_at_exactly_bigint() -> None:
    """
    Condition:
    - A value in Wh whose milli-units are exactly the BIGINT maximum.

    Expected:
    - It stages, because the bound excludes only values above the maximum.
    """
    start = datetime(2026, 10, 20, tzinfo=UTC)
    value_milli = 2**63 - 1
    row = RowResult(
        data_row=1,
        file_line=2,
        status="parsed",
        asset_name="A",
        stream_key="a",
        kind="interval_energy",
        unit="Wh",
        value_milli=value_milli,
        interval_start=start,
        interval_end=start + timedelta(hours=1),
        interval_basis="explicit",
        raw_value=format(Decimal(value_milli) / 1000, "f"),
    )

    staged = stage_row(row, classify_module.FileColumns(value_header="wh", time_header="t", header_line=1))

    assert isinstance(staged, StagedRow)
    assert staged.observation.energy_mwh == value_milli
    assert MeasurementKind.INTERVAL_ENERGY.value == staged.observation.kind.value


def test_counts_a_row_006_refuses_is_a_bug_not_an_invalid_row() -> None:
    """
    Condition:
    - A row 024 calls parsed, in a unit 006 does not accept, so the two disagree.

    Expected:
    - The refusal propagates to the unknown-failure fallback instead of being counted as a user's mistake.
    """
    start = datetime(2026, 10, 20, tzinfo=UTC)
    row = RowResult(
        data_row=1,
        file_line=2,
        status="parsed",
        asset_name="A",
        stream_key="a",
        kind="interval_energy",
        unit="BTU",
        value_milli=1000,
        interval_start=start,
        interval_end=start + timedelta(hours=1),
        raw_value="1",
    )

    with pytest.raises(ReadingRejectedError, match="unit_invalid"):
        stage_row(row, classify_module.FileColumns(value_header="wh", time_header="t", header_line=1))


def test_counts_a_huge_echoed_cell_is_bounded() -> None:
    """
    Condition:
    - A row error whose message echoes a 128 KiB cell, as 024's ``value_too_large`` does.

    Expected:
    - The stored message stays bounded, keeping its row prefix, the start of the cell and the correction at its end.
    """
    cell = "9" * 131_072
    message = f'Baris data 7, energy_wh: angka "{cell}" terlalu besar. Periksa nilai dan satuannya.'

    bounded = classify_module.bound_text(message)

    assert len(bounded) <= classify_module.MAX_MESSAGE_LENGTH
    assert bounded.startswith('Baris data 7, energy_wh: angka "999')
    assert bounded.endswith('999" terlalu besar. Periksa nilai dan satuannya.')
    assert "…" in bounded


def test_counts_a_short_message_is_left_alone() -> None:
    """
    Condition:
    - A message at exactly the bound.

    Expected:
    - It is returned unchanged.
    """
    message = "x" * classify_module.MAX_MESSAGE_LENGTH

    assert classify_module.bound_text(message) == message


T0 = datetime(2026, 10, 20, tzinfo=UTC)
COLUMNS = classify_module.FileColumns(value_header="energy_wh", time_header="interval_start", header_line=1)
CONFLICT_TEXT = "nilai berbeda untuk sumber dan interval yang sama."
OVERLAP_TEXT = "interval bertumpang tindih dengan data lain pada sumber yang sama."


def _hour(hour: float) -> datetime:
    return T0 + timedelta(hours=hour)


def _interval(data_row: int, start: float, end: float, value: str = "10", *, stream: str = "a") -> StagedRow:
    row = RowResult(
        data_row=data_row,
        file_line=data_row + 1,
        status="parsed",
        asset_name=stream.upper(),
        stream_key=stream,
        kind="interval_energy",
        unit="Wh",
        value_milli=int(Decimal(value) * 1000),
        interval_start=_hour(start),
        interval_end=_hour(end),
        interval_basis="explicit",
        raw_value=value,
    )
    staged = stage_row(row, COLUMNS)
    assert isinstance(staged, StagedRow)
    return staged


def _point(data_row: int, at: float, value: str = "10") -> StagedRow:
    row = RowResult(
        data_row=data_row,
        file_line=data_row + 1,
        status="parsed",
        asset_name="A",
        stream_key="a",
        kind="counter",
        unit="Wh",
        value_milli=int(Decimal(value) * 1000),
        measured_at=_hour(at),
        raw_value=value,
    )
    staged = stage_row(row, COLUMNS)
    assert isinstance(staged, StagedRow)
    return staged


def _stored_interval(start: float, end: float, value: str = "10.000") -> MeasurementRow:
    reading = ReadingInput(value=Decimal(value), unit="Wh", interval_start=_hour(start), interval_end=_hour(end))
    return normalize(reading, MeasurementKind.INTERVAL_ENERGY)


def _stored_point(at: float, value: str = "10.000") -> MeasurementRow:
    return normalize(ReadingInput(value=Decimal(value), unit="Wh", measured_at=_hour(at)), MeasurementKind.COUNTER)


def _store(*rows: MeasurementRow, stream: str = "a") -> dict:
    intervals = [row for row in rows if row.interval_start is not None]
    current = {row.identity_key: row for row in rows}
    return {stream: classify_module.StoredStream(current=current, intervals=intervals)}


def _results(staged: list[StagedRow], stored: dict | None = None) -> list[tuple[str, str | None]]:
    found = classify_module.classify(staged, stored or {})
    assert [item.row.data_row for item in found] == [row.data_row for row in staged]
    return [(item.status.value, item.reason) for item in found]


ACCEPTED = ("accepted", None)
DUPLICATE = ("duplicate", None)
CHANGED = ("conflict", "conflict")
OVERLAP = ("conflict", "interval_overlap")


def test_rows_identical_repeats_accept_the_first() -> None:
    """
    Condition:
    - The same interval and value three times in a file.

    Expected:
    - One accepted and two duplicates, the first in file order accepted.
    """
    assert _results([_interval(1, 0, 1), _interval(2, 0, 1), _interval(3, 0, 1)]) == [ACCEPTED, DUPLICATE, DUPLICATE]


def test_rows_values_written_differently_are_duplicates() -> None:
    """
    Condition:
    - ``10`` and ``10.0`` at one identity.

    Expected:
    - One accepted and one duplicate, because 024 hands 006 one canonical value.
    """
    assert _results([_interval(1, 0, 1, "10"), _interval(2, 0, 1, "10.0")]) == [ACCEPTED, DUPLICATE]


def test_rows_a_changed_value_conflicts_the_whole_group() -> None:
    """
    Condition:
    - Three rows at one identity, one with a different value.

    Expected:
    - All three conflict with the exact message, naming the value header. None is picked silently.
    """
    found = classify_module.classify([_interval(1, 0, 1, "10"), _interval(2, 0, 1, "11"), _interval(3, 0, 1, "10")], {})

    assert [(item.status.value, item.reason) for item in found] == [CHANGED, CHANGED, CHANGED]
    assert found[1].field == "energy_wh"
    assert found[1].message == f"Baris data 2, energy_wh: {CONFLICT_TEXT}"


def test_rows_overlapping_intervals_both_conflict() -> None:
    """
    Condition:
    - ``[00:00, 02:00)`` and ``[01:00, 03:00)``: different identities on one source.

    Expected:
    - Both are ``interval_overlap`` with the exact message, naming the start header.
    """
    found = classify_module.classify([_interval(1, 0, 2), _interval(2, 1, 3)], {})

    assert [(item.status.value, item.reason) for item in found] == [OVERLAP, OVERLAP]
    assert found[0].field == "interval_start"
    assert found[0].message == f"Baris data 1, interval_start: {OVERLAP_TEXT}"


def test_rows_adjacent_intervals_are_accepted() -> None:
    """
    Condition:
    - ``[00:00, 01:00)`` and ``[01:00, 02:00)``.

    Expected:
    - Half-open intervals do not overlap.
    """
    assert _results([_interval(1, 0, 1), _interval(2, 1, 2)]) == [ACCEPTED, ACCEPTED]


def test_rows_a_chain_flags_every_member() -> None:
    """
    Condition:
    - ``[0,10) [5,6) [8,12)``, where the second and third do not touch each other.

    Expected:
    - All three are flagged, because each overlaps another.
    """
    assert _results([_interval(1, 0, 10), _interval(2, 5, 6), _interval(3, 8, 12)]) == [OVERLAP, OVERLAP, OVERLAP]


def test_rows_a_cluster_ends_where_coverage_ends() -> None:
    """
    Condition:
    - An overlapping pair, then an interval after the longer one ends.

    Expected:
    - The later interval stays accepted, even though it starts after a shorter member ended.
    """
    assert _results([_interval(1, 0, 10), _interval(2, 1, 2), _interval(3, 10, 11)]) == [OVERLAP, OVERLAP, ACCEPTED]


def test_rows_unsorted_files_are_swept_correctly() -> None:
    """
    Condition:
    - Rows out of time order, the overlapping ones far apart in the file.

    Expected:
    - The sweep finds them, and results stay in file order.
    """
    assert _results([_interval(1, 5, 6), _interval(2, 0, 1), _interval(3, 5.5, 7)]) == [OVERLAP, ACCEPTED, OVERLAP]


def test_rows_streams_do_not_interact() -> None:
    """
    Condition:
    - The same interval on two streams, one with a different value.

    Expected:
    - Each is accepted: two sources may report one time.
    """
    assert _results([_interval(1, 0, 2, "1", stream="a"), _interval(2, 0, 2, "2", stream="b")]) == [ACCEPTED, ACCEPTED]


def test_rows_a_duplicated_row_overlapping_a_third_flags_the_whole_group() -> None:
    """
    Condition:
    - A repeated interval, and a third row overlapping it.

    Expected:
    - All three rows are ``interval_overlap``: nothing of the group is accepted or a duplicate.
    """
    assert _results([_interval(1, 0, 2), _interval(2, 0, 2), _interval(3, 1, 3)]) == [OVERLAP, OVERLAP, OVERLAP]


def test_rows_stored_same_observation_is_a_duplicate() -> None:
    """
    Condition:
    - A row already stored with the same value, repeated in the file.

    Expected:
    - Every row is a duplicate, so a reimport adds nothing.
    """
    assert _results([_interval(1, 0, 1), _interval(2, 0, 1)], _store(_stored_interval(0, 1))) == [DUPLICATE, DUPLICATE]


@pytest.mark.parametrize("stored_value", ["11.000", "10"], ids=["changed_value", "changed_raw_value"])
def test_rows_stored_changed_observation_conflicts(stored_value: str) -> None:
    """
    Condition:
    - A stored row at one identity with a different value, or the same energy but different raw text.

    Expected:
    - A conflict, because 006 would store either as a revision, which this spec forbids.
    """
    assert _results([_interval(1, 0, 1)], _store(_stored_interval(0, 1, stored_value))) == [CHANGED]


def test_rows_overlap_with_stored_conflicts() -> None:
    """
    Condition:
    - A stored ``[0, 2)`` and a file row ``[1, 3)``.

    Expected:
    - ``interval_overlap``.
    """
    assert _results([_interval(1, 1, 3)], _store(_stored_interval(0, 2))) == [OVERLAP]


def test_rows_adjacent_to_stored_is_accepted() -> None:
    """
    Condition:
    - A stored ``[0, 1)`` and a file row ``[1, 2)``.

    Expected:
    - Accepted.
    """
    assert _results([_interval(1, 1, 2)], _store(_stored_interval(0, 1))) == [ACCEPTED]


def test_rows_stored_overlap_skips_the_same_identity() -> None:
    """
    Condition:
    - A stored row identical to the file row.

    Expected:
    - A duplicate, because a row does not overlap itself.
    """
    assert _results([_interval(1, 0, 2)], _store(_stored_interval(0, 2))) == [DUPLICATE]


def test_rows_stored_overlap_finds_a_long_interval_behind_short_ones() -> None:
    """
    Condition:
    - A long stored ``[0, 10)`` and short stored rows after its start, and a file row ``[9, 9.5)``.

    Expected:
    - The file row overlaps the long interval even though the nearest earlier stored row ended before it.
    """
    stored = _store(_stored_interval(0, 10), _stored_interval(1, 2), _stored_interval(3, 4))

    assert _results([_interval(1, 9, 9.5)], stored) == [OVERLAP]


def test_rows_counter_repeat_change_and_stored() -> None:
    """
    Condition:
    - Counter points: one repeated, one changed in the file, one stored with the same value, and one stored changed.

    Expected:
    - Duplicate, conflict, duplicate and conflict, by 006's point identity.
    """
    staged = [
        _point(1, 0, "1"),
        _point(2, 0, "1"),
        _point(3, 1, "1"),
        _point(4, 1, "2"),
        _point(5, 2, "3"),
        _point(6, 3, "4"),
    ]
    stored = _store(_stored_point(2, "3.000"), _stored_point(3, "9.000"))

    assert _results(staged, stored) == [ACCEPTED, DUPLICATE, CHANGED, CHANGED, DUPLICATE, CHANGED]


def test_rows_points_never_overlap() -> None:
    """
    Condition:
    - Two different points, and a stored counter delta covering both.

    Expected:
    - Both are accepted, because only interval kinds take part in overlap.
    """
    stored = classify_module.StoredStream(current={}, intervals=[_stored_interval(0, 10)])

    assert _results([_point(1, 1), _point(2, 2)], {"a": stored}) == [ACCEPTED, ACCEPTED]


@pytest.mark.parametrize(
    ("staged", "stored", "expected"),
    [
        (
            [_interval(1, 0, 2, "1"), _interval(2, 0, 2, "2"), _interval(3, 1, 3, "1")],
            [],
            [CHANGED, CHANGED, OVERLAP],
        ),
        ([_interval(1, 0, 2), _interval(2, 1, 3)], [_stored_interval(0, 2, "99.000")], [OVERLAP, OVERLAP]),
        ([_interval(1, 0, 2)], [_stored_interval(0, 2, "99.000"), _stored_interval(1, 3)], [CHANGED]),
        ([_interval(1, 0, 2)], [_stored_interval(0, 2), _stored_interval(1, 3)], [OVERLAP]),
        ([_interval(1, 0, 2), _interval(2, 0, 2)], [_stored_interval(0, 2)], [DUPLICATE, DUPLICATE]),
    ],
    ids=[
        "in_file_change_over_in_file_overlap",
        "in_file_overlap_over_stored_change",
        "stored_change_over_stored_overlap",
        "stored_overlap_over_stored_repeat",
        "stored_repeat_over_accepted",
    ],
)
def test_rows_precedence_follows_d5(staged: list[StagedRow], stored: list[MeasurementRow], expected: list) -> None:
    """
    Condition:
    - Two applicable outcomes for one row group, for each neighbouring pair in D5's order.

    Expected:
    - The earlier one wins, and each row is classified exactly once.
    """
    assert _results(staged, _store(*stored)) == expected


def test_rows_jitter_from_d21_is_an_overlap(parse_text: Callable) -> None:
    """
    Condition:
    - D21's example over twenty rows: timestamps at 0, 3601, 7199, 10800 seconds and on, from which 024 infers a
      one-hour cadence.

    Expected:
    - The second row's interval reaches past the third's start, so those two are ``interval_overlap``.
    """
    seconds = [0, 3601, 7199, *(hour * 3600 for hour in range(3, 20))]
    lines = [f"{(T0 + timedelta(seconds=second)).isoformat()},A,1" for second in seconds]
    parsed, rows = parse_text("timestamp,asset,energy_wh\n" + "\n".join(lines) + "\n")

    results = _results(_staged(parsed, rows))

    assert parsed.cadences["a"] == timedelta(hours=1)
    assert results == [ACCEPTED, OVERLAP, OVERLAP, *[ACCEPTED] * 17]
