"""Conservative fit bounds (PRD section 10): unknown features widen the upper bound only."""

import re
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


_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _norm_words(text: str) -> list[str]:
    return _WORD_RE.findall(text.casefold())


def extract_terms(keywords: tuple[str, ...], *texts: str) -> tuple[str, ...]:
    """Build casefolded whole-word terms (plus whole multi-word keywords) from product keywords and prose.

    Args:
        keywords (tuple[str, ...]): Stated keywords.
        *texts (str): Product prose fields (title, summary, problem, solution).

    Returns:
        tuple[str, ...]: Deduplicated normalized terms in deterministic order.
    """
    seen: dict[str, None] = {}
    for keyword in keywords:
        words = _norm_words(keyword)
        if not words:
            continue
        phrase = " ".join(words)
        seen.setdefault(phrase, None)
        for word in words:
            seen.setdefault(word, None)
    for text in texts:
        for word in _norm_words(text):
            seen.setdefault(word, None)
    return tuple(seen)


def join_normalized_text(keywords: tuple[str, ...], *texts: str) -> str:
    """Join keywords and prose into a single space-delimited casefolded word stream for phrase checks.

    Args:
        keywords (tuple[str, ...]): Stated keywords.
        *texts (str): Product prose fields.

    Returns:
        str: Normalized words separated by single spaces.
    """
    parts = [_norm_words(part) for part in (*keywords, *texts) if part]
    return " ".join(word for words in parts for word in words)


def topic_overlap(
    target_keywords: tuple[str, ...],
    source_keywords: tuple[str, ...],
    source_terms: tuple[str, ...] = (),
    source_text: str = "",
) -> tuple[Decimal | None, list[str], list[str]]:
    """Share of mandate keywords found as whole words/phrases in the product's keywords and prose (spec 057).

    Args:
        target_keywords (tuple[str, ...]): Mandate keywords.
        source_keywords (tuple[str, ...]): Invention keywords.
        source_terms (tuple[str, ...], optional): Pre-extracted whole-word terms from keywords + prose.
        source_text (str, optional): Joined normalized prose for multi-word phrase checks.

    Returns:
        tuple[Decimal | None, list[str], list[str]]: Overlap in [0, 1] (None when target has no keywords),
            matched mandate keywords, and missing mandate keywords.
    """
    unique_targets: list[tuple[str, str]] = []
    seen_targets: set[str] = set()
    for raw in target_keywords:
        norm = " ".join(_norm_words(raw))
        if not norm or norm in seen_targets:
            continue
        seen_targets.add(norm)
        unique_targets.append((raw.strip(), norm))
    if not unique_targets:
        return None, [], []

    term_set = set(extract_terms(source_keywords))
    for term in source_terms:
        words = _norm_words(term)
        if words:
            term_set.add(" ".join(words))
            term_set.update(words)
    joined_parts = [source_text.strip(), join_normalized_text(source_keywords)]
    haystack = " " + " ".join(part for part in joined_parts if part) + " "

    matched: list[str] = []
    missing: list[str] = []
    for label, norm in unique_targets:
        if " " in norm:
            hit = norm in term_set or f" {norm} " in haystack
        else:
            hit = norm in term_set
        if hit:
            matched.append(label)
        else:
            missing.append(label)
    score = half_up(Decimal(len(matched)) / Decimal(len(unique_targets)))
    return score, matched, missing


def readiness_feature(
    stage: str | None, accepted_stages: tuple[str, ...], tkt: int | None, min_tkt: int | None
) -> Decimal | None:
    """Mean of stage compatibility and TKT compatibility; parts that are unknown or unasked are omitted (spec 057).

    Args:
        stage (str | None): Invention stage.
        accepted_stages (tuple[str, ...]): Mandate accepted stages.
        tkt (int | None): Invention TKT level (1–9), or None.
        min_tkt (int | None): Mandate minimum TKT preference (1–9), or None.

    Returns:
        Decimal | None: Value in [0, 1], or None when both parts are omitted.
    """
    parts: list[Decimal] = []
    if stage is not None and accepted_stages:
        parts.append(Decimal(1) if stage in accepted_stages else Decimal(0))
    if tkt is not None and min_tkt is not None:
        if tkt >= min_tkt:
            parts.append(Decimal(1))
        else:
            parts.append(max(Decimal(0), Decimal(1) - Decimal("0.25") * Decimal(min_tkt - tkt)))
    if not parts:
        return None
    return sum(parts, Decimal(0)) / Decimal(len(parts))
