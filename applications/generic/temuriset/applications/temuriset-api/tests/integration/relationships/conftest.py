"""Fixtures for relationships: an approved pitch whose meeting both parties recorded as completed."""

from datetime import UTC, datetime
from typing import Any

from httpx import AsyncClient, Response

from app.core import clock
from tests.integration.matching.conftest import World, make_world, world  # noqa: F401 - shared fixtures
from tests.integration.pitches.conftest import act, client_of, preflight, reread, submit
from tests.integration.scheduling.conftest import accept, propose

MADE = datetime(2026, 11, 2, 8, tzinfo=UTC)
AFTER = datetime(2026, 11, 20, tzinfo=UTC)

VALUES = {
    "name": "ClearSpring dan Mitra A",
    "scope": "Validasi prototipe dua belas bulan",
    "start_date": "2026-12-01",
    "amount": "25000",
    "currency": "USD",
    "evidence": "Catatan pertemuan 4 November 2026",
}
ALL = ["name", "type", "scope", "date", "amount"]


async def met(loaded: World, fixture: str = "F01", target: str = "A1", partner: str = "A") -> dict[str, Any]:
    """Send a fixture to a target, approve it, and complete one meeting; return the recipient's reading."""
    mitra = loaded.recipients.clients[partner]
    inventor, _ = client_of(loaded, fixture)
    sent = await submit(loaded, fixture, await preflight(loaded, fixture, target))
    assert sent.status_code == 201, sent.text
    pitch = await reread(mitra, {"id": sent.json()["pitch_id"]})
    approved = await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")
    assert approved.status_code == 200, approved.text
    with clock.frozen(MADE):
        offered = (await propose(mitra, pitch, ["2026-11-04T10:00:00Z", "2026-11-04T11:00:00Z"], "p")).json()
        meeting = (await accept(inventor, offered, 1, "a")).json()
    with clock.frozen(AFTER):
        for client, key in ((inventor, "o1"), (mitra, "o2")):
            done = await client.post(
                f"/api/v1/meetings/{meeting['id']}/outcome",
                json={"acting_party_id": client.headers["X-Acting-Party"], "result": "COMPLETED"},
                headers={"Idempotency-Key": key},
            )
            assert done.status_code == 200, done.text
    return await reread(mitra, pitch)


async def propose_partnership(client: AsyncClient, pitch: dict[str, Any], key: str = "ks", **body: Any) -> Response:
    """Propose version 1 as a PROJECT with every field in the ceiling and the proposer's subset."""
    return await client.post(
        f"/api/v1/pitches/{pitch['id']}/partnerships",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "type": "PROJECT",
            "values": VALUES,
            "ceiling": ALL,
            "subset": ALL,
            **body,
        },
        headers={"Idempotency-Key": key},
    )


async def partnership_action(
    client: AsyncClient, record: dict[str, Any], action: str, key: str, **body: Any
) -> Response:
    """POST an action on a relationship as the client's acting party."""
    return await client.post(
        f"/api/v1/partnerships/{record['id']}/{action}",
        json={"acting_party_id": client.headers["X-Acting-Party"], **body},
        headers={"Idempotency-Key": key},
    )


async def confirm(client: AsyncClient, record: dict[str, Any], subset: list[str], key: str) -> Response:
    """Confirm the record's current version with a public subset."""
    current = record["current"]
    return await partnership_action(
        client, record, "confirmations", key, version=current["number"], checksum=current["checksum"], subset=subset
    )
