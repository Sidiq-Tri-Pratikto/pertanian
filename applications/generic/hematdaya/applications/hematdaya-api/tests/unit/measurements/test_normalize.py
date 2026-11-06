"""Normalization oracles from PRD §19.4 and edge cases."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import BaseModel, ValidationError

from app.assets.model.models import MeasurementKind
from app.core.types import DecimalString
from app.measurements.model.models import Quality, ReadingInput, StoredKind
from app.measurements.service.normalize import CounterPoint, ReadingRejectedError, counter_deltas, normalize, to_mwh

T0 = datetime(2026, 10, 19, 0, tzinfo=UTC)


def _interval(value: str, unit: str = "Wh", minutes: int = 60, **extra: object) -> ReadingInput:
    return ReadingInput(
        value=Decimal(value), unit=unit, interval_start=T0, interval_end=T0 + timedelta(minutes=minutes), **extra
    )


def test_interval_energy_is_stored_as_integer_mwh() -> None:
    """
    Condition:
    - 10 Wh, and 0.0147 kWh, over one hour.

    Expected:
    - 10,000 mWh and 14,700 mWh for that interval.
    """
    assert normalize(_interval("10"), MeasurementKind.INTERVAL_ENERGY).energy_mwh == 10_000
    assert normalize(_interval("0.0147", "kWh"), MeasurementKind.INTERVAL_ENERGY).energy_mwh == 14_700


def test_average_power_converts_by_duration() -> None:
    """
    Condition:
    - AT-27a: average power 100 W for 30 minutes.

    Expected:
    - 50 Wh, that is 50,000 mWh.
    """
    row = normalize(_interval("100", "W", minutes=30), MeasurementKind.AVERAGE_POWER)

    assert (row.kind, row.energy_mwh) == (StoredKind.AVERAGE_POWER, 50_000)


def test_instantaneous_power_never_becomes_energy() -> None:
    """
    Condition:
    - AT-27a: one instantaneous sample of 100 W.

    Expected:
    - A point with no energy.
    """
    row = normalize(ReadingInput(value=Decimal(100), unit="W", measured_at=T0), MeasurementKind.INSTANTANEOUS_POWER)

    assert (row.kind, row.energy_mwh, row.measured_at) == (StoredKind.INSTANTANEOUS_POWER, None, T0)


def test_counter_reset_starts_a_new_segment_with_no_energy() -> None:
    """
    Condition:
    - AT-27b: counter readings 100 → 130 → 5 Wh, an hour apart.

    Expected:
    - One 30 Wh delta; the reset interval has no energy, never −125 or +125 Wh.
    """
    points = [CounterPoint(T0 + timedelta(hours=i), wh * 1000) for i, wh in enumerate((100, 130, 5))]

    deltas = counter_deltas(points, 3600)

    assert [(row.interval_start, row.energy_mwh, row.counter_segment) for row in deltas] == [(T0, 30_000, 0)]


def test_counter_after_reset_continues_in_the_new_segment() -> None:
    """
    Condition:
    - 100 → 130 → 5 → 25 Wh.

    Expected:
    - 30 Wh in segment 0, then 20 Wh in segment 1.
    """
    points = [CounterPoint(T0 + timedelta(hours=i), wh * 1000) for i, wh in enumerate((100, 130, 5, 25))]

    assert [(row.energy_mwh, row.counter_segment) for row in counter_deltas(points, 3600)] == [(30_000, 0), (20_000, 1)]


def test_long_counter_gap_keeps_its_total_but_is_flagged() -> None:
    """
    Condition:
    - Hourly counter readings with one five-hour gap.

    Expected:
    - The gap's delta keeps its full energy and is flagged long_gap; the hourly one is valid.
    """
    points = [
        CounterPoint(T0, 0),
        CounterPoint(T0 + timedelta(hours=1), 10_000),
        CounterPoint(T0 + timedelta(hours=6), 60_000),
    ]

    assert [(row.energy_mwh, row.quality) for row in counter_deltas(points, 3600)] == [
        (10_000, Quality.VALID),
        (50_000, Quality.LONG_GAP),
    ]


@pytest.mark.parametrize(("exact", "expected"), [("0.5", 0), ("1.5", 2), ("2.5", 2), ("2.5001", 3)])
def test_quantization_rounds_half_to_even(exact: str, expected: int) -> None:
    """
    Condition:
    - Exact mWh values with fractional parts, including ties.

    Expected:
    - Nearest integer mWh, exact ties to even.
    """
    assert to_mwh(Decimal(exact)) == expected


@pytest.mark.parametrize(
    ("reading", "kind", "reason"),
    [
        (_interval("-1"), MeasurementKind.INTERVAL_ENERGY, "negative"),
        (_interval("NaN"), MeasurementKind.INTERVAL_ENERGY, "non_finite"),
        (_interval("Infinity"), MeasurementKind.INTERVAL_ENERGY, "non_finite"),
        (_interval("1", "W"), MeasurementKind.INTERVAL_ENERGY, "unit_invalid"),
        (_interval("1", minutes=0), MeasurementKind.INTERVAL_ENERGY, "interval_reversed"),
        (
            ReadingInput(value=Decimal(1), unit="Wh", measured_at=T0),
            MeasurementKind.INTERVAL_ENERGY,
            "interval_bounds_required",
        ),
        (_interval("1", "W"), MeasurementKind.INSTANTANEOUS_POWER, "capture_time_required"),
        (ReadingInput(value=Decimal(1), unit="W", measured_at=T0), MeasurementKind.COUNTER, "unit_invalid"),
    ],
)
def test_invalid_readings_are_rejected_not_zeroed(reading: ReadingInput, kind: MeasurementKind, reason: str) -> None:
    """
    Condition:
    - Negative, non-finite, wrong unit, empty or missing bounds, or a missing capture time.

    Expected:
    - Each is rejected with its stable reason, never stored as zero.
    """
    with pytest.raises(ReadingRejectedError) as error:
        normalize(reading, kind)

    assert error.value.reason == reason


def test_zero_is_a_measurement() -> None:
    """
    Condition:
    - A valid 0 Wh interval.

    Expected:
    - It is stored as 0 mWh, not dropped.
    """
    assert normalize(_interval("0"), MeasurementKind.INTERVAL_ENERGY).energy_mwh == 0


def test_identity_prefers_the_source_record_id() -> None:
    """
    Condition:
    - The same interval with and without a capture ID; equal values in different intervals.

    Expected:
    - The record ID wins; different intervals are different identities.
    """
    with_id = normalize(_interval("5", source_record_id="abc"), MeasurementKind.INTERVAL_ENERGY)
    without_id = normalize(_interval("5"), MeasurementKind.INTERVAL_ENERGY)
    later = normalize(
        ReadingInput(
            value=Decimal(5), unit="Wh", interval_start=T0 + timedelta(hours=1), interval_end=T0 + timedelta(hours=2)
        ),
        MeasurementKind.INTERVAL_ENERGY,
    )

    assert with_id.identity_key == "r:abc"
    assert without_id.identity_key != later.identity_key


class _Wire(BaseModel):
    value: DecimalString


def test_decimal_string_refuses_json_numbers() -> None:
    """
    Condition:
    - A decimal arrives as a JSON number, as text, and as text with an exponent.

    Expected:
    - Numbers and exponents are refused; text parses exactly and serializes back as text.
    """
    with pytest.raises(ValidationError) as number:
        _Wire.model_validate_json('{"value": 12.5}')
    with pytest.raises(ValidationError):
        _Wire.model_validate_json('{"value": "1e3"}')
    parsed = _Wire.model_validate_json('{"value": "0.1"}')

    assert number.value.errors()[0]["type"] == "decimal_string_type"
    assert parsed.value == Decimal("0.1")
    assert parsed.model_dump_json() == '{"value":"0.1"}'
