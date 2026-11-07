# Implementation Plan: CSV parser

**Branch**: `m5/csv-parser` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

A pure parser with no database and no import from M1, ported rule by rule with its tests. 025 is the layer that meets M1.

## Project Structure

```text
app/imports/
├── model/models.py                  # ParsedFile, RowResult, MeaningQuestion and their parts
└── service/{dialect.py, columns.py, numbers.py, times.py, cadence.py, parser.py}
tests/unit/imports/                  # one file per module, plus oracles, boundary and performance
```

## Parser contract

A stream is one source in a file: the `source` cell, or the asset name when that is blank, stripped and lower-cased.

```python
# app/imports/model/models.py: frozen Pydantic models
class ValueKind(StrEnum):
    INTERVAL_ENERGY = "interval_energy"
    AVERAGE_POWER = "average_power"
    COUNTER = "counter"


class PowerMeaning(StrEnum):
    AVERAGE = "average"
    INSTANTANEOUS = "instantaneous"


class QuestionKind(StrEnum):
    VALUE_KIND = "value_kind"
    POWER_MEANING = "power_meaning"
    TIMEZONE = "timezone"
    INTERVAL_DURATION = "interval_duration"


class RowStatus(StrEnum):
    PARSED = "parsed"
    INVALID = "invalid"
    PENDING = "pending"


class IntervalBasis(StrEnum):
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    DECLARED = "declared"


class StructuralReason(StrEnum): ...  # the Structural table in tasks.md


class RowReason(StrEnum): ...  # the Rows table in tasks.md


class CellFailure(BaseModel):  # returned by numbers.py and times.py, never raised
    reason: RowReason
    detail: str


class StructuralError(BaseModel):
    reason: StructuralReason
    message: str
    file_line: int | None = None


class MeaningQuestion(BaseModel):
    kind: QuestionKind
    message: str
    streams: tuple[str, ...] = ()


class RowError(BaseModel):
    reason: RowReason
    data_row: int
    file_line: int
    field: str
    message: str


class RowResult(BaseModel):
    data_row: int
    file_line: int
    status: RowStatus
    error: RowError | None = None
    asset_name: str | None = None
    stream_key: str | None = None
    kind: ValueKind | None = None
    unit: str | None = None
    value_milli: int | None = None
    interval_start: datetime | None = None
    interval_end: datetime | None = None  # UTC when set
    interval_basis: IntervalBasis | None = None
    measured_at: datetime | None = None  # UTC when set
    raw_value: str | None = None
    raw_start: str | None = None
    raw_end: str | None = None
    # property value -> Decimal | None: value_milli as a Decimal with exactly three places


class MeaningAnswers(BaseModel):
    value_kind: ValueKind | None = None
    power_meaning: PowerMeaning | None = None
    timezone_confirmed: bool = False
    interval_minutes: dict[str, int] = {}  # by stream key


class ParsedFile(BaseModel):
    structural_errors: list[StructuralError]
    questions: list[MeaningQuestion]
    site_timezone: str
    answers: MeaningAnswers
    delimiter: str | None
    had_bom: bool
    header_line: int | None
    headers: list[str]
    ignored_columns: list[str]
    value_kinds: list[ValueKind]
    total_rows: int
    blank_lines: int
    asset_names: list[str]
    has_naive_timestamps: bool
    cadences: dict[str, timedelta | None]  # timestamp-only streams, by stream key
    # property ok -> bool: no structural errors


# app/imports/service/parser.py
def parse(source: BinaryIO, *, site_timezone: str, answers: MeaningAnswers = MeaningAnswers()) -> ParsedFile: ...
def iter_rows(source: BinaryIO, parsed: ParsedFile) -> Iterator[RowResult]: ...  # yields nothing on structural errors
```

`source` is a seekable binary file. Both functions seek to 0 and leave it open. `site_timezone` is an IANA name the caller has validated, passed as plain text so no M1 type enters here.

## Design

**Reading.** Check the size with `seek` before decoding. Decode with `io.TextIOWrapper(source, encoding="utf-8-sig", newline="")` and detach it in a `finally`, so the caller's file stays open. A decode failure or a NUL character is a structural error. Do not use `csv.Sniffer`. Detect the delimiter from the first nonblank line outside quotes, as the prototype does. Tokenize with `csv.reader(lines, delimiter=delimiter, strict=True)`, so quoting matches the standard and an unterminated quote fails instead of swallowing the rest of the file. Do not call `csv.field_size_limit`, which is process-wide. A record's file line is the previous `reader.line_num + 1`, because `line_num` is the record's last physical line.

**Streaming.** `csv.reader` reads line by line, but a row's interval end depends on a cadence that needs every timestamp of its stream. So `parse` makes one pass that keeps only per-stream timestamps, names and counts, and `iter_rows` makes a second pass that yields one row at a time and keeps nothing.

**Numbers.** Validate the shape with `[0-9]` patterns and `fullmatch`, then build integer milli-units from the digits, three places maximum. No float enters, and neither does `Decimal` arithmetic, which rounds to its context. `Decimal` is the output type only: `RowResult.value` has exactly three places, so `10`, `10.0` and `10,000` reach 006 as one value. The parser never converts watts to energy: 006 does.

**Times.** Validate the shape with the prototype's pattern and build `datetime(...)` from its groups. Do not use `datetime.fromisoformat`, which reads `08.30` as 08:00:00.3. Normalize to UTC at once, because arithmetic between datetimes sharing a `ZoneInfo` is wall-clock. Resolve confirmed local timestamps with `zoneinfo`, which never raises on a gap, so compare the offsets of fold 0 and fold 1 and round-trip through UTC. Require an offset or correction for ambiguous or nonexistent local times.

**Cadence.** Cadence uses the positive gaps between sorted distinct timestamps per stream, in integer microseconds. Use the median only when at least 90% of those gaps are within one second of it. Confirm inferred durations in preview, or require a declared duration or explicit start/end when inference fails. A declared duration belongs to one stream. Convert timestamp-only interval rows to `[timestamp, timestamp + duration)`, including the final row, and keep counter points for the counter path. Validate explicit end after start. The preview in 025 classifies overlapping intervals after source identity is resolved.

**Meaning.** Every average-power alias waits for a confirmed meaning, and instantaneous power stays blocked. Competing value columns wait for a choice, and only the chosen column is read. Two headers with one role are a structural error, as is a timestamp column beside interval columns. Any naive time cell, including `interval_end`, asks for timezone confirmation.

## Errors

The parser returns failures as data and raises no `AppError`. `StructuralError`, `MeaningQuestion` and `RowError` carry stable snake_case reasons and exact Indonesian text, listed in `tasks.md`. It registers no code and logs nothing. `csv.Error` and `UnicodeDecodeError` are translated in `dialect.py`, and their text never reaches a message. An unexpected exception is a bug, so it propagates to the registered `APP-UNKNOWN` fallback. 025 is the boundary: it maps reasons to `APP-IMPORT-TOO-LARGE` and `APP-IMPORT-STRUCTURE`.

## Prototype Reference

`tokenize`, `detectDelimiter`, `parseDecimal`, `parseTime`, `parseCsv`, `inferCadence`, the meaning part of `mappingIssues` (L713–L720) and the row checks of `buildPreview` (L742–L767), where the spec's exact message lives. The rest of `buildPreview`, and `defaultMapping`, belong to 025. Tests AT-27a, AT-27b, AT-28, AT-29, AT-31, AT-32 and AT-30's first error message. `domain.test.js` has no AT-26 test, so AT-26 is written from the two CSV blocks in PRD §10.2.

## Test Plan

Port the tests above with the same messages. Assert AT-27a's 50 Wh and AT-27b's 30 Wh by feeding parser rows into 006's `normalize` and `counter_deltas`, in the test only. Add: mixed line endings, BOM before a quoted header, non-UTF-8 and NUL, unterminated quote, malformed quote, duplicate meaning columns, a timestamp beside interval columns, extra columns, blank-line numbering, quoted newline numbering, dotted times, offsets out of range, year overflow, a naive `interval_end`, nonexistent and ambiguous local times in a DST zone, two sources with different cadences, a declared duration on one stream, repeated timestamps excluded from the cadence denominator, irregular gaps, exactly 90% agreement, final-row interval, counter points, ambiguous numbers (`0.250`, `1.250`, `"1,250"`), non-ASCII digits and `NaN`, a 5,000-digit value, 60 and 61 character names and sources, 10 MiB boundary, 150,000 and 150,001 rows, lazy row delivery, peak memory, a boundary test on imports, no logging, performance run.

## Performance

Target: 150,000 rows within 10 MiB in under 60 seconds on the dev machine. Measured 2026-11-07 on an Apple M3 with 16 GiB, Darwin 27.2.0, Python 3.13.16, for `parse` plus a full `iter_rows`: 1.99 s for 150,000 explicit-offset rows (10,312,544 bytes), and 1.50 s for 150,000 confirmed naive rows over 40 streams (5,062,526 bytes). Peak `tracemalloc` was 0.04 MiB and 6.05 MiB in `parse`, and 0.04 MiB and 0.05 MiB in `iter_rows` with rows discarded. PRD §18's full validation and commit target is measured by 041.

## Out of Scope

Storage, duplicates against stored data (025), commit (026), screens (027). No route, migration, table or error code. No production import from `app.measurements`, `app.sites`, `app.assets` or `app.energy`.

## Task Outline

1. Port tests, failing.
2. Dialect and tokenizer.
3. Column aliases.
4. Numbers and times.
5. Cadence.
6. Assemble `parse()` and `iter_rows()`; performance note.
