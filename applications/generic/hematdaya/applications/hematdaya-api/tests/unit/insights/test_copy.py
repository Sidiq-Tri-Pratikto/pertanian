"""Insight copy is built from the snapshot and never diagnoses, claims waste or savings, or says switch off."""

import pytest

from app.insights.service.copy import FORBIDDEN, insight_copy, number


def _snapshot(direction: str, percent: str | None, expected_use: str = "unknown") -> dict:
    return {
        "direction": direction,
        "asset": {"name": "Kulkas", "expected_use": expected_use},
        "delta_kwh": "1.400" if direction == "increase" else "-1.400",
        "percent": percent,
        "period": {"start_date": "2026-10-19", "end_date": "2026-10-25"},
        "current": {"mask_kwh": "3.920"},
        "baseline_kwh": "2.520",
        "historical": [
            {"start_date": "2026-10-12", "end_date": "2026-10-18", "mask_kwh": "2.520"},
            {"start_date": "2026-10-05", "end_date": "2026-10-11", "mask_kwh": "2.520"},
        ],
    }


def test_increase_copy_matches_the_evidence() -> None:
    """
    Condition:
    - An increase of 1.400 kWh, 55.56%.

    Expected:
    - Title and body use Indonesian decimals and name the comparison weeks.
    """
    copy = insight_copy(_snapshot("increase", "55.56"))

    assert copy["title"] == "Kulkas naik 1,400 kWh (+55,56%)"
    assert "Median 2 minggu pembanding: 2,520 kWh" in copy["observed"]
    assert "12 Oktober 2026 – 18 Oktober 2026: 2,520 kWh" in copy["comparison"]
    assert copy["pct_note"] is None


@pytest.mark.parametrize(
    "snapshot",
    [
        _snapshot("increase", "55.56", "continuous"),
        _snapshot("decrease", "-35.71"),
        _snapshot("increase", None),
    ],
)
def test_no_generated_string_breaks_the_advice_boundary(snapshot: dict) -> None:
    """
    Condition:
    - A continuous asset's increase, a decrease, and a zero-baseline increase.

    Expected:
    - No forbidden word appears; a decrease is never verified savings; a missing percent says why.
    """
    copy = insight_copy(snapshot)
    text = " ".join(value for value in copy.values() if value).lower()

    assert not [word for word in FORBIDDEN if word in text]
    if snapshot["direction"] == "decrease":
        assert copy["title"] == "Kulkas turun 1,400 kWh (−35,71%)"
        assert "bukan bukti penghematan" in copy["unknown"]
    if snapshot["percent"] is None:
        assert copy["pct_note"] == "Persentase tidak tersedia karena nilai pembanding nol."


def test_numbers_render_without_parsing_to_float() -> None:
    """
    Condition:
    - Large and fractional wire decimals.

    Expected:
    - Thousands with dots, decimals with a comma.
    """
    assert (number("1234.500"), number("0.168"), number("72")) == ("1.234,500", "0,168", "72")


def test_english_copy_uses_the_same_frozen_values() -> None:
    """
    Condition:
    - The same observation snapshot is presented in both languages.

    Expected:
    - Both presentations retain the original values and periods.
    """
    copy = insight_copy(_snapshot("increase", "55.56"), "en")
    assert copy["title"] == "Kulkas rose by 1.400 kWh (+55.56%)"
    assert "3.920 kWh" in copy["observed"]
    assert "2.520 kWh" in copy["observed"]
    assert "12 October 2026 – 18 October 2026" in copy["comparison"]
