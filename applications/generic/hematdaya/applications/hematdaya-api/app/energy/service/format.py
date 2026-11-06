"""Wire formatting: decimal strings, rounded once at the response."""

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal


def kwh(mwh: int) -> str:
    """Format integer mWh as kWh with three decimals.

    Args:
        mwh (int): Energy.

    Returns:
        str: For example ``"14.700"``.
    """
    return str((Decimal(mwh) / Decimal(1_000_000)).quantize(Decimal("0.001"), rounding=ROUND_HALF_EVEN))


def ratio(value: float) -> str:
    """Format a coverage ratio, rounded down so partial coverage never reads as complete.

    Args:
        value (float): Ratio between 0 and 1.

    Returns:
        str: For example ``"0.999"``.
    """
    return str(Decimal(repr(value)).quantize(Decimal("0.001"), rounding=ROUND_DOWN))


def percent(part: int, whole: int) -> str:
    """Format a share of a positive total with two decimals.

    Args:
        part (int): The asset's mWh.
        whole (int): The total mWh, greater than zero.

    Returns:
        str: For example ``"57.14"``.
    """
    return str((Decimal(part) * 100 / Decimal(whole)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
