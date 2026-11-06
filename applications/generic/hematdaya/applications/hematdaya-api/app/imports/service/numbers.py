"""Reads a value cell as exact integer milli-units, with no float and no Decimal arithmetic."""

import re

from app.imports.model.models import CellFailure, RowReason

MAX_MILLI = 2**63 - 1
"""``measurements.energy_mwh`` is a BIGINT, and 006 stores this number as mWh for a value in Wh."""
_MAX_INTEGER_DIGITS = 16
"""Guards ``int()``, which raises above 4,300 digits. ``MAX_MILLI`` has 16 integer digits as a value."""
_MAX_DECIMALS = 3

_SEMICOLON_GROUPED = re.compile(r"-?[1-9][0-9]{0,2}(\.[0-9]{3})+(,[0-9]+)?")
_SEMICOLON_PLAIN = re.compile(r"-?[0-9]+(,[0-9]+)?")
_SEMICOLON_DOTTED = re.compile(r"-?[0-9]+\.[0-9]+")
_COMMA_GROUPED = re.compile(r"-?[1-9][0-9]{0,2},[0-9]{3}")
_COMMA_DECIMAL = re.compile(r"-?[0-9]+,[0-9]+")
_COMMA_PLAIN = re.compile(r"-?[0-9]+(\.[0-9]+)?")


def _not_a_number(text: str) -> CellFailure:
    return CellFailure(reason=RowReason.VALUE_NOT_NUMBER, detail=f'"{text}" bukan angka.')


def _canonical_in_semicolon_file(text: str) -> str | CellFailure:
    # One dotted group with no decimal comma is left to fall through: 1.250 may mean 1,250 or 1.25.
    if _SEMICOLON_GROUPED.fullmatch(text) and ("," in text or text.count(".") >= 2):
        return text.replace(".", "").replace(",", ".")
    if _SEMICOLON_PLAIN.fullmatch(text):
        return text.replace(",", ".")
    if _SEMICOLON_DOTTED.fullmatch(text):
        return CellFailure(
            reason=RowReason.VALUE_AMBIGUOUS,
            detail=f'angka "{text}" ambigu pada berkas titik koma. Gunakan koma desimal, misalnya 12,5.',
        )
    return _not_a_number(text)


def _canonical_in_comma_file(text: str) -> str | CellFailure:
    if _COMMA_GROUPED.fullmatch(text):
        return CellFailure(
            reason=RowReason.VALUE_AMBIGUOUS_COMMA,
            detail=(
                f'angka "{text}" ambigu pada berkas koma. Gunakan titik desimal, misalnya 1.25, '
                "atau tulis tanpa pemisah ribuan, misalnya 1250."
            ),
        )
    if _COMMA_DECIMAL.fullmatch(text):
        return text.replace(",", ".")
    if _COMMA_PLAIN.fullmatch(text):
        return text
    return _not_a_number(text)


def parse_decimal(raw: str, delimiter: str) -> int | CellFailure | None:
    """Read a value cell as exact integer milli-units.

    Args:
        raw (str): The cell as written.
        delimiter (str): The file's column separator, which decides what a comma or a dot means.

    Returns:
        int | CellFailure | None: Milli-units, possibly negative; a failure saying why; None for a blank cell.
    """
    text = raw.strip()
    if not text:
        return None
    canonical = _canonical_in_semicolon_file(text) if delimiter == ";" else _canonical_in_comma_file(text)
    if isinstance(canonical, CellFailure):
        return canonical
    integer, _, fraction = canonical.removeprefix("-").partition(".")
    if len(fraction) > _MAX_DECIMALS:
        return CellFailure(reason=RowReason.VALUE_TOO_PRECISE, detail="gunakan paling banyak 3 angka desimal.")
    integer = integer.lstrip("0")
    too_large = CellFailure(
        reason=RowReason.VALUE_TOO_LARGE, detail=f'angka "{text}" terlalu besar. Periksa nilai dan satuannya.'
    )
    if len(integer) > _MAX_INTEGER_DIGITS:
        return too_large
    milli = int(integer or "0") * 1000 + int(fraction.ljust(_MAX_DECIMALS, "0"))
    if milli > MAX_MILLI:
        return too_large
    return -milli if canonical.startswith("-") else milli
