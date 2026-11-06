"""Template brief helpers and the summarizer check, with no database (spec 022)."""

import pytest

from app.briefs.service.summarizer_service import OffSummarizer, traceable
from app.briefs.service.template import amount, brief_text

SUPPLIED = [
    {"text": "Saat ini: Kapasitas saring 10 L/jam.", "refs": [{"kind": "fact"}]},
    {"text": "Kebutuhan USD 20.000–30.000, total 6 bulan untuk biaya pilot enam bulan.", "refs": [{"kind": "x"}]},
]


@pytest.mark.parametrize(
    ("value", "shown"),
    [("20000.0000", "20.000"), ("500000", "500.000"), ("1234567.5000", "1.234.567,5"), ("0.1000", "0,1"), ("7", "7")],
)
def test_amounts_use_indonesian_grouping_without_floats(value: str, shown: str) -> None:
    """
    Condition:
    - Decimal strings as the service stores them.

    Expected:
    - Dots group thousands, a comma marks the fraction, and trailing zeros go.
    """
    assert amount(value) == shown


@pytest.mark.parametrize(
    ("summary", "expected"),
    [
        ("Kapasitas saring 10 L/jam. Kebutuhan USD 20.000–30.000 untuk biaya pilot.", True),
        ("Kapasitas saring 50 L/jam.", False),
        ("Sertifikat nasional sudah terbit untuk produk ekspor.", False),
        ("", True),
    ],
)
def test_a_summary_must_rest_on_the_supplied_sentences(summary: str, expected: bool) -> None:
    """
    Condition:
    - Summaries that repeat supplied facts, invent a number, or invent a claim (AC68).

    Expected:
    - Only the first and an empty one pass.
    """
    assert traceable(summary, SUPPLIED) is expected


async def test_the_default_summarizer_is_off() -> None:
    """
    Condition:
    - The default port.

    Expected:
    - It is named ``off`` and returns nothing, so the template is used.
    """
    assert OffSummarizer.name == "off"
    assert await OffSummarizer().summarize(SUPPLIED) is None
    assert brief_text(SUPPLIED).splitlines() == [sentence["text"] for sentence in SUPPLIED]
