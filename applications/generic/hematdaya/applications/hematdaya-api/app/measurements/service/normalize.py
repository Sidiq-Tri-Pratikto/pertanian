"""Pure normalization: one rule for every source, so no adapter can bypass it."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

from app.assets.model.models import MeasurementKind
from app.measurements.model.models import MeasurementRow, Quality, ReadingInput, StoredKind

MWH_PER_UNIT = {"Wh": Decimal(1000), "kWh": Decimal(1_000_000)}
MILLIWATT_PER_UNIT = {"W": Decimal(1000), "kW": Decimal(1_000_000)}
LONG_GAP_CADENCES = 2
"""A counter delta spanning more than this many cadences keeps its total but supports no narrower period."""


class ReadingRejectedError(ValueError):
    """A reading that must not be stored. ``reason`` is a stable code."""

    def __init__(self, reason: str) -> None:
        """Name the reason.

        Args:
            reason (str): Stable reason code.
        """
        super().__init__(reason)
        self.reason = reason


def to_mwh(value: Decimal) -> int:
    """Quantize once to integer mWh: nearest, exact ties to even.

    Args:
        value (Decimal): Exact mWh.

    Returns:
        int: Integer mWh.
    """
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def identity_key(reading: ReadingInput, kind: StoredKind) -> str:
    """Return the reading's identity: the source record ID, else kind plus interval bounds or capture time.

    Args:
        reading (ReadingInput): The reading.
        kind (StoredKind): Its stored kind.

    Returns:
        str: Key unique per source; repeats share it, distinct observations never do.
    """
    if reading.source_record_id is not None:
        return f"r:{reading.source_record_id}"
    if reading.measured_at is not None:
        return f"p:{kind.value}:{reading.measured_at.timestamp():.6f}"
    assert reading.interval_start is not None and reading.interval_end is not None
    return f"i:{kind.value}:{reading.interval_start.timestamp():.6f}:{reading.interval_end.timestamp():.6f}"


def normalize(reading: ReadingInput, source_kind: MeasurementKind) -> MeasurementRow:
    """Turn one raw observation into a storable row.

    Interval energy keeps its interval. Average power becomes ``W × seconds / 3600``. Instantaneous power and
    counter readings become points with no energy; counter deltas are derived separately.

    Args:
        reading (ReadingInput): The raw observation.
        source_kind (MeasurementKind): What the source declares its values mean.

    Returns:
        MeasurementRow: The normalized row.

    Raises:
        ReadingRejectedError: For a non-finite or negative value, a wrong unit, or missing or reversed time bounds.
    """
    value = reading.value
    if not value.is_finite():
        raise ReadingRejectedError("non_finite")
    if value < 0:
        raise ReadingRejectedError("negative")
    raw = {"raw_value": format(value, "f"), "raw_unit": reading.unit, "source_record_id": reading.source_record_id}
    if source_kind in (MeasurementKind.INTERVAL_ENERGY, MeasurementKind.AVERAGE_POWER):
        start, end = reading.interval_start, reading.interval_end
        if start is None or end is None or reading.measured_at is not None:
            raise ReadingRejectedError("interval_bounds_required")
        if end <= start:
            raise ReadingRejectedError("interval_reversed")
        if source_kind is MeasurementKind.INTERVAL_ENERGY:
            factor = MWH_PER_UNIT.get(reading.unit)
            kind = StoredKind.INTERVAL_ENERGY
            energy = None if factor is None else to_mwh(value * factor)
        else:
            factor = MILLIWATT_PER_UNIT.get(reading.unit)
            kind = StoredKind.AVERAGE_POWER
            seconds = Decimal((end - start) // timedelta(microseconds=1)) / Decimal(1_000_000)
            energy = None if factor is None else to_mwh(value * factor * seconds / Decimal(3600))
        if energy is None:
            raise ReadingRejectedError("unit_invalid")
        return MeasurementRow(
            identity_key=identity_key(reading, kind),
            kind=kind,
            interval_start=start,
            interval_end=end,
            energy_mwh=energy,
            **raw,
        )
    if reading.measured_at is None or reading.interval_start is not None or reading.interval_end is not None:
        raise ReadingRejectedError("capture_time_required")
    if source_kind is MeasurementKind.INSTANTANEOUS_POWER:
        kind, units = StoredKind.INSTANTANEOUS_POWER, MILLIWATT_PER_UNIT
    else:
        kind, units = StoredKind.COUNTER_POINT, MWH_PER_UNIT
    if reading.unit not in units:
        raise ReadingRejectedError("unit_invalid")
    return MeasurementRow(identity_key=identity_key(reading, kind), kind=kind, measured_at=reading.measured_at, **raw)


@dataclass(frozen=True)
class CounterPoint:
    """A current counter reading: capture time and cumulative mWh."""

    measured_at: datetime
    cumulative_mwh: int

    @classmethod
    def from_row(cls, row: MeasurementRow) -> "CounterPoint":
        """Read a stored counter point.

        Args:
            row (MeasurementRow): A ``counter_point`` row.

        Returns:
            CounterPoint: Its capture time and cumulative mWh.
        """
        assert row.measured_at is not None and row.raw_value is not None and row.raw_unit is not None
        return cls(row.measured_at, to_mwh(Decimal(row.raw_value) * MWH_PER_UNIT[row.raw_unit]))


def counter_deltas(points: list[CounterPoint], cadence_seconds: int | None) -> list[MeasurementRow]:
    """Derive interval energy from consecutive counter readings, one segment at a time.

    The first reading anchors a segment and is not energy. A decrease starts a new segment, and the reset
    interval has no energy at all: never a negative delta, never the raw value.

    Args:
        points (list[CounterPoint]): Current counter readings of one source.
        cadence_seconds (int | None): The source's cadence; one hour when unknown.

    Returns:
        list[MeasurementRow]: Derived deltas in time order.
    """
    long_gap = timedelta(seconds=(cadence_seconds or 3600) * LONG_GAP_CADENCES)
    ordered = sorted(points, key=lambda point: point.measured_at)
    deltas: list[MeasurementRow] = []
    segment = 0
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.cumulative_mwh < previous.cumulative_mwh:
            segment += 1
            continue
        start, end = previous.measured_at, current.measured_at
        deltas.append(
            MeasurementRow(
                identity_key=f"d:{start.timestamp():.6f}:{end.timestamp():.6f}",
                source_record_id=None,
                kind=StoredKind.COUNTER_DELTA,
                interval_start=start,
                interval_end=end,
                energy_mwh=current.cumulative_mwh - previous.cumulative_mwh,
                counter_segment=segment,
                quality=Quality.LONG_GAP if end - start > long_gap else Quality.VALID,
            )
        )
    return deltas
