"""Parse the constrained meter telemetry contract at the broker boundary."""

import re
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.errors.base import RequestInvalidError
from app.measurements.model.models import ReadingInput

TOPIC_FILTER = "hematdaya/v1/meters/+/readings"
_TOPIC = re.compile(r"hematdaya/v1/meters/([0-9a-f-]{36})/readings")


class CounterPayload(BaseModel):
    """Only the capture time and cumulative Wh are accepted from a meter."""

    model_config = ConfigDict(extra="forbid", strict=True)
    measured_at: int = Field(ge=0, le=253402300799)
    energy_wh: str = Field(pattern=r"^[0-9]{1,15}(\.[0-9]{1,6})?$", max_length=22)


def decode_telemetry(topic: str, payload: bytes, now: datetime) -> tuple[UUID, ReadingInput]:
    """Return identity from the ACL-bound topic and a validated counter sample."""
    match = _TOPIC.fullmatch(topic)
    if not match or len(payload) > 256:
        raise RequestInvalidError()
    try:
        meter_id = UUID(match[1])
        if str(meter_id) != match[1]:
            raise ValueError("Noncanonical meter identity")
        data = CounterPayload.model_validate_json(payload)
        measured_at = datetime.fromtimestamp(data.measured_at, UTC)
    except (ValueError, OverflowError, OSError, ValidationError):
        # Payload values may be sensitive. Never attach the validation exception to the error record.
        raise RequestInvalidError() from None
    if measured_at > now:
        raise RequestInvalidError()
    return meter_id, ReadingInput(value=Decimal(data.energy_wh), unit="Wh", measured_at=measured_at)
