"""Broker payloads cannot supply authorization or fabricate a current capture."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.errors.base import RequestInvalidError
from app.meter_pilot.service.telemetry import decode_telemetry


def test_decode_decimal_counter():
    """Bind a reading to the broker topic and preserve its exact Wh value."""
    meter = uuid4()
    now = datetime.fromtimestamp(1_800_000_001, UTC)
    identity, reading = decode_telemetry(
        f"hematdaya/v1/meters/{meter}/readings",
        b'{"measured_at":1800000000,"energy_wh":"12.345"}',
        now,
    )
    assert identity == meter
    assert str(reading.value) == "12.345"
    assert reading.unit == "Wh"
    assert reading.measured_at == datetime.fromtimestamp(1_800_000_000, UTC)


@pytest.mark.parametrize(
    "payload",
    [
        b'{"measured_at":1800000000,"energy_wh":"1","site_id":"fake-secret"}',
        b'{"measured_at":1800000000,"energy_wh":1}',
        b'{"measured_at":1800000000,"energy_wh":"Infinity"}',
        b'{"measured_at":1800000000,"energy_wh":"-1"}',
        b'{"measured_at":1800000002,"energy_wh":"1"}',
    ],
)
def test_refuse_invalid_payload(payload):
    """Never expose a payload or treat a malformed or future sample as energy."""
    with pytest.raises(RequestInvalidError) as caught:
        decode_telemetry(f"hematdaya/v1/meters/{uuid4()}/readings", payload, datetime.fromtimestamp(1_800_000_001, UTC))
    assert "fake-secret" not in str(caught.value.debug_info)
