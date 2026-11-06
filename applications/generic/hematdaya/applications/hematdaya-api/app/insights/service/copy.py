"""User-facing copy, built only from a frozen snapshot. Advice stays advice: no diagnosis, waste or savings claim,
and never an instruction to switch anything off."""

from datetime import date
from typing import Any

MONTHS = ("Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
          "November", "Desember")  # fmt: skip
FORBIDDEN = ("boros", "pemborosan", "rusak", "kerusakan", "matikan", "cabut", "hemat sebesar", "terbukti hemat")


def number(value: str) -> str:
    """Render a wire decimal the Indonesian way, without parsing it: ``1.400`` becomes ``1,400``.

    Args:
        value (str): Decimal string.

    Returns:
        str: Display text.
    """
    whole, _, fraction = value.lstrip("-").partition(".")
    grouped = f"{int(whole):,}".replace(",", ".")
    return grouped + ("," + fraction if fraction else "")


def _date(text: str) -> str:
    day = date.fromisoformat(text)
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _range(start: str, end: str) -> str:
    return _date(start) if start == end else f"{_date(start)} – {_date(end)}"


def insight_copy(snapshot: dict[str, Any]) -> dict[str, str | None]:
    """Build the observation's text from its evidence.

    Args:
        snapshot (dict[str, Any]): Frozen evidence.

    Returns:
        dict[str, str | None]: Title, observation, percent note, comparison, unknowns and next step.
    """
    name = snapshot["asset"]["name"]
    up = snapshot["direction"] == "increase"
    delta = number(snapshot["delta_kwh"])
    percent = snapshot["percent"]
    pct = f"{'+' if up else '−'}{number(percent.lstrip('-'))}%" if percent is not None else None
    period = _range(snapshot["period"]["start_date"], snapshot["period"]["end_date"])
    weeks = len(snapshot["historical"])
    history = "; ".join(
        f"{_range(w['start_date'], w['end_date'])}: {number(w['mask_kwh'])} kWh" for w in snapshot["historical"]
    )
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
