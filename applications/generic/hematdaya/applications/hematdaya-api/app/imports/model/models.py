"""The CSV parser's contract: what it returns, and the answers it needs. Failures are data here, never raised."""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ValueKind(StrEnum):
    """What a file's values mean, in merged 006's words."""

    INTERVAL_ENERGY = "interval_energy"
    AVERAGE_POWER = "average_power"
    COUNTER = "counter"


class PowerMeaning(StrEnum):
    """What the user says a power column means."""

    AVERAGE = "average"
    INSTANTANEOUS = "instantaneous"


class QuestionKind(StrEnum):
    """What the parser must ask before a row can be read."""

    VALUE_KIND = "value_kind"
    POWER_MEANING = "power_meaning"
    TIMEZONE = "timezone"
    INTERVAL_DURATION = "interval_duration"


class RowStatus(StrEnum):
    """Where one row stands."""

    PARSED = "parsed"
    INVALID = "invalid"
    PENDING = "pending"


class IntervalBasis(StrEnum):
    """Where a row's interval end came from."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    DECLARED = "declared"


class StructuralReason(StrEnum):
    """Why a whole file cannot be read."""

    EMPTY_INPUT = "empty_input"
    TOO_LARGE = "too_large"
    NOT_UTF8 = "not_utf8"
    DELIMITER_AMBIGUOUS = "delimiter_ambiguous"
    SINGLE_COLUMN = "single_column"
    QUOTE_UNCLOSED = "quote_unclosed"
    QUOTE_MALFORMED = "quote_malformed"
    DUPLICATE_ROLE = "duplicate_role"
    COMPETING_TIME_COLUMNS = "competing_time_columns"
    MISSING_ASSET = "missing_asset"
    MISSING_TIME = "missing_time"
    MISSING_VALUE = "missing_value"
    COUNTER_NEEDS_TIMESTAMP = "counter_needs_timestamp"
    TOO_MANY_ROWS = "too_many_rows"
    NO_DATA_ROWS = "no_data_rows"


class RowReason(StrEnum):
    """Why one row cannot be read."""

    COLUMN_COUNT = "column_count"
    ASSET_EMPTY = "asset_empty"
    ASSET_TOO_LONG = "asset_too_long"
    SOURCE_TOO_LONG = "source_too_long"
    TIME_FORMAT = "time_format"
    TIME_IMPOSSIBLE = "time_impossible"
    TIME_NONEXISTENT = "time_nonexistent"
    TIME_AMBIGUOUS = "time_ambiguous"
    INTERVAL_REVERSED = "interval_reversed"
    VALUE_EMPTY = "value_empty"
    VALUE_AMBIGUOUS = "value_ambiguous"
    VALUE_AMBIGUOUS_COMMA = "value_ambiguous_comma"
    VALUE_NOT_NUMBER = "value_not_number"
    VALUE_TOO_PRECISE = "value_too_precise"
    VALUE_TOO_LARGE = "value_too_large"
    NEGATIVE = "negative"


class _Frozen(BaseModel):
    """A value that cannot change after construction."""

    model_config = ConfigDict(frozen=True)


class CellFailure(_Frozen):
    """Why one cell cannot be read. Returned by the cell parsers, never raised.

    Attributes:
        reason (RowReason): Stable reason.
        detail (str): The correction, without the row and field prefix.
    """

    reason: RowReason
    detail: str


class StructuralError(_Frozen):
    """A failure of the whole file.

    Attributes:
        reason (StructuralReason): Stable reason.
        message (str): What happened and what to do next.
        file_line (int | None): The file line it starts on, when one applies.
    """

    reason: StructuralReason
    message: str
    file_line: int | None = None


class MeaningQuestion(_Frozen):
    """Something only the user can answer. It blocks commit but is not an error in the file.

    Attributes:
        kind (QuestionKind): What is being asked.
        message (str): The question.
        streams (tuple[str, ...]): The stream keys it concerns, when it concerns only some.
    """

    kind: QuestionKind
    message: str
    streams: tuple[str, ...] = ()


class RowError(_Frozen):
    """A failure of one row. An expected result, so it has no reference ID.

    Attributes:
        reason (RowReason): Stable reason.
        data_row (int): Nonblank data row, from 1.
        file_line (int): File line the record starts on, from 1.
        field (str): The header as written, or ``baris`` for a column count mismatch.
        message (str): The full message, with row and field.
    """

    reason: RowReason
    data_row: int
    file_line: int
    field: str
    message: str


class RowResult(_Frozen):
    """One row as read. Times are UTC when set.

    Attributes:
        data_row (int): Nonblank data row, from 1.
        file_line (int): File line the record starts on, from 1.
        status (RowStatus): Parsed, invalid, or pending an answer.
        error (RowError | None): The failure of an invalid row.
        asset_name (str | None): The name, stripped and otherwise verbatim.
        stream_key (str | None): The source cell or asset name, stripped and lower-cased.
        kind (ValueKind | None): What the value means, once known.
        unit (str | None): ``Wh`` or ``W``.
        value_milli (int | None): The exact value in thousandths of the unit.
        interval_start (datetime | None): Interval start, inclusive.
        interval_end (datetime | None): Interval end, exclusive.
        interval_basis (IntervalBasis | None): Where the end came from.
        measured_at (datetime | None): Capture time of a counter reading.
        raw_value (str | None): The value cell as written.
        raw_start (str | None): The timestamp or interval start cell as written.
        raw_end (str | None): The interval end cell as written.
        value (Decimal | None): ``value_milli`` as a Decimal with exactly three places.
    """

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
    interval_end: datetime | None = None
    interval_basis: IntervalBasis | None = None
    measured_at: datetime | None = None
    raw_value: str | None = None
    raw_start: str | None = None
    raw_end: str | None = None

    @property
    def value(self) -> Decimal | None:
        """The value with exactly three places, built from text so no Decimal context can round it."""
        return None if self.value_milli is None else Decimal(f"{self.value_milli}E-3")


class MeaningAnswers(_Frozen):
    """The user's answers to the parser's questions.

    Attributes:
        value_kind (ValueKind | None): The chosen value column's kind.
        power_meaning (PowerMeaning | None): What a power column means.
        timezone_confirmed (bool): Whether naive times may be read in the site's timezone.
        interval_minutes (dict[str, int]): Declared duration in minutes, by stream key.
    """

    value_kind: ValueKind | None = None
    power_meaning: PowerMeaning | None = None
    timezone_confirmed: bool = False
    interval_minutes: dict[str, int] = Field(default_factory=dict)


class ParsedFile(_Frozen):
    """The file-level answers of one parse.

    Attributes:
        structural_errors (list[StructuralError]): Why the whole file cannot be read.
        questions (list[MeaningQuestion]): What must be answered first.
        site_timezone (str): IANA name naive times are read in, once confirmed.
        answers (MeaningAnswers): The answers this parse used.
        delimiter (str | None): The column separator, when detected.
        had_bom (bool): Whether the file started with a UTF-8 BOM.
        header_line (int | None): File line of the header.
        headers (list[str]): Headers as written, stripped.
        ignored_columns (list[str]): Headers with no meaning here.
        value_kinds (list[ValueKind]): Value roles present.
        total_rows (int): Nonblank data rows.
        blank_lines (int): Blank records, wherever they are.
        asset_names (list[str]): Names in first-seen order.
        has_naive_timestamps (bool): Whether any time cell has no offset.
        cadences (dict[str, timedelta | None]): Cadence of each timestamp-only stream, by stream key.
        ok (bool): Whether the file has no structural error.
    """

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
    cadences: dict[str, timedelta | None]

    @property
    def ok(self) -> bool:
        """Whether the file has no structural error."""
        return not self.structural_errors
