"""Effective public fields: never more than either party allowed, the ceiling, or what restrictions leave (030)."""

import itertools

from app.relationships.service.consent import FIELDS, checksum, effective_fields
from app.relationships.service.service import public_values

SUBSETS = [list(combo) for size in range(len(FIELDS) + 1) for combo in itertools.combinations(FIELDS, size)]


def test_effective_fields_never_exceed_either_subset_the_ceiling_or_survive_a_restriction() -> None:
    """
    Condition:
    - Every pair of party subsets of the six fields, with the full ceiling, a narrower ceiling, and a restriction.

    Expected:
    - The result is exactly the intersection within the ceiling minus restrictions, so never wider than either.
    """
    for mine, theirs in itertools.product(SUBSETS, repeat=2):
        for ceiling in (list(FIELDS), ["name", "type", "scope"]):
            shown = effective_fields(ceiling, [mine, theirs], {"date"})

            assert set(shown) <= set(mine) & set(theirs) & set(ceiling)
            assert "date" not in shown
            assert set(shown) == (set(mine) & set(theirs) & set(ceiling)) - {"date"}


def test_one_confirmation_makes_nothing_public() -> None:
    """
    Condition:
    - Only the proposer has confirmed (AC52).

    Expected:
    - No public field.
    """
    assert effective_fields(list(FIELDS), [list(FIELDS)], set()) == []


def test_the_checksum_changes_with_any_content_and_the_version() -> None:
    """
    Condition:
    - The same summary, then a different scope, then another version number.

    Expected:
    - Equal for equal content; different otherwise, so an old confirmation cannot confirm a new version (FR-001).
    """
    values = {"scope": "A", "start_date": "2026-12-01"}

    assert checksum("PROJECT", 1, values, ["name"]) == checksum("PROJECT", 1, dict(values), ["name"])
    assert checksum("PROJECT", 1, values, ["name"]) != checksum("PROJECT", 1, {**values, "scope": "B"}, ["name"])
    assert checksum("PROJECT", 1, values, ["name"]) != checksum("PROJECT", 2, values, ["name"])


def test_a_project_shows_no_share_and_evidence_never_shows() -> None:
    """
    Condition:
    - A PROJECT with an amount and, wrongly, a percent; every field allowed (AC54).

    Expected:
    - The amount shows with its currency; no percent, share or evidence appears.
    """
    values = {
        "name": "N",
        "scope": "S",
        "start_date": "2026-12-01",
        "amount": "25000",
        "currency": "USD",
        "percent": "10",
        "evidence": "private",
    }

    shown = public_values("PROJECT", values, list(FIELDS))

    assert shown["amount"] == {"amount": "25000", "currency": "USD"}
    assert "percent" not in shown and "private" not in str(shown)
    assert shown["type"] == "Proyek"
