"""Stages parsed rows through 006's normalization and summarizes the counts."""

from bisect import bisect_left
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from itertools import accumulate
from typing import BinaryIO

from app.assets.model.models import MeasurementKind
from app.imports.model.models import (
    ImportRowStatus,
    IntervalBasis,
    ParsedFile,
    RowError,
    RowReason,
    RowResult,
    RowStatus,
    ValueKind,
)
from app.imports.service.columns import VALUE_ROLES, Role, resolve_columns
from app.imports.service.parser import iter_rows
from app.measurements.model.models import MeasurementRow, ReadingInput, StoredKind
from app.measurements.service.normalize import normalize

MAX_ENERGY_MWH = 2**63 - 1
"""``measurements.energy_mwh`` is a BIGINT, and ``normalize`` has no bound for W × seconds."""
MAX_IMPORT_STREAMS = 100
"""PRD §18's working scale is 20 sources. One relation per pair costs three round trips under the site lock."""
MAX_MESSAGE_LENGTH = 500
"""Row messages may echo a cell of up to 128 KiB, and they are stored and returned for every invalid row."""
_CONFLICT_TEXT = "nilai berbeda untuk sumber dan interval yang sama."
_OVERLAP_TEXT = "interval bertumpang tindih dengan data lain pada sumber yang sama."
_ELISION = "…"
_KEPT_AT_END = 150


def bound_text(text: str) -> str:
    """Cut the middle of a long message, keeping its start and the correction at its end.

    Args:
        text (str): The message.

    Returns:
        str: The message, at most ``MAX_MESSAGE_LENGTH`` characters.
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        return text
    kept_at_start = MAX_MESSAGE_LENGTH - _KEPT_AT_END - len(_ELISION)
    return text[:kept_at_start] + _ELISION + text[-_KEPT_AT_END:]


def chosen_kind(parsed: ParsedFile) -> ValueKind | None:
    """Return what a file's values mean, once known.

    Args:
        parsed (ParsedFile): The file.

    Returns:
        ValueKind | None: The only value column's kind, the answered one among several, or None.
    """
    if len(parsed.value_kinds) == 1:
        return parsed.value_kinds[0]
    return parsed.answers.value_kind if parsed.answers.value_kind in parsed.value_kinds else None


@dataclass(frozen=True, slots=True)
class FileColumns:
    """The headers a row's own messages name, worked out once per file.

    Attributes:
        value_header (str): The value column's header.
        time_header (str): The timestamp or interval start header.
        header_line (int): File line of the header.
    """

    value_header: str
    time_header: str
    header_line: int


def file_columns(parsed: ParsedFile) -> FileColumns:
    """Work out the headers a file's row messages name.

    Args:
        parsed (ParsedFile): A file with no structural error.

    Returns:
        FileColumns: Its headers. The value header is empty while the value column is unchosen.
    """
    columns = resolve_columns(parsed.headers).columns
    kind = chosen_kind(parsed)
    time_role = Role.TIMESTAMP if Role.TIMESTAMP in columns else Role.INTERVAL_START
    assert parsed.header_line is not None
    return FileColumns(
        value_header="" if kind is None else parsed.headers[columns[VALUE_ROLES[kind]]],
        time_header=parsed.headers[columns[time_role]],
        header_line=parsed.header_line,
    )


def row_message(data_row: int, file_line: int, header_line: int, field_name: str, text: str) -> str:
    """Render a row message in the parser's form.

    Args:
        data_row (int): Nonblank data row, from 1.
        file_line (int): File line the record starts on.
        header_line (int): File line of the header.
        field_name (str): The header it concerns.
        text (str): The correction.

    Returns:
        str: The message, naming the file line only when it differs from the data row's place.
    """
    note = "" if file_line == data_row + header_line else f" (baris file {file_line})"
    return f"Baris data {data_row}{note}, {field_name}: {text}"


@dataclass(frozen=True, slots=True)
class StagedRow:
    """A parsed row in 006's terms. It keeps the normalized fields, not a ``MeasurementRow`` per row.

    A retained Pydantic row costs about 1.2 KiB, which took a 150,000-row preview over its 256 MiB bound (T023).

    Attributes:
        data_row (int): Nonblank data row, from 1.
        file_line (int): File line the record starts on.
        asset_name (str): The name as written.
        stream_key (str): The stream.
        identity_key (str): 006's identity.
        stored_kind (StoredKind): 006's row kind.
        interval_start (datetime | None): Interval start, inclusive.
        interval_end (datetime | None): Interval end, exclusive.
        measured_at (datetime | None): Capture time of a point.
        energy_mwh (int | None): Integer mWh of an interval row.
        value (str): The canonical value 006 stores as raw, with exactly three places.
        kind (ValueKind): What the value means.
        unit (str): The value's unit.
        value_milli (int): The exact value in thousandths of the unit.
        interval_basis (IntervalBasis | None): Where the interval end came from.
        raw_value (str): The value cell as written.
        raw_start (str | None): The timestamp or interval start cell as written.
        raw_end (str | None): The interval end cell as written.
        columns (FileColumns): The file's headers.
        observation (MeasurementRow): The normalized row, rebuilt when asked for. "Same" is its ``same_observation``.
    """

    data_row: int
    file_line: int
    asset_name: str
    stream_key: str
    identity_key: str
    stored_kind: StoredKind
    interval_start: datetime | None
    interval_end: datetime | None
    measured_at: datetime | None
    energy_mwh: int | None
    value: str
    kind: ValueKind
    unit: str
    value_milli: int
    interval_basis: IntervalBasis | None
    raw_value: str
    raw_start: str | None
    raw_end: str | None
    columns: FileColumns

    @property
    def observation(self) -> MeasurementRow:
        """The normalized row this staged row was made from."""
        return MeasurementRow(
            identity_key=self.identity_key,
            source_record_id=None,
            kind=self.stored_kind,
            interval_start=self.interval_start,
            interval_end=self.interval_end,
            measured_at=self.measured_at,
            energy_mwh=self.energy_mwh,
            raw_value=self.value,
            raw_unit=self.unit,
        )


def stage_row(row: RowResult, columns: FileColumns) -> StagedRow | RowError:
    """Normalize a parsed row, or return why it cannot be stored.

    Args:
        row (RowResult): A parsed or invalid row. Pending rows are counted by the caller and never staged.
        columns (FileColumns): The file's headers.

    Returns:
        StagedRow | RowError: The staged row, or the failure of an invalid one.

    Raises:
        ReadingRejectedError: When 006 refuses a row 024 parsed. The two disagree, which is a bug.
    """
    if row.error is not None:
        return row.error
    assert row.value is not None and row.value_milli is not None and row.kind is not None and row.unit is not None
    assert row.asset_name is not None and row.stream_key is not None and row.raw_value is not None
    reading = ReadingInput(
        value=row.value,
        unit=row.unit,
        interval_start=row.interval_start,
        interval_end=row.interval_end,
        measured_at=row.measured_at,
    )
    observation = normalize(reading, MeasurementKind(row.kind.value))
    if observation.energy_mwh is not None and observation.energy_mwh > MAX_ENERGY_MWH:
        text = f'angka "{row.raw_value.strip()}" terlalu besar. Periksa nilai dan satuannya.'
        return RowError(
            reason=RowReason.VALUE_TOO_LARGE,
            data_row=row.data_row,
            file_line=row.file_line,
            field=columns.value_header,
            message=row_message(row.data_row, row.file_line, columns.header_line, columns.value_header, text),
        )
    return StagedRow(
        data_row=row.data_row,
        file_line=row.file_line,
        asset_name=row.asset_name,
        stream_key=row.stream_key,
        identity_key=observation.identity_key,
        stored_kind=observation.kind,
        interval_start=observation.interval_start,
        interval_end=observation.interval_end,
        measured_at=observation.measured_at,
        energy_mwh=observation.energy_mwh,
        value=format(row.value, "f"),
        kind=row.kind,
        unit=row.unit,
        value_milli=row.value_milli,
        interval_basis=row.interval_basis,
        raw_value=row.raw_value,
        raw_start=row.raw_start,
        raw_end=row.raw_end,
        columns=columns,
    )


@dataclass(slots=True)
class StreamFacts:
    """What a file says about one stream, including one whose rows are all invalid.

    Attributes:
        stream_key (str): The stream.
        names (dict[str, None]): Its asset names in first-seen order.
        kind (ValueKind | None): What its values mean, once known.
        unit (str | None): Its unit, once known.
        cadence (timedelta | None): The cadence the parser inferred, for a timestamp-only stream.
        interval_basis (IntervalBasis | None): Where its interval ends came from.
        period_start (datetime | None): Earliest instant of its staged rows.
        period_end (datetime | None): Latest instant of its staged rows.
    """

    stream_key: str
    names: dict[str, None] = field(default_factory=dict)
    kind: ValueKind | None = None
    unit: str | None = None
    cadence: timedelta | None = None
    interval_basis: IntervalBasis | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None


def _note_period(facts: StreamFacts, start: datetime, end: datetime) -> None:
    facts.period_start = start if facts.period_start is None else min(facts.period_start, start)
    facts.period_end = end if facts.period_end is None else max(facts.period_end, end)


def row_span(row: StagedRow) -> tuple[datetime, datetime]:
    """Return the instants a staged row covers.

    Args:
        row (StagedRow): The row.

    Returns:
        tuple[datetime, datetime]: Its interval, or its capture time twice for a counter point.
    """
    if row.interval_start is not None and row.interval_end is not None:
        return row.interval_start, row.interval_end
    assert row.measured_at is not None
    return row.measured_at, row.measured_at


@dataclass(slots=True)
class StagedFile:
    """Every row of a file, sorted by what can happen to it.

    Attributes:
        staged (list[StagedRow]): Rows ready to classify, in file order.
        errors (list[RowError]): Invalid rows, in file order.
        pending (int): Rows waiting on an answer. They are counted, not stored.
        streams (list[StreamFacts]): Streams in first-seen order.
    """

    staged: list[StagedRow] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)
    pending: int = 0
    streams: list[StreamFacts] = field(default_factory=list)


def stage_file(source: BinaryIO, parsed: ParsedFile) -> StagedFile:
    """Read every row once and stage it. CPU work: call it through ``asyncio.to_thread``.

    Args:
        source (BinaryIO): The parsed file.
        parsed (ParsedFile): Its file-level answers, with no structural error.

    Returns:
        StagedFile: The file's rows and streams.
    """
    result = StagedFile()
    columns = file_columns(parsed)
    streams: dict[str, StreamFacts] = {}
    for row in iter_rows(source, parsed):
        facts = None
        if row.stream_key is not None and row.asset_name is not None:
            facts = streams.get(row.stream_key)
            if facts is None:
                facts = StreamFacts(stream_key=row.stream_key, cadence=parsed.cadences.get(row.stream_key))
                streams[row.stream_key] = facts
            facts.names.setdefault(row.asset_name)
            facts.kind = facts.kind or row.kind
            facts.unit = facts.unit or row.unit
        if row.status is RowStatus.PENDING:
            result.pending += 1
            continue
        staged = stage_row(row, columns)
        if isinstance(staged, RowError):
            result.errors.append(staged)
            continue
        assert facts is not None
        facts.interval_basis = facts.interval_basis or staged.interval_basis
        _note_period(facts, *row_span(staged))
        result.staged.append(staged)
    result.streams = list(streams.values())
    return result


@dataclass(frozen=True, slots=True)
class RowCounts:
    """How many rows ended up where. A CHECK constraint enforces that they add up to ``total``.

    Attributes:
        total (int): Nonblank data rows.
        accepted (int): Rows a commit would add.
        invalid (int): Rows that cannot be read.
        duplicate (int): Exact repeats.
        conflict (int): Changed values and overlapping intervals.
        pending (int): Rows waiting on an answer.
    """

    total: int
    accepted: int = 0
    invalid: int = 0
    duplicate: int = 0
    conflict: int = 0
    pending: int = 0


@dataclass(frozen=True, slots=True)
class PreviewSummary:
    """Whether a preview could be committed.

    Attributes:
        blocked (bool): Whether a commit would be refused.
        block_reasons (list[str]): Why, in fixed order.
        needs_acknowledgment (bool): Whether invalid rows must be acknowledged first.
    """

    blocked: bool
    block_reasons: list[str]
    needs_acknowledgment: bool


def summarize(counts: RowCounts, *, open_questions: int, streams: int = 0) -> PreviewSummary:
    """Decide whether a preview is blocked. Skipped rows never waive a question or a conflict.

    Args:
        counts (RowCounts): The reconciled counts.
        open_questions (int): How many questions are open.
        streams (int, optional): How many streams hold staged rows. Defaults to 0.

    Returns:
        PreviewSummary: The decision.
    """
    reasons: list[str] = []
    if open_questions or counts.pending:
        reasons.append("Lengkapi pemetaan terlebih dahulu.")
    if counts.invalid * 5 > counts.total:
        reasons.append(f"Impor diblokir: {counts.invalid} dari {counts.total} baris tidak valid.")
    if counts.conflict:
        reasons.append(
            "Nilai berbeda ditemukan untuk sumber dan interval yang sama. "
            "Pilih sumber atau perbaiki data sebelum melanjutkan."
        )
    if streams > MAX_IMPORT_STREAMS:
        reasons.append(
            f"Berkas ini memuat {streams} perangkat, melebihi batas {MAX_IMPORT_STREAMS} perangkat per impor. "
            "Pisahkan berkasnya lalu coba lagi."
        )
    if not counts.accepted and not counts.duplicate and not reasons:
        reasons.append("Tidak ada baris valid yang dapat diimpor.")
    blocked = bool(reasons)
    return PreviewSummary(
        blocked=blocked, block_reasons=reasons, needs_acknowledgment=counts.invalid > 0 and not blocked
    )


@dataclass(frozen=True, slots=True)
class StoredStream:
    """What a resolved stream's source already holds.

    Attributes:
        current (dict[str, MeasurementRow]): Current revisions of the file's identities.
        intervals (list[MeasurementRow]): Current rows with energy overlapping the stream's period.
    """

    current: dict[str, MeasurementRow]
    intervals: list[MeasurementRow]


@dataclass(frozen=True, slots=True)
class Classified:
    """One staged row's result. Every staged row gets exactly one.

    Attributes:
        row (StagedRow): The row.
        status (ImportRowStatus): Accepted, duplicate or conflict.
        reason (str | None): ``conflict`` or ``interval_overlap`` for a conflict.
        field (str | None): The header a conflict names.
        message (str | None): The conflict's message.
    """

    row: StagedRow
    status: ImportRowStatus
    reason: str | None = None
    field: str | None = None
    message: str | None = None


class _Verdict(Enum):
    """What happened to one identity of one stream. Absent means its first row is accepted."""

    CHANGED = auto()
    OVERLAP = auto()
    REPEATED = auto()


@dataclass(slots=True)
class _Stream:
    """One stream's identities: the first row of each, and which of them hold different values."""

    firsts: dict[str, StagedRow] = field(default_factory=dict)
    changed: set[str] = field(default_factory=set)


class _StoredIntervals:
    """Stored intervals of one source, asked whether a candidate overlaps a different identity."""

    def __init__(self, rows: list[MeasurementRow]) -> None:
        """Index the rows by start, with the furthest end reached so far.

        Args:
            rows (list[MeasurementRow]): Stored rows with interval bounds.
        """
        self.rows = sorted(rows, key=lambda row: row.interval_start)
        self.starts = [row.interval_start for row in self.rows]
        self.reach = list(accumulate((row.interval_end for row in self.rows), max))

    def overlap(self, candidate: StagedRow) -> bool:
        """Tell whether a candidate overlaps a stored interval of another identity. Adjacent ones do not.

        Args:
            candidate (StagedRow): An interval row.

        Returns:
            bool: True when it overlaps one.
        """
        for index in range(bisect_left(self.starts, candidate.interval_end) - 1, -1, -1):
            if self.reach[index] <= candidate.interval_start:
                return False
            stored = self.rows[index]
            if stored.interval_end > candidate.interval_start and stored.identity_key != candidate.identity_key:
                return True
        return False


def _overlapping_in_file(firsts: Iterable[StagedRow]) -> set[str]:
    """Sweep one stream's intervals in start order, in O(n log n), and flag every cluster of two or more."""
    flagged: set[str] = set()
    cluster: list[str] = []
    cluster_end: datetime | None = None
    intervals = [row for row in firsts if row.interval_start is not None]
    for row in sorted(intervals, key=lambda item: item.interval_start):
        if cluster_end is not None and row.interval_start < cluster_end:
            cluster.append(row.identity_key)
            cluster_end = max(cluster_end, row.interval_end)
            continue
        if len(cluster) > 1:
            flagged.update(cluster)
        cluster, cluster_end = [row.identity_key], row.interval_end
    if len(cluster) > 1:
        flagged.update(cluster)
    return flagged


def _verdicts(stream: _Stream, stored: StoredStream | None) -> dict[str, _Verdict]:
    """Apply D5's precedence to each identity of one stream."""
    overlapping = _overlapping_in_file(stream.firsts.values())
    current = {} if stored is None else stored.current
    intervals = _StoredIntervals([] if stored is None else stored.intervals)
    verdicts: dict[str, _Verdict] = {}
    for identity, first in stream.firsts.items():
        if identity in stream.changed:
            verdicts[identity] = _Verdict.CHANGED
        elif identity in overlapping:
            verdicts[identity] = _Verdict.OVERLAP
        else:
            existing = current.get(identity)
            if existing is not None and not first.observation.same_observation(existing):
                verdicts[identity] = _Verdict.CHANGED
            elif first.interval_start is not None and intervals.overlap(first):
                verdicts[identity] = _Verdict.OVERLAP
            elif existing is not None:
                verdicts[identity] = _Verdict.REPEATED
    return verdicts


def _conflict(row: StagedRow, reason: str, field_name: str, text: str) -> Classified:
    message = row_message(row.data_row, row.file_line, row.columns.header_line, field_name, text)
    return Classified(row=row, status=ImportRowStatus.CONFLICT, reason=reason, field=field_name, message=message)


def classify(staged: list[StagedRow], stored: Mapping[str, StoredStream]) -> list[Classified]:
    """Classify every staged row against the file and stored data, using 006's identity and comparison.

    ``measurements`` has no exclusion constraint, so overlapping intervals with different identities would both be
    stored and summed: this is the only guard against them. CPU work: call it through ``asyncio.to_thread``.

    Args:
        staged (list[StagedRow]): The file's staged rows.
        stored (Mapping[str, StoredStream]): What each resolved stream's source holds, by stream key.

    Returns:
        list[Classified]: One result per row, in the given order.
    """
    streams: dict[str, _Stream] = {}
    for row in staged:
        stream = streams.setdefault(row.stream_key, _Stream())
        first = stream.firsts.setdefault(row.identity_key, row)
        if first is not row and not row.observation.same_observation(first.observation):
            stream.changed.add(row.identity_key)
    verdicts = {key: _verdicts(stream, stored.get(key)) for key, stream in streams.items()}
    results: list[Classified] = []
    for row in staged:
        verdict = verdicts[row.stream_key].get(row.identity_key)
        if verdict is _Verdict.CHANGED:
            results.append(_conflict(row, "conflict", row.columns.value_header, _CONFLICT_TEXT))
        elif verdict is _Verdict.OVERLAP:
            results.append(_conflict(row, "interval_overlap", row.columns.time_header, _OVERLAP_TEXT))
        elif verdict is None and streams[row.stream_key].firsts[row.identity_key] is row:
            results.append(Classified(row=row, status=ImportRowStatus.ACCEPTED))
        else:
            results.append(Classified(row=row, status=ImportRowStatus.DUPLICATE))
    return results
