"""What a partner's amounts mean (D13). Every amount is parsed exactly; nothing passes through float."""

from decimal import Decimal
from typing import Any

from app.capabilities.service.service import SUPPORTED_CURRENCIES
from app.core.types import money_text, parse_decimal
from app.intake.model.schema import FinancialInput, RangeInput

_BAD_NUMBER = "Isi dengan angka desimal, misalnya 20000 atau 20000.50."


def _error(loc: list[str], field: str, message: str) -> dict:
    return {"loc": [*loc, field], "msg": message, "type": "financial"}


def _amount(text: str | None, loc: list[str], field: str, errors: list[dict]) -> Decimal | None:
    if text is None or text == "":
        return None
    value = parse_decimal(text)
    if value is None:
        errors.append(_error(loc, field, _BAD_NUMBER))
    elif value < 0:
        errors.append(_error(loc, field, "Jumlah tidak boleh negatif."))
    return value


def _check_meaning(value: RangeInput, loc: list[str], errors: list[dict]) -> None:
    if value.currency is None:
        errors.append(_error(loc, "currency", "Pilih mata uang."))
    elif value.currency not in SUPPORTED_CURRENCIES:
        errors.append(_error(loc, "currency", "Mata uang ini belum didukung. Pilih IDR atau USD."))
    if value.basis is None:
        errors.append(_error(loc, "basis", "Pilih dasar jumlah ini."))
    if not value.period:
        errors.append(_error(loc, "period", "Isi periode yang dicakup jumlah ini."))
    if value.basis == "total_period" and value.months is None:
        errors.append(_error(loc, "months", "Isi jumlah bulan yang dicakup."))
    if value.basis != "total_period" and value.months is not None:
        errors.append(_error(loc, "months", "Jumlah bulan hanya untuk total satu periode."))


def validate_range(value: RangeInput, loc: list[str]) -> tuple[list[dict], dict[str, Any]]:
    """Check that a range is valid and says what it means.

    Args:
        value (RangeInput): The range as sent.
        loc (list[str]): Where it sits in the request, for field errors.

    Returns:
        tuple[list[dict], dict[str, Any]]: Field errors, and the values with exact amounts; the values are only
            meaningful when there are no errors.
    """
    errors: list[dict] = []
    low = _amount(value.min, loc, "min", errors)
    high = _amount(value.max, loc, "max", errors)
    if not errors and (low is None) != (high is None):
        errors.append(
            _error(loc, "max" if high is None else "min", "Isi jumlah minimum dan maksimum, atau kosongkan keduanya.")
        )
    if low is not None and high is not None:
        if not errors and high < low:
            errors.append(_error(loc, "max", "Jumlah maksimum tidak boleh lebih kecil dari jumlah minimum."))
        _check_meaning(value, loc, errors)
    known = low is not None and high is not None
    values = {
        "subject": value.subject,
        "basis": value.basis if known else None,
        "min": low,
        "max": high,
        "currency": value.currency if known else None,
        "period": value.period if known else "",
        "months": value.months if known else None,
        "unknown_reason": None if known else value.unknown_reason,
    }
    return errors, values


def validate_check_range(value: RangeInput, loc: list[str]) -> tuple[list[dict], dict[str, Any]]:
    """Check a profile's range: amounts, or an explained unknown.

    Args:
        value (RangeInput): The range as sent.
        loc (list[str]): Where it sits in the request.

    Returns:
        tuple[list[dict], dict[str, Any]]: Field errors and the values.
    """
    errors, values = validate_range(value, loc)
    if not errors and values["min"] is None and values["unknown_reason"] is None:
        errors.append(_error(loc, "unknown_reason", "Pilih alasan bila kisaran belum diketahui."))
    return errors, values


def validate_financial(value: FinancialInput) -> tuple[list[dict], dict[str, Any]]:
    """Check an opportunity's financial basis: a range, non-cash support, license terms, or an explained unknown.

    Args:
        value (FinancialInput): The basis as sent.

    Returns:
        tuple[list[dict], dict[str, Any]]: Field errors, and the JSON to store, with amounts as decimal strings.
    """
    loc = ["body", "financial"]
    errors, values = validate_range(value, loc)
    if not errors and values["min"] is None and not (value.noncash or value.terms or values["unknown_reason"]):
        errors.append(
            _error(loc, "unknown_reason", "Isi kisaran, dukungan nontunai atau ketentuan, atau pilih alasan.")
        )
    return errors, {
        **values,
        "min": money_text(values["min"]) if not errors else None,
        "max": money_text(values["max"]) if not errors else None,
        "scope": value.scope,
        "noncash": value.noncash,
        "terms": value.terms,
    }
