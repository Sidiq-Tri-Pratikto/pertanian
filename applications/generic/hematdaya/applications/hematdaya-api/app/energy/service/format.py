"""Wire formatting: decimal strings, rounded once at the response."""

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from fractions import Fraction


def kwh(mwh: int | Fraction) -> str:
    """Format exact mWh as kWh with three decimals, rounding once, ties to even.

    Args:
        mwh (int | Fraction): Energy; a Fraction keeps exact medians until here.

    Returns:
        str: For example ``"14.700"`` or ``"-1.400"``.
    """
    wh = round(Fraction(mwh) / 1000)  # Fraction rounds half to even.
    return str((Decimal(wh) / Decimal(1000)).quantize(Decimal("0.001"), rounding=ROUND_HALF_EVEN))


def ratio(value: float | Fraction) -> str:
    """Format a coverage ratio, rounded down so partial coverage never reads as complete.

    Args:
        value (float | Fraction): Ratio between 0 and 1.

    Returns:
        str: For example ``"0.999"``.
    """
    exact = Fraction(value) if isinstance(value, Fraction) else Fraction(repr(value))
    return str((Decimal(exact.numerator) / Decimal(exact.denominator)).quantize(Decimal("0.001"), rounding=ROUND_DOWN))


def percent(part: int | Fraction, whole: int | Fraction) -> str:
    """Format part as a percent of a positive whole with two decimals.

    Args:
        part (int | Fraction): The part, possibly negative.
        whole (int | Fraction): The whole, greater than zero.

    Returns:
        str: For example ``"57.14"`` or ``"55.56"``.
    """
    exact = Fraction(part) * 100 / Fraction(whole)
    value = Decimal(exact.numerator) / Decimal(exact.denominator)
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
