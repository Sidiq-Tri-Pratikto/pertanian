"""Budget rules without a database."""

from decimal import Decimal
from types import SimpleNamespace

from app.needs.model.schema import BudgetInput
from app.needs.service.budget import budget_response, directly_comparable, validate_budget


def _response(currency: str | None, basis: str):
    record = SimpleNamespace(
        min_amount=Decimal(1000),
        max_amount=Decimal(2000),
        currency=currency,
        basis=basis,
        period="",
        scope="",
        estimated_on=None,
        assumptions="",
        unknown_reason=None,
        financial=True,
        lines_explanation="",
    )
    return budget_response(record, [])


def test_monthly_and_period_totals_are_never_compared_directly() -> None:
    """
    Condition:
    - One monthly amount and one six-month total in the same currency (AC18), plus other pairs.

    Expected:
    - Only the same currency, same basis and, for period totals, the same months compare directly.
    """
    monthly, total = _response("USD", "monthly"), _response("USD", "total_period")

    assert directly_comparable(monthly, total, None, 6) is False
    assert directly_comparable(total, total, 6, 6) is True
    assert directly_comparable(total, total, 6, 12) is False
    assert directly_comparable(monthly, _response("USD", "monthly"), None, None) is True
    assert directly_comparable(monthly, _response("IDR", "monthly"), None, None) is False


def test_half_a_range_is_refused() -> None:
    """
    Condition:
    - Only a maximum is given.

    Expected:
    - Both or neither.
    """
    errors, _, _ = validate_budget(BudgetInput(max="100", currency="IDR"))

    assert errors[0]["msg"] == "Isi biaya minimum dan maksimum, atau kosongkan keduanya."


def test_a_bad_line_names_its_row() -> None:
    """
    Condition:
    - A line with a negative quantity.

    Expected:
    - The error points at that line.
    """
    errors, _, _ = validate_budget(
        BudgetInput(min="1", max="2", currency="IDR", lines=[{"label": "x", "quantity": "-1", "unit_cost": "1"}])
    )

    assert errors == [
        {
            "loc": ["body", "budget", "lines", 0],
            "msg": "Isi dengan angka desimal, misalnya 20000 atau 20000.50.",
            "type": "budget",
        }
    ]
