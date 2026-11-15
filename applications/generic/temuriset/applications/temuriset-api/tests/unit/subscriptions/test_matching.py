"""Topic matching for investor alerts and digests (spec 046 FR-003)."""

import pytest

from app.subscriptions.service.matching import match

CLEARSPRING = {
    "sector": "Air dan sanitasi",
    "stage": "PROTOTYPE",
    "title": "ClearSpring",
    "summary": "Filter air tenaga surya untuk desa.",
    "keywords": ["filter air", "surya"],
}


@pytest.mark.parametrize(
    ("topics", "expected"),
    [
        (
            {"sectors": ["Air dan sanitasi"], "stages": ["PROTOTYPE"]},
            ("ALERT", ["sektor Air dan sanitasi", "tahap Prototipe"]),
        ),
        ({"sectors": ["air dan sanitasi"]}, ("ALERT", ["sektor Air dan sanitasi"])),
        ({"sectors": ["Air dan sanitasi"], "stages": ["MARKET"]}, ("DIGEST", ["sektor Air dan sanitasi"])),
        ({"sectors": ["Energi"], "keywords": ["surya"]}, ("DIGEST", ["kata kunci “surya”"])),
        ({"keywords": ["filter air", "baterai"]}, ("ALERT", ["kata kunci “filter air”"])),
        ({"keywords": ["filt"]}, None),
        ({"sectors": ["Energi"], "stages": ["IDEA"]}, None),
        ({}, None),
    ],
)
def test_every_filled_group_matching_is_an_alert_and_some_is_the_digest(
    topics: dict, expected: tuple[str, list[str]] | None
) -> None:
    """
    Condition:
    - ClearSpring (water, prototype, "filter air", "surya") against subscribers with different topics.

    Expected:
    - All filled groups matching gives ``ALERT``; some gives ``DIGEST``; none, a partial word or no topics gives None.
      Reasons name only the matched terms.
    """
    found = match(topics, CLEARSPRING)

    assert (None if found is None else (found.level, found.reasons)) == expected
