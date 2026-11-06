"""Conservative fit bounds (PRD section 10): unknown features widen the upper bound only."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# Policy ``matching-weights`` version 1.
WEIGHTS_A = {
    "problem": Decimal("0.45"),
    "stage": Decimal("0.15"),
    "sector": Decimal("0.15"),
    "financial": Decimal("0.15"),
    "timing": Decimal("0.10"),
}
WEIGHTS_B = {
    "support": Decimal("0.40"),
    "form": Decimal("0.30"),
    "geo": Decimal("0.15"),
    "availability": Decimal("0.15"),
}
# Policy ``fit-thresholds`` version 1.
STRONG_LOWER, STRONG_COVERAGE = Decimal(70), Decimal("0.70")
POTENTIAL_LOWER, POTENTIAL_COVERAGE = Decimal(50), Decimal("0.50")
MIN_COVERAGE = Decimal("0.40")

_HUNDREDTH = Decimal("0.01")


def half_up(value: Decimal) -> Decimal:
    """Round to two places, halves away from zero, as the prototype's ``Math.round`` does for these values.

    Args:
        value (Decimal): The value.

    Returns:
        Decimal: Rounded.
    """
    return value.quantize(_HUNDREDTH, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Side:
    """One direction of fit.

    Attributes:
        low (Decimal): Score counting unknown features as zero.
        high (Decimal): Score counting unknown features as one.
        known (Decimal): Share of weight that is known.
    """

    low: Decimal
    high: Decimal
    known: Decimal


def side(features: dict[str, Decimal | None], weights: dict[str, Decimal]) -> Side:
    """Score one direction.

    Args:
        features (dict[str, Decimal | None]): Feature values from 0 to 1, or None when unknown.
        weights (dict[str, Decimal]): Weights that sum to 1.

    Returns:
        Side: The bounds.
    """
    low = sum((weights[key] * value for key, value in features.items() if value is not None), Decimal(0))
    unknown = sum((weights[key] for key, value in features.items() if value is None), Decimal(0))
    return Side(low=low, high=low + unknown, known=Decimal(1) - unknown)


def harmonic(first: Decimal, second: Decimal) -> Decimal:
    """Harmonic mean, so a weak side cannot be hidden by a strong one.

    Args:
        first (Decimal): One side.
        second (Decimal): The other.

    Returns:
        Decimal: The mean, or 0 when both are 0.
    """
    total = first + second
    return Decimal(0) if total == 0 else 2 * first * second / total


@dataclass(frozen=True)
class FitBounds:
    """Fit as a range on 0–100 and the share of information it rests on.

    Attributes:
        lower (Decimal): Lower bound.
        upper (Decimal): Upper bound.
        coverage (Decimal): Known share, 0–1.
    """

    lower: Decimal
    upper: Decimal
    coverage: Decimal


def fit_bounds(a: Side, b: Side) -> FitBounds:
    """Combine both directions.

    Args:
        a (Side): Direction A, the need against the mandate.
        b (Side): Direction B, the mandate against the need.

    Returns:
        FitBounds: Bounds and coverage.
    """
    return FitBounds(
        lower=half_up(100 * harmonic(a.low, b.low)),
        upper=half_up(100 * harmonic(a.high, b.high)),
        coverage=half_up((a.known + b.known) / 2),
    )


def relevance(source_keywords: tuple[str, ...], target_keywords: tuple[str, ...]) -> Decimal:
    """Share of the target's keywords the source also states. Zero means no relevance signal.

    Args:
        source_keywords (tuple[str, ...]): The applicant's published keywords.
        target_keywords (tuple[str, ...]): The opportunity's keywords.

    Returns:
        Decimal: Overlap from 0 to 1, rounded to two places.
    """
    wanted = {word.casefold() for word in target_keywords}
    if not wanted:
        return Decimal(0)
    stated = {word.casefold() for word in source_keywords}
    return half_up(Decimal(len(wanted & stated)) / Decimal(len(wanted)))
