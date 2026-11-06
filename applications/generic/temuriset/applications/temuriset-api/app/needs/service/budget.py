"""Budget rules (FR06, AC16, AC17). Every amount is parsed exactly; nothing passes through float."""

from decimal import Decimal

from app.capabilities.service.service import SUPPORTED_CURRENCIES
from app.core.types import money_text, parse_decimal
from app.needs.model.schema import BudgetInput, BudgetLineResponse, BudgetResponse

_BAD_NUMBER = "Isi dengan angka desimal, misalnya 20000 atau 20000.50."


def _error(field: str, message: str) -> dict:
    return {"loc": ["body", "budget", field], "msg": message, "type": "budget"}


def _amount(text: str | None, field: str, label: str, errors: list[dict]) -> Decimal | None:
    if text is None or text == "":
        return None
    value = parse_decimal(text)
    if value is None:
        errors.append(_error(field, _BAD_NUMBER))
    elif value < 0:
        errors.append(_error(field, f"{label} tidak boleh negatif."))
    return value


def validate_budget(budget: BudgetInput) -> tuple[list[dict], dict, list[dict]]:
    """Check a budget and compute its line totals.

    Args:
        budget (BudgetInput): The budget as sent.

    Returns:
        tuple[list[dict], dict, list[dict]]: Field errors, column values, and line rows; the last two are only
            meaningful when there are no errors.
    """
    errors: list[dict] = []
    low = _amount(budget.min, "min", "Biaya minimum", errors)
    high = _amount(budget.max, "max", "Biaya maksimum", errors)
    if (low is None) != (high is None) and not errors:
        errors.append(
            _error("max" if high is None else "min", "Isi biaya minimum dan maksimum, atau kosongkan keduanya.")
        )
    if low is None and high is None and budget.unknown_reason is None and not errors:
        errors.append(_error("unknown_reason", "Pilih alasan bila kisaran biaya belum diketahui."))
    if low is not None and high is not None and low >= 0 and high >= 0:
        if high < low:
            errors.append(_error("max", "Biaya maksimum tidak boleh lebih kecil dari biaya minimum."))
        if budget.financial and (low == 0 or high == 0):
            errors.append(_error("min", "Isi biaya lebih dari nol, atau tandai kebutuhan ini sebagai nonfinansial."))
        if budget.currency is None:
            errors.append(_error("currency", "Pilih mata uang."))
        elif budget.currency not in SUPPORTED_CURRENCIES:
            errors.append(_error("currency", "Mata uang ini belum didukung. Pilih IDR atau USD."))
    lines, total = [], Decimal(0)
    for index, line in enumerate(budget.lines):
        quantity = parse_decimal(line.quantity)
        unit_cost = parse_decimal(line.unit_cost)
        if quantity is None or unit_cost is None or quantity < 0 or unit_cost < 0:
            errors.append({"loc": ["body", "budget", "lines", index], "msg": _BAD_NUMBER, "type": "budget"})
            continue
        total += quantity * unit_cost
        lines.append(
            {
                "position": index,
                "label": line.label,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "explanation": line.explanation,
            }
        )
    if lines and low is not None and high is not None and not low <= total <= high and not budget.lines_explanation:
        errors.append(
            _error(
                "lines_explanation", "Jelaskan mengapa kisaran berbeda dari jumlah rincian, misalnya cakupan sebagian."
            )
        )
    values = {
        "min_amount": low,
        "max_amount": high,
        "currency": budget.currency if low is not None else None,
        "basis": budget.basis,
        "period": budget.period,
        "scope": budget.scope,
        "estimated_on": budget.estimated_on,
        "assumptions": budget.assumptions,
        "unknown_reason": budget.unknown_reason if low is None else None,
        "financial": budget.financial,
        "lines_explanation": budget.lines_explanation,
    }
    return errors, values, lines


def budget_response(record, lines) -> BudgetResponse:  # noqa: ANN001 - ORM rows of this module
    """Render a stored budget with exact line totals.

    Args:
        record: The budget row.
        lines: Its line rows.

    Returns:
        BudgetResponse: The budget.
    """
    rendered = [
        BudgetLineResponse(
            label=line.label,
            quantity=money_text(line.quantity) or "0",
            unit_cost=money_text(line.unit_cost) or "0",
            total=money_text(line.quantity * line.unit_cost) or "0",
            explanation=line.explanation,
        )
        for line in lines
    ]
    return BudgetResponse(
        min=money_text(record.min_amount),
        max=money_text(record.max_amount),
        currency=record.currency,
        basis=record.basis,
        period=record.period,
        scope=record.scope,
        estimated_on=record.estimated_on,
        assumptions=record.assumptions,
        unknown_reason=record.unknown_reason,
        financial=record.financial,
        lines=rendered,
        lines_total=money_text(sum((line.quantity * line.unit_cost for line in lines), Decimal(0))) if lines else None,
        lines_explanation=record.lines_explanation,
    )


def directly_comparable(
    first: BudgetResponse, second: BudgetResponse, first_months: int | None, second_months: int | None
) -> bool:
    """Whether two amounts may be compared at all (AC18): same currency and a confirmed equivalent basis.

    A monthly amount and a six-month total are never compared directly; matching (019) explains the gap instead.

    Args:
        first (BudgetResponse): One budget.
        second (BudgetResponse): The other.
        first_months (int | None): Months the first covers.
        second_months (int | None): Months the second covers.

    Returns:
        bool: True only for the same currency and basis, and the same months when both are period totals.
    """
    if first.currency is None or first.currency != second.currency or first.basis != second.basis:
        return False
    return first.basis != "total_period" or (first_months is not None and first_months == second_months)
