"""The parser's contract types and their vocabulary against merged 006."""

from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from app.assets.model.models import MeasurementKind
from app.imports.model.models import (
    MeaningAnswers,
    MeaningQuestion,
    ParsedFile,
    QuestionKind,
    RowResult,
    RowStatus,
    StructuralError,
    StructuralReason,
    ValueKind,
)
from app.measurements.service.normalize import MILLIWATT_PER_UNIT, MWH_PER_UNIT


def _row(value_milli: int | None) -> RowResult:
    return RowResult(data_row=1, file_line=2, status=RowStatus.PARSED, value_milli=value_milli)


def _parsed(errors: list[StructuralError]) -> ParsedFile:
    return ParsedFile(
        structural_errors=errors,
        questions=[],
        site_timezone="Asia/Jakarta",
        answers=MeaningAnswers(),
        delimiter=",",
        had_bom=False,
        header_line=1,
        headers=[],
        ignored_columns=[],
        value_kinds=[],
        total_rows=0,
        blank_lines=0,
        asset_names=[],
        has_naive_timestamps=False,
        cadences={},
    )


@pytest.mark.parametrize(
    ("value_milli", "canonical"),
    [(10000, "10.000"), (12500, "12.500"), (0, "0.000"), (1, "0.001"), (9223372036854775807, "9223372036854775.807")],
)
def test_row_value_has_exactly_three_places(value_milli: int, canonical: str) -> None:
    """
    Condition:
    - A row holding an exact integer of milli-units.

    Expected:
    - ``value`` is the same number as a Decimal with three places, so 006 sees one canonical text.
    """
    value = _row(value_milli).value
    assert value == Decimal(canonical)
    assert format(value, "f") == canonical


def test_row_value_ignores_the_decimal_context() -> None:
    """
    Condition:
    - The largest value, read under a Decimal context of two digits.

    Expected:
    - The value is still exact: it does not depend on process-wide Decimal settings.
    """
    with localcontext(prec=2):
        assert format(_row(9223372036854775807).value, "f") == "9223372036854775.807"


def test_row_value_is_none_without_a_value() -> None:
    """
    Condition:
    - A row with no value.

    Expected:
    - ``value`` is None rather than zero.
    """
    assert _row(None).value is None


@pytest.mark.parametrize(
    ("instance", "field", "new"),
    [
        (_row(1), "value_milli", 2),
        (MeaningAnswers(), "timezone_confirmed", True),
        (StructuralError(reason=StructuralReason.EMPTY_INPUT, message="m"), "message", "x"),
        (MeaningQuestion(kind=QuestionKind.TIMEZONE, message="m"), "message", "x"),
        (_parsed([]), "total_rows", 1),
    ],
)
def test_models_are_frozen(instance: object, field: str, new: object) -> None:
    """
    Condition:
    - Any contract model after construction.

    Expected:
    - Assignment is refused, so a parsed result cannot drift from the file it describes.
    """
    with pytest.raises(ValidationError, match="frozen"):
        setattr(instance, field, new)


def test_parsed_file_ok_means_no_structural_errors() -> None:
    """
    Condition:
    - One file with no structural error and one with an error.

    Expected:
    - ``ok`` follows the structural errors alone.
    """
    assert _parsed([]).ok is True
    assert _parsed([StructuralError(reason=StructuralReason.EMPTY_INPUT, message="m")]).ok is False


def test_answers_do_not_share_their_default_durations() -> None:
    """
    Condition:
    - Two default answers.

    Expected:
    - Each has its own empty duration mapping.
    """
    first, second = MeaningAnswers(), MeaningAnswers()
    first.interval_minutes["a"] = 60
    assert second.interval_minutes == {}


@pytest.mark.parametrize("kind", list(ValueKind))
def test_value_kinds_match_merged_measurement_kinds(kind: ValueKind) -> None:
    """
    Condition:
    - Every parser value kind.

    Expected:
    - It is also a MeasurementKind value, so 025 needs no translation table.
    """
    assert MeasurementKind(kind.value).value == kind.value


def test_units_match_merged_normalization() -> None:
    """
    Condition:
    - The two units the parser emits.

    Expected:
    - 006's case-sensitive conversion tables hold them.
    """
    assert "Wh" in MWH_PER_UNIT
    assert "W" in MILLIWATT_PER_UNIT
