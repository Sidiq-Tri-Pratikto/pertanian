"""Fixtures for scheduling: the matching world, an approved F01 pitch, and helpers."""

from datetime import datetime
from typing import Any

from httpx import AsyncClient, Response
from sqlalchemy.dialects.postgresql import Range

from app.core.database import get_session_factory
from app.scheduling.repository.sqlalchemy.models import BookingRecord
from tests.integration.matching.conftest import World, make_world, world  # noqa: F401 - shared fixtures
from tests.integration.pitches.conftest import act, reread, submitted


async def approved(loaded: World) -> dict[str, Any]:
    """Send F01 to A1 and approve it for discussion; return Mitra A's reading."""
    mitra = loaded.recipients.clients["A"]
    pitch = await submitted(loaded)
    response = await act(mitra, pitch, "decisions", "approve", submission=1, decision="APPROVE")
    assert response.status_code == 200, response.text
    return await reread(mitra, pitch)


async def propose(client: AsyncClient, pitch: dict[str, Any], slots: list[str], key: str, **body: Any) -> Response:
    """Propose slots of 60 minutes by default, in Asia/Jakarta."""
    return await client.post(
        f"/api/v1/pitches/{pitch['id']}/schedule-proposals",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "slots": slots,
            "minutes": 60,
            "time_zone": "Asia/Jakarta",
            "agenda": "Membahas rencana validasi enam bulan",
            **body,
        },
        headers={"Idempotency-Key": key},
    )


async def schedule(client: AsyncClient, pitch: dict[str, Any]) -> dict[str, Any]:
    """Read a pitch's schedule."""
    return (await client.get(f"/api/v1/pitches/{pitch['id']}/schedule")).json()


async def accept(client: AsyncClient, proposal: dict[str, Any], position: int, key: str) -> Response:
    """Accept the slot at a position (1-based) of a proposal."""
    slot = next(item for item in proposal["slots"] if item["position"] == position)
    return await client.post(
        f"/api/v1/schedule-proposals/{proposal['id']}/accept",
        json={
            "acting_party_id": client.headers["X-Acting-Party"],
            "slot_id": slot["id"],
            "expected_version": proposal["version"],
        },
        headers={"Idempotency-Key": key},
    )


async def busy(party_id: str, start: datetime, end: datetime) -> None:
    """Book a party's time, as another meeting would ("Agenda lain Peserta P")."""
    async with get_session_factory()() as session, session.begin():
        session.add(BookingRecord(party_id=party_id, title="Agenda lain", during=Range(start, end, bounds="[)")))
