"""Value cells become exact integer milli-units, or a failure that says why. Port of ``parseDecimal`` (L613)."""

import pytest

from app.imports.model.models import CellFailure, RowReason
from app.imports.service.numbers import parse_decimal


@pytest.mark.parametrize(
    ("raw", "milli"),
    [
        ("10", 10000),
        ("12.5", 12500),
        ("0", 0),
        ("0.001", 1),
        ("00012", 12000),
        ("-1", -1000),
        ("-0", 0),
        ("12,5", 12500),
        ("12,50", 12500),
        ("0,250", 250),
        (" 10 ", 10000),
    ],
)
def test_comma_file_reads_exact_milli_units(raw: str, milli: int) -> None:
    """
    Condition:
    - A value in a comma file, where a cell holding a comma must have been quoted.

    Expected:
    - The exact integer milli-units.
    """
    assert parse_decimal(raw, ",") == milli


@pytest.mark.parametrize(
    ("raw", "milli"),
    [
        ("12,5", 12500),
        ("1.250,5", 1250500),
        ("1.250.000", 1250000000),
        ("1,250", 1250),
        ("12,500", 12500),
        ("-1.250,5", -1250500),
        ("10", 10000),
    ],
)
def test_semicolon_file_reads_exact_milli_units(raw: str, milli: int) -> None:
    """
    Condition:
    - A value in a semicolon file, where the comma is the decimal mark.

    Expected:
    - The exact integer milli-units, with dots read only as unambiguous thousands.
    """
    assert parse_decimal(raw, ";") == milli


@pytest.mark.parametrize("delimiter", [",", ";"])
@pytest.mark.parametrize("raw", ["", "   ", "\t"])
def test_blank_value_is_none(raw: str, delimiter: str) -> None:
    """
    Condition:
    - A blank or whitespace cell.

    Expected:
    - None, so the caller can report it and never reads it as zero.
    """
    assert parse_decimal(raw, delimiter) is None


@pytest.mark.parametrize("raw", ["12.5", "1.25", "0.250", "1.250"])
def test_dotted_value_in_semicolon_file_is_ambiguous(raw: str) -> None:
    """
    Condition:
    - A dotted value in a semicolon file with a single group and no decimal comma (D12).

    Expected:
    - ``value_ambiguous`` with an example, never a read that may be 1,000 times off.
    """
    assert parse_decimal(raw, ";") == CellFailure(
        reason=RowReason.VALUE_AMBIGUOUS,
        detail=f'angka "{raw}" ambigu pada berkas titik koma. Gunakan koma desimal, misalnya 12,5.',
    )


@pytest.mark.parametrize("raw", ["1,250", "12,500", "-1,250"])
def test_grouped_value_in_comma_file_is_ambiguous(raw: str) -> None:
    """
    Condition:
    - A quoted value in a comma file that reads equally as thousands or as decimals (D12).

    Expected:
    - ``value_ambiguous_comma`` with an example.
    """
    assert parse_decimal(raw, ",") == CellFailure(
        reason=RowReason.VALUE_AMBIGUOUS_COMMA,
        detail=(
            f'angka "{raw}" ambigu pada berkas koma. Gunakan titik desimal, misalnya 1.25, '
            "atau tulis tanpa pemisah ribuan, misalnya 1250."
        ),
    )


@pytest.mark.parametrize(
    ("raw", "delimiter"),
    [
        ("1,250.5", ","),
        ("1.250,5", ","),
        ("12.345.6", ";"),
        ("+5", ","),
        (".5", ","),
        ("5.", ","),
        ("1e5", ","),
        ("NaN", ","),
        ("Infinity", ","),
        ("sNaN", ","),
        ("1_000", ","),
        ("١٢", ","),
        ("0x10", ","),
        ("dua", ","),
        ("+5", ";"),
        ("1e5", ";"),
        ("NaN", ";"),
        ("١٢", ";"),
        ("dua", ";"),
    ],
)
def test_non_number_is_rejected(raw: str, delimiter: str) -> None:
    """
    Condition:
    - Text that ``Decimal`` or ``int`` might accept, or that is no number at all.

    Expected:
    - ``value_not_number`` naming the cell.
    """
    assert parse_decimal(raw, delimiter) == CellFailure(
        reason=RowReason.VALUE_NOT_NUMBER, detail=f'"{raw}" bukan angka.'
    )


@pytest.mark.parametrize(
    ("raw", "delimiter"), [("1.2345", ","), ("1.0000", ","), ("1,2345", ","), ("1,2345", ";"), ("1.250,1234", ";")]
)
def test_more_than_three_places_is_rejected_not_rounded(raw: str, delimiter: str) -> None:
    """
    Condition:
    - More than three decimals, even when the extra digits are zeros (FR-004).

    Expected:
    - ``value_too_precise``, never a rounded value.
    """
    assert parse_decimal(raw, delimiter) == CellFailure(
        reason=RowReason.VALUE_TOO_PRECISE, detail="gunakan paling banyak 3 angka desimal."
    )


def test_largest_storable_value_stays_exact() -> None:
    """
    Condition:
    - The value whose milli-units equal ``2**63 - 1``, beyond JavaScript's exact range.

    Expected:
    - Every digit survives.
    """
    assert parse_decimal("9223372036854775.807", ",") == 2**63 - 1


@pytest.mark.parametrize("raw", ["9223372036854775.808", "-9223372036854775.808", "9" * 400, "1" * 5000])
def test_value_beyond_the_bound_is_rejected_without_an_exception(raw: str) -> None:
    """
    Condition:
    - A value above the BIGINT bound, including text longer than ``int()`` accepts.

    Expected:
    - ``value_too_large`` is returned, and nothing is raised.
    """
    assert parse_decimal(raw, ",") == CellFailure(
        reason=RowReason.VALUE_TOO_LARGE, detail=f'angka "{raw}" terlalu besar. Periksa nilai dan satuannya.'
    )


def test_leading_zeros_do_not_count_toward_the_digit_guard() -> None:
    """
    Condition:
    - 5,000 leading zeros before a small value.

    Expected:
    - The value reads normally, without reaching ``int()``'s digit limit.
    """
    assert parse_decimal("0" * 5000 + "1", ",") == 1000
