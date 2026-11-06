"""Measurement domain models."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import AwareDatetime, BaseModel, Field


class StoredKind(StrEnum):
    """Row kinds. Points carry no energy; interval rows carry integer mWh."""

    INTERVAL_ENERGY = "interval_energy"
    AVERAGE_POWER = "average_power"
    INSTANTANEOUS_POWER = "instantaneous_power"
    COUNTER_POINT = "counter_point"
    COUNTER_DELTA = "counter_delta"


class Quality(StrEnum):
    """A reading's usability. ``long_gap`` keeps its whole-span total but supports no narrower period."""

    VALID = "valid"
    LONG_GAP = "long_gap"


class ReadingInput(BaseModel):
    """One raw observation as a source delivered it. The source declares what the value means.

    Attributes:
        value (Decimal): Exact raw value; never a binary float.
        unit (str): ``Wh`` or ``kWh`` for energy and counters, ``W`` or ``kW`` for power.
        interval_start (datetime | None): Interval start for interval energy and average power.
        interval_end (datetime | None): Interval end, exclusive.
        measured_at (datetime | None): Capture time for instantaneous power and counter readings.
        source_record_id (str | None): The source's stable record ID, when it has one.
    """

    value: Decimal = Field(allow_inf_nan=True)  # Normalization rejects non-finite values per reading.
    unit: str
    interval_start: AwareDatetime | None = None
    interval_end: AwareDatetime | None = None
    measured_at: AwareDatetime | None = None
    source_record_id: str | None = Field(default=None, min_length=1, max_length=200)


class Rejection(BaseModel):
    """A reading refused before storage. Diagnostics, never stored as valid data.

    Attributes:
        index (int): Position in the submitted batch.
        reason (str): Stable reason code.
    """

    index: int
    reason: str


class IngestResult(BaseModel):
    """What one batch changed, and the interval later reads must recompute.

    Attributes:
        added (int): New identities stored.
        repeated (int): Identical repeats; nothing stored.
        revised (int): Same identity, changed value: a new revision.
        rejected (list[Rejection]): Refused readings.
        affected_from (datetime | None): Start of the changed data, including replaced counter deltas.
        affected_to (datetime | None): End of the changed data, exclusive.
    """

    added: int = 0
    repeated: int = 0
    revised: int = 0
    rejected: list[Rejection] = []
    affected_from: datetime | None = None
    affected_to: datetime | None = None


class MeasurementRow(BaseModel):
    """A normalized row ready for storage or read back as current."""

    identity_key: str
    source_record_id: str | None
    kind: StoredKind
    interval_start: datetime | None = None
    interval_end: datetime | None = None
    measured_at: datetime | None = None
    energy_mwh: int | None = None
    raw_value: str | None = None
    raw_unit: str | None = None
    counter_segment: int | None = None
    quality: Quality = Quality.VALID
    revision: int = 1
    provenance: dict[str, Any] = {}

    def same_observation(self, other: "MeasurementRow") -> bool:
        """Tell whether a repeat carries exactly the stored observation.

        Args:
            other (MeasurementRow): The stored current row.

        Returns:
            bool: True for an idempotent repeat.
        """
        fields = ("kind", "interval_start", "interval_end", "measured_at", "energy_mwh", "raw_value", "raw_unit")
        return all(getattr(self, name) == getattr(other, name) for name in fields)
