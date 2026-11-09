"""A provisioned owner enrolls a meter and sees measured energy through the normal read path."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from paho.mqtt.client import MQTTMessage

from app.core.database import get_session_factory
from app.core.errors.base import NotFoundError, RequestInvalidError
from app.core.settings import get_settings
from app.measurements.service.service import IngestService
from app.meter_pilot.operator import provision
from app.meter_pilot.repository.sqlalchemy.repository import SqlAlchemyPilotRepository
from app.meter_pilot.worker import accept_message

BASE = datetime(2026, 11, 9, 3, tzinfo=UTC)
START_KEY = "start_meter_pilot_test_key"
CONFIRM_KEY = "confirm_meter_pilot_test_key"


@pytest.fixture
def clock(monkeypatch):
    """Keep enrollment, transport and the standard site's report on the same clock."""
    times = [BASE]
    monkeypatch.setattr(get_settings(), "meter_pilot_enabled", True)
    for module in ("app.meter_pilot.service.service", "app.meter_pilot.worker", "app.sites.service.clock"):
        monkeypatch.setattr(f"{module}.wall_now", lambda: times[0])
    return times


def packet(meter_id, at, wh, **extra):
    """Build a synthetic broker delivery with the production payload shape."""
    message = MQTTMessage(topic=f"hematdaya/v1/meters/{meter_id}/readings".encode())
    message.qos = 1
    message.payload = json.dumps({"measured_at": int(at.timestamp()), "energy_wh": wh, **extra}).encode()
    return message


async def setup_site():
    """Provision an isolated site using the operator's normal transaction."""
    meter_id = uuid4()
    async with get_session_factory().begin() as session:
        site_id, code = await provision(session, "Meter test site", meter_id)
    return site_id, meter_id, {"Authorization": f"Bearer {code}"}


async def start(client, site, auth, key=START_KEY):
    return await client.post(
        f"/api/v1/sites/{site}/enrollments",
        headers={**auth, "Idempotency-Key": key},
        json={"model_id": "shelly-plug-pm-gen3"},
    )


async def confirm(client, enrollment, auth, name="Desk lamp"):
    return await client.post(
        f"/api/v1/enrollments/{enrollment}/confirm",
        headers={**auth, "Idempotency-Key": CONFIRM_KEY},
        json={"asset_name": name},
    )


async def test_pilot_disabled_by_default(client: AsyncClient):
    catalog = await client.get("/api/v1/device-catalog")
    assert catalog.json()["devices"][0]["status"] == "planned"
    assert (await client.get("/api/v1/pilot/session")).status_code == 404


async def test_enroll_retry_energy_freshness_and_revocation(client: AsyncClient, clock):
    site, meter, auth = await setup_site()
    other_site, _, other_auth = await setup_site()
    assert (await client.get("/api/v1/pilot/session", headers=auth)).json()["site_id"] == str(site)
    assert (await client.get("/api/v1/sites/" + str(other_site), headers=auth)).status_code == 404
    assert (await client.get("/api/v1/device-catalog")).json()["devices"][0]["status"] == "available"
    opened = await start(client, site, auth)
    assert opened.status_code == 200, opened.text
    enrollment = opened.json()["id"]
    assert opened.json()["status"] == "waiting"
    assert (await start(client, site, auth)).json()["id"] == enrollment
    assert (await start(client, site, other_auth)).status_code == 404
    assert (await client.get(f"/api/v1/enrollments/{enrollment}", headers=other_auth)).status_code == 404
    assert (await confirm(client, enrollment, auth)).status_code == 409

    clock[0] += timedelta(seconds=60)
    with pytest.raises(NotFoundError):
        await accept_message(packet(uuid4(), clock[0], "100.000"))
    with pytest.raises(RequestInvalidError):
        await accept_message(packet(meter, clock[0], "100.000", site_id=str(other_site)))
    await accept_message(packet(meter, clock[0], "100.000"))
    progress = await client.get(f"/api/v1/enrollments/{enrollment}", headers=auth)
    assert progress.json()["status"] == "ready"
    summary_url = f"/api/v1/sites/{site}/summary?preset=today"
    assert (await client.get(summary_url, headers=auth)).json()["assets"] == []

    confirmations = await asyncio.gather(confirm(client, enrollment, auth), confirm(client, enrollment, auth))
    assert [response.status_code for response in confirmations] == [200, 200]
    assert confirmations[0].json() == confirmations[1].json()
    assert confirmations[0].json()["status"] == "connected"
    assert (await confirm(client, enrollment, auth, "Different name")).status_code == 409
    initial = (await client.get(summary_url, headers=auth)).json()
    assert initial["energy_kwh"] is None
    assert initial["source_freshness"][0]["state"] == "current"

    clock[0] += timedelta(seconds=60)
    delivery = packet(meter, clock[0], "110.000")
    await accept_message(delivery)
    await accept_message(delivery)
    recorded = (await client.get(summary_url, headers=auth)).json()
    assert recorded["energy_kwh"] == "0.010"
    assert len(recorded["assets"]) == 1
    assert recorded["source_freshness"][0]["origin"] == "live"

    clock[0] += timedelta(seconds=121)
    await accept_message(delivery)
    stale = (await client.get(summary_url, headers=auth)).json()
    assert stale["source_freshness"][0]["state"] == "stale"
    async with get_session_factory().begin() as session:
        await SqlAlchemyPilotRepository(session).update_assignment(meter, meter_revoked_at=clock[0])
    with pytest.raises(NotFoundError):
        await accept_message(packet(meter, clock[0], "130.000"))
    assert (await client.get(summary_url, headers=auth)).json()["energy_kwh"] == "0.010"
    async with get_session_factory().begin() as session:
        await SqlAlchemyPilotRepository(session).update_assignment(meter, access_digest=None)
    assert (await client.get(summary_url, headers=auth)).status_code == 401


async def test_enrollment_expiry_and_failed_confirmation_roll_back(client: AsyncClient, clock, monkeypatch):
    site, meter, auth = await setup_site()
    first = (await start(client, site, auth)).json()
    clock[0] += timedelta(minutes=16)
    assert (await start(client, site, auth)).json()["status"] == "expired"
    assert (await confirm(client, first["id"], auth)).status_code == 409
    second = (await start(client, site, auth, "new_meter_pilot_attempt_key")).json()
    assert second["id"] != first["id"]
    clock[0] += timedelta(seconds=60)
    await accept_message(packet(meter, clock[0], "3"))
    with monkeypatch.context() as patch:

        async def fail_ingestion(*_args, **_kwargs):
            raise RequestInvalidError()

        patch.setattr(IngestService, "ingest", fail_ingestion)
        assert (await confirm(client, second["id"], auth)).status_code == 400
    summary = (await client.get(f"/api/v1/sites/{site}/summary?preset=today", headers=auth)).json()
    assert summary["assets"] == []
    assert (await confirm(client, second["id"], auth)).json()["status"] == "connected"
