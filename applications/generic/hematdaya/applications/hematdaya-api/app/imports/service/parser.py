"""Reads a CSV file in two passes: file-level answers first, then one row at a time."""

from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import BinaryIO, NamedTuple

from app.imports.model.models import (
    CellFailure,
    IntervalBasis,
    MeaningAnswers,
    MeaningQuestion,
    ParsedFile,
    PowerMeaning,
    QuestionKind,
    RowError,
    RowReason,
    RowResult,
    RowStatus,
    StructuralError,
    StructuralReason,
    ValueKind,
)
from app.imports.service.cadence import infer_cadence
from app.imports.service.columns import VALUE_ROLES, ColumnMap, Role, resolve_columns
from app.imports.service.dialect import Record, detect_delimiter, has_bom, read_records, source_size
from app.imports.service.numbers import parse_decimal
from app.imports.service.times import impossible_time, parse_time, resolve_local

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 150_000
MAX_NAME_LENGTH = 60
MIN_INTERVAL_MINUTES = 1
MAX_INTERVAL_MINUTES = 1440
_MIB = 1024 * 1024
_UNITS = {ValueKind.INTERVAL_ENERGY: "Wh", ValueKind.AVERAGE_POWER: "W", ValueKind.COUNTER: "Wh"}
_ROW_FIELD = "baris"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MICROSECOND = timedelta(microseconds=1)


def _chosen_kind(value_kinds: list[ValueKind], answers: MeaningAnswers) -> ValueKind | None:
    if len(value_kinds) == 1:
        return value_kinds[0]
    return answers.value_kind if answers.value_kind in value_kinds else None


def _cell(fields: list[str], position: int | None) -> str:
    return fields[position] if position is not None and position < len(fields) else ""


def _stream_key(source_cell: str, name: str) -> str:
    return (source_cell.strip() or name.strip()).lower()


def _instant(raw: str, site_timezone: str, confirmed: bool) -> datetime | CellFailure:
    """Read a time cell as far as the answers allow: UTC, or still naive while the zone is unconfirmed."""
    value = parse_time(raw)
    if isinstance(value, CellFailure) or value.tzinfo is not None or not confirmed:
        return value
    return resolve_local(value, site_timezone, raw)


@dataclass
class _Scan:
    """What the first pass keeps: file-level answers only, never the rows."""

    site_timezone: str
    answers: MeaningAnswers
    header_line: int | None = None
    headers: list[str] = field(default_factory=list)
    columns: ColumnMap | None = None
    total_rows: int = 0
    blank_lines: int = 0
    asset_names: dict[str, None] = field(default_factory=dict)
    has_naive: bool = False
    timestamps: dict[str, list[int]] = field(default_factory=dict)
    failure: StructuralError | None = None

    def note_row(self, fields: list[str], columns: ColumnMap) -> None:
        """Keep what the file-level answers need from one data row.

        Args:
            fields (list[str]): The row's cells.
            columns (ColumnMap): The file's columns.
        """
        roles = columns.columns
        name = _cell(fields, roles.get(Role.ASSET)).strip()
        if name:
            self.asset_names.setdefault(name)
        if Role.TIMESTAMP not in roles:
            self._note_naive(_cell(fields, roles.get(Role.INTERVAL_START)))
            self._note_naive(_cell(fields, roles.get(Role.INTERVAL_END)))
            return
        raw = _cell(fields, roles[Role.TIMESTAMP])
        self._note_naive(raw)
        if name and _chosen_kind(columns.value_kinds, self.answers) is not ValueKind.COUNTER:
            self._note_timestamp(raw, _stream_key(_cell(fields, roles.get(Role.SOURCE)), name))

    def _note_naive(self, raw: str) -> None:
        if not self.has_naive:
            value = parse_time(raw)
            self.has_naive = isinstance(value, datetime) and value.tzinfo is None

    def _note_timestamp(self, raw: str, stream: str) -> None:
        # Any row with a name and a valid time counts, whatever its value, or a bad value would open a false gap.
        value = _instant(raw, self.site_timezone, self.answers.timezone_confirmed)
        if isinstance(value, datetime):
            instant = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
            self.timestamps.setdefault(stream, []).append((instant - _EPOCH) // _MICROSECOND)


def _scan(source: BinaryIO, delimiter: str, scan: _Scan) -> None:
    for record in read_records(source, delimiter):
        if isinstance(record, StructuralError):
            scan.failure = record
            return
        if record.blank:
            scan.blank_lines += 1
        elif scan.columns is None:
            scan.header_line = record.file_line
            scan.headers = [header.strip() for header in record.fields]
            scan.columns = resolve_columns(scan.headers)
        else:
            scan.total_rows += 1
            # Past the limit the file is already refused, so only the true count is still worth keeping.
            if not scan.columns.errors and scan.total_rows <= MAX_ROWS:
                scan.note_row(record.fields, scan.columns)


def _row_limit_errors(total_rows: int) -> list[StructuralError]:
    if total_rows > MAX_ROWS:
        return [
            StructuralError(
                reason=StructuralReason.TOO_MANY_ROWS,
                message=f"{total_rows} baris data melebihi batas 150.000 baris.",
            )
        ]
    if not total_rows:
        return [StructuralError(reason=StructuralReason.NO_DATA_ROWS, message="Tidak ada baris data setelah header.")]
    return []


def _too_large_error(size: int) -> StructuralError:
    # Rounded up in integers, so a file one byte over the limit never reads as exactly 10 MiB.
    whole, tenth = divmod(-(-size * 10 // _MIB), 10)
    shown = f"{whole},{tenth}" if tenth else str(whole)
    return StructuralError(reason=StructuralReason.TOO_LARGE, message=f"Ukuran {shown} MiB melebihi batas 10 MiB.")


def _questions(
    columns: ColumnMap,
    answers: MeaningAnswers,
    site_timezone: str,
    has_naive: bool,
    cadences: dict[str, timedelta | None],
) -> list[MeaningQuestion]:
    questions: list[MeaningQuestion] = []
    kind = _chosen_kind(columns.value_kinds, answers)
    if kind is None:
        questions.append(
            MeaningQuestion(
                kind=QuestionKind.VALUE_KIND,
                message=(
                    "Berkas memiliki lebih dari satu kolom nilai. "
                    "Pilih satu jenis nilai; nilai energi dan daya tidak dijumlahkan."
                ),
            )
        )
    if kind is ValueKind.AVERAGE_POWER and answers.power_meaning is not PowerMeaning.AVERAGE:
        message = (
            "Daya sesaat tidak dapat diubah menjadi energi. Impor diblokir; "
            "gunakan data energi interval atau daya rata-rata interval."
            if answers.power_meaning is PowerMeaning.INSTANTANEOUS
            else "Konfirmasi arti kolom daya: rata-rata selama interval atau daya sesaat."
        )
        questions.append(MeaningQuestion(kind=QuestionKind.POWER_MEANING, message=message))
    if has_naive and not answers.timezone_confirmed:
        questions.append(
            MeaningQuestion(
                kind=QuestionKind.TIMEZONE,
                message=f"Waktu tanpa zona waktu. Konfirmasi bahwa waktu dibaca sebagai {site_timezone}.",
            )
        )
    out_of_range = tuple(
        stream
        for stream, minutes in answers.interval_minutes.items()
        if not MIN_INTERVAL_MINUTES <= minutes <= MAX_INTERVAL_MINUTES
    )
    if out_of_range:
        questions.append(
            MeaningQuestion(
                kind=QuestionKind.INTERVAL_DURATION,
                message="Panjang interval harus bilangan bulat 1–1440 menit.",
                streams=out_of_range,
            )
        )
    if kind is not ValueKind.COUNTER:
        unknown = tuple(
            stream for stream, cadence in cadences.items() if cadence is None and stream not in answers.interval_minutes
        )
        if unknown:
            questions.append(
                MeaningQuestion(
                    kind=QuestionKind.INTERVAL_DURATION,
                    message=(
                        f"Interval tidak dapat disimpulkan untuk: {', '.join(unknown)} "
                        "(satu baris atau jarak tidak teratur). Isi panjang interval."
                    ),
                    streams=unknown,
                )
            )
    return questions


def parse(source: BinaryIO, *, site_timezone: str, answers: MeaningAnswers = MeaningAnswers()) -> ParsedFile:
    """Read a file's structure and everything that needs the whole file. Keeps no rows.

    Args:
        source (BinaryIO): A seekable binary file. It stays open.
        site_timezone (str): IANA name, validated by the caller, that naive times are read in once confirmed.
        answers (MeaningAnswers, optional): The user's answers. Defaults to none given.

    Returns:
        ParsedFile: The file-level answers, with any structural errors and questions.
    """
    had_bom = has_bom(source)
    context = {"site_timezone": site_timezone, "answers": answers, "had_bom": had_bom}
    size = source_size(source)
    if size > MAX_BYTES:
        return _failed_file(_too_large_error(size), **context)
    delimiter = detect_delimiter(source)
    if isinstance(delimiter, StructuralError):
        return _failed_file(delimiter, **context)
    scan = _Scan(site_timezone=site_timezone, answers=answers)
    _scan(source, delimiter, scan)
    if scan.failure is not None:
        return _failed_file(scan.failure, delimiter=delimiter, **context)
    assert scan.columns is not None  # A nonblank first line always yields a header.
    errors = scan.columns.errors + _row_limit_errors(scan.total_rows)
    cadences = {stream: infer_cadence(times) for stream, times in scan.timestamps.items()}
    return ParsedFile(
        structural_errors=errors,
        questions=[] if errors else _questions(scan.columns, answers, site_timezone, scan.has_naive, cadences),
        delimiter=delimiter,
        header_line=scan.header_line,
        headers=scan.headers,
        ignored_columns=scan.columns.ignored_columns,
        value_kinds=scan.columns.value_kinds,
        total_rows=scan.total_rows,
        blank_lines=scan.blank_lines,
        asset_names=list(scan.asset_names),
        has_naive_timestamps=scan.has_naive,
        cadences=cadences,
        **context,
    )


def _failed_file(
    error: StructuralError, *, site_timezone: str, answers: MeaningAnswers, had_bom: bool, delimiter: str | None = None
) -> ParsedFile:
    return ParsedFile(
        structural_errors=[error],
        questions=[],
        site_timezone=site_timezone,
        answers=answers,
        delimiter=delimiter,
        had_bom=had_bom,
        header_line=None,
        headers=[],
        ignored_columns=[],
        value_kinds=[],
        total_rows=0,
        blank_lines=0,
        asset_names=[],
        has_naive_timestamps=False,
        cadences={},
    )


@dataclass(frozen=True)
class _Reading:
    """What every row of one file needs to know, worked out once."""

    parsed: ParsedFile
    delimiter: str
    columns: dict[Role, int]
    kind: ValueKind | None
    value_position: int | None
    meaning_settled: bool


class _RowTimes(NamedTuple):
    """A row's times once known. All None while a row waits for an answer."""

    interval_start: datetime | None = None
    interval_end: datetime | None = None
    interval_basis: IntervalBasis | None = None
    measured_at: datetime | None = None


class _TimeFailure(NamedTuple):
    """Which time cell failed, and why."""

    position: int
    failure: CellFailure


def _reading_of(parsed: ParsedFile, delimiter: str) -> _Reading:
    columns = resolve_columns(parsed.headers).columns
    kind = _chosen_kind(parsed.value_kinds, parsed.answers)
    return _Reading(
        parsed=parsed,
        delimiter=delimiter,
        columns=columns,
        kind=kind,
        value_position=None if kind is None else columns[VALUE_ROLES[kind]],
        meaning_settled=kind is not ValueKind.AVERAGE_POWER or parsed.answers.power_meaning is PowerMeaning.AVERAGE,
    )


def _duration(stream: str, parsed: ParsedFile) -> tuple[timedelta, IntervalBasis] | None:
    declared = parsed.answers.interval_minutes.get(stream)
    if declared is not None:
        if MIN_INTERVAL_MINUTES <= declared <= MAX_INTERVAL_MINUTES:
            return timedelta(minutes=declared), IntervalBasis.DECLARED
        return None
    cadence = parsed.cadences.get(stream)
    return None if cadence is None else (cadence, IntervalBasis.INFERRED)


def _explicit_times(fields: list[str], reading: _Reading) -> _RowTimes | _TimeFailure:
    parsed = reading.parsed
    bounds: list[datetime] = []
    for role in (Role.INTERVAL_START, Role.INTERVAL_END):
        position = reading.columns[role]
        value = _instant(fields[position], parsed.site_timezone, parsed.answers.timezone_confirmed)
        if isinstance(value, CellFailure):
            return _TimeFailure(position, value)
        bounds.append(value)
    start, end = bounds
    # Two naive bounds share a zone, so their wall clocks compare. A naive bound beside an offset has no instant yet.
    comparable = (start.tzinfo is None) == (end.tzinfo is None)
    if comparable and end <= start:
        reversed_bounds = CellFailure(
            reason=RowReason.INTERVAL_REVERSED, detail="akhir interval harus setelah awal interval."
        )
        return _TimeFailure(reading.columns[Role.INTERVAL_END], reversed_bounds)
    if start.tzinfo is None or end.tzinfo is None:
        return _RowTimes()
    return _RowTimes(interval_start=start, interval_end=end, interval_basis=IntervalBasis.EXPLICIT)


def _timestamp_times(fields: list[str], reading: _Reading, stream: str) -> _RowTimes | _TimeFailure:
    parsed = reading.parsed
    position = reading.columns[Role.TIMESTAMP]
    raw = fields[position]
    instant = _instant(raw, parsed.site_timezone, parsed.answers.timezone_confirmed)
    if isinstance(instant, CellFailure):
        return _TimeFailure(position, instant)
    if instant.tzinfo is None:
        return _RowTimes()
    if reading.kind is ValueKind.COUNTER:
        return _RowTimes(measured_at=instant)
    duration = _duration(stream, parsed)
    if duration is None:
        return _RowTimes()
    try:
        end = instant + duration[0]
    except OverflowError:
        return _TimeFailure(position, impossible_time(raw.strip()))
    return _RowTimes(interval_start=instant, interval_end=end, interval_basis=duration[1])


def _invalid(known: dict[str, object], reading: _Reading, name: str, failure: CellFailure) -> RowResult:
    data_row, file_line = known["data_row"], known["file_line"]
    line_note = "" if file_line == data_row + reading.parsed.header_line else f" (baris file {file_line})"
    error = RowError(
        reason=failure.reason,
        data_row=data_row,
        file_line=file_line,
        field=name,
        message=f"Baris data {data_row}{line_note}, {name}: {failure.detail}",
    )
    return RowResult(status=RowStatus.INVALID, error=error, **known)


def _column_count_failure(got: int, expected: int, delimiter: str) -> CellFailure:
    hint = ' Koma desimal harus diberi tanda kutip, misalnya "12,5".' if delimiter == "," else ""
    return CellFailure(
        reason=RowReason.COLUMN_COUNT, detail=f"jumlah kolom {got} tidak sama dengan header ({expected}).{hint}"
    )


def _value_failure(value: int | CellFailure | None) -> CellFailure | None:
    if isinstance(value, CellFailure):
        return value
    if value is None:
        return CellFailure(
            reason=RowReason.VALUE_EMPTY, detail="nilai kosong. Isi angka 0 atau lebih; kosong tidak dianggap 0."
        )
    if value < 0:
        return CellFailure(reason=RowReason.NEGATIVE, detail="gunakan angka 0 atau lebih.")
    return None


def _name_failure(role: Role, text: str) -> CellFailure | None:
    if role is Role.ASSET and not text:
        return CellFailure(reason=RowReason.ASSET_EMPTY, detail="nama perangkat kosong.")
    if len(text) <= MAX_NAME_LENGTH:
        return None
    if role is Role.ASSET:
        return CellFailure(
            reason=RowReason.ASSET_TOO_LONG,
            detail="nama lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.",
        )
    return CellFailure(
        reason=RowReason.SOURCE_TOO_LONG,
        detail="nama sumber lebih dari 60 karakter; tidak dipotong otomatis. Perpendek namanya.",
    )


def _read_row(record: Record, data_row: int, reading: _Reading) -> RowResult:
    headers, columns = reading.parsed.headers, reading.columns
    fields = record.fields
    known: dict[str, object] = {"data_row": data_row, "file_line": record.file_line}
    if len(fields) != len(headers):
        failure = _column_count_failure(len(fields), len(headers), reading.delimiter)
        return _invalid(known, reading, _ROW_FIELD, failure)
    has_timestamp = Role.TIMESTAMP in columns
    known |= {
        "raw_start": fields[columns[Role.TIMESTAMP if has_timestamp else Role.INTERVAL_START]],
        "raw_end": None if has_timestamp else fields[columns[Role.INTERVAL_END]],
    }
    name = fields[columns[Role.ASSET]].strip()
    source_cell = _cell(fields, columns.get(Role.SOURCE)).strip()
    for role, text in ((Role.ASSET, name), (Role.SOURCE, source_cell)):
        failure = _name_failure(role, text)
        if failure is not None:
            return _invalid(known, reading, headers[columns[role]], failure)
    stream = _stream_key(source_cell, name)
    known |= {"asset_name": name, "stream_key": stream}
    if reading.kind is None or reading.value_position is None:
        return RowResult(status=RowStatus.PENDING, **known)
    raw_value = fields[reading.value_position]
    known |= {"kind": reading.kind, "unit": _UNITS[reading.kind], "raw_value": raw_value}
    times = _timestamp_times(fields, reading, stream) if has_timestamp else _explicit_times(fields, reading)
    if isinstance(times, _TimeFailure):
        return _invalid(known, reading, headers[times.position], times.failure)
    value = parse_decimal(raw_value, reading.delimiter)
    failure = _value_failure(value)
    if failure is not None:
        return _invalid(known, reading, headers[reading.value_position], failure)
    resolved = times.measured_at is not None or times.interval_start is not None
    status = RowStatus.PARSED if resolved and reading.meaning_settled else RowStatus.PENDING
    return RowResult(status=status, value_milli=value, **known, **times._asdict())


def iter_rows(source: BinaryIO, parsed: ParsedFile) -> Iterator[RowResult]:
    """Yield one row at a time, keeping none of them.

    Args:
        source (BinaryIO): The source given to ``parse``. It stays open.
        parsed (ParsedFile): Its file-level answers.

    Yields:
        RowResult: Each nonblank data row in file order. Nothing when the file has structural errors.

    Raises:
        RuntimeError: When the source changed between the two passes, which is a bug in the caller.
    """
    if not parsed.ok or parsed.delimiter is None:
        return
    reading = _reading_of(parsed, parsed.delimiter)
    header_seen = False
    data_row = 0
    with closing(read_records(source, parsed.delimiter)) as records:
        for record in records:
            if isinstance(record, StructuralError):
                raise RuntimeError("The source changed between the two passes.")
            if record.blank:
                continue
            if not header_seen:
                header_seen = True
                continue
            data_row += 1
            yield _read_row(record, data_row, reading)
