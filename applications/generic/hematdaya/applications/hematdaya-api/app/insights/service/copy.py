"""User-facing copy, built only from a frozen snapshot. Advice stays advice: no diagnosis, waste or savings claim,
and never an instruction to switch anything off."""

from datetime import date
from typing import Any

from app.core.locale import MONTH_NAMES, Locale

FORBIDDEN = ("boros", "pemborosan", "rusak", "kerusakan", "matikan", "cabut", "hemat sebesar", "terbukti hemat")


def number(value: str, language: Locale = "id") -> str:
    """Render a wire decimal the Indonesian way, without parsing it: ``1.400`` becomes ``1,400``.

    Args:
        value (str): Decimal string.

    Returns:
        str: Display text.
    """
    whole, _, fraction = value.lstrip("-").partition(".")
    grouped = f"{int(whole):,}"
    if language == "en":
        return grouped + ("." + fraction if fraction else "")
    return grouped.replace(",", ".") + ("," + fraction if fraction else "")


def _date(text: str, language: Locale = "id") -> str:
    day = date.fromisoformat(text)
    return f"{day.day} {MONTH_NAMES[language][day.month - 1]} {day.year}"


def _range(start: str, end: str, language: Locale = "id") -> str:
    return _date(start, language) if start == end else f"{_date(start, language)} – {_date(end, language)}"


def insight_copy(snapshot: dict[str, Any], language: Locale = "id") -> dict[str, str | None]:
    """Build the observation's text from its evidence.

    Args:
        snapshot (dict[str, Any]): Frozen evidence.

    Returns:
        dict[str, str | None]: Title, observation, percent note, comparison, unknowns and next step.
    """
    name = snapshot["asset"]["name"]
    up = snapshot["direction"] == "increase"
    delta = number(snapshot["delta_kwh"], language)
    percent = snapshot["percent"]
    pct = f"{'+' if up else '−'}{number(percent.lstrip('-'), language)}%" if percent is not None else None
    period = _range(snapshot["period"]["start_date"], snapshot["period"]["end_date"], language)
    weeks = len(snapshot["historical"])
    history = "; ".join(
        f"{_range(w['start_date'], w['end_date'], language)}: {number(w['mask_kwh'], language)} kWh"
        for w in snapshot["historical"]
    )
    if language == "en":
        change = "increase" if up else "decrease"
        return {
            "title": f"{name} {'rose' if up else 'fell'} by {delta} kWh" + (f" ({pct})" if pct else ""),
            "observed": f"{name} used {number(snapshot['current']['mask_kwh'], language)} kWh during {period}. "
            f"The median across {weeks} comparison weeks was {number(snapshot['baseline_kwh'], language)} kWh. "
            f"The recorded {change} was {delta} kWh.",
            "pct_note": None if pct else "A percentage is unavailable because the comparison value was zero.",
            "comparison": f"The same days and hours in the previous {weeks} weeks ({history}).",
            "unknown": "The cause of the change is unknown. "
            + ("The reading alone cannot diagnose a device problem." if up else "Savings require separate evidence."),
            "step": "Check whether the timing or pattern of use changed.",
        }
    return {
        "title": f"{name} {'naik' if up else 'turun'} {delta} kWh" + (f" ({pct})" if pct else ""),
        "observed": (
            f"{name} memakai {number(snapshot['current']['mask_kwh'])} kWh pada {period}. Median {weeks} minggu"
            f" pembanding: {number(snapshot['baseline_kwh'])} kWh. {'Kenaikan' if up else 'Penurunan'} tercatat"
            f" {delta} kWh."
        ),
        "pct_note": None if pct else "Persentase tidak tersedia karena nilai pembanding nol.",
        "comparison": f"Hari dan jam yang sama pada {weeks} minggu sebelumnya ({history}).",
        "unknown": "Penyebab perubahan belum diketahui. "
        + ("Kenaikan ini bukan diagnosis masalah perangkat." if up else "Penurunan ini bukan bukti penghematan."),
        "step": "Periksa apakah waktu atau pola pemakaian berubah.",
    }
