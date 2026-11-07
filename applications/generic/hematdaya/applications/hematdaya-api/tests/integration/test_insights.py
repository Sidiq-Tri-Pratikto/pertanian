"""Insights over seeded demo workspaces: AT-17, revisions, retirement, concurrency and notices."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import DBAPIError

from app.assets.model.models import MeasurementKind, SourceModel, SourceOrigin, TransportStatus
from app.core.database import get_session_factory
from app.measurements.dependencies import build_ingest_service
from app.measurements.model.models import ReadingInput
from app.sites.repository.sqlalchemy.repository import SqlAlchemySiteRepository
from tests.integration.conftest import execute, start_demo, summary

pytestmark = pytest.mark.integration

WEEK = {"start_date": "2026-10-19", "end_date": "2026-10-25"}


async def _insights(client: AsyncClient, session: dict, **params: str) -> dict:
    response = await client.get(
        f"/api/v1/sites/{session['site_id']}/insights", params=params or WEEK, headers=session["auth"]
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _tv_source(site_id: str) -> SourceModel:
    rows = await execute(
        "SELECT s.id FROM sources s JOIN bindings b ON b.source_id = s.id JOIN assets a ON a.id = b.asset_id"
        " WHERE a.site_id = :site AND a.name = 'TV'",
        site=UUID(site_id),
    )
    return SourceModel(
        id=rows[0][0], site_id=UUID(site_id), label="TV", origin=SourceOrigin.SIMULATED,
        measurement_kind=MeasurementKind.INTERVAL_ENERGY, cadence_seconds=3600, resolution_mwh=1000,
        transport_status=TransportStatus.NONE,
    )  # fmt: skip


async def _correct_tv_19h(site_id: str, wh: int, days: int = 7) -> None:
    """Re-send TV's 19.00 readings for the selected week with a new value, as a correction would."""
    source = await _tv_source(site_id)
    first = datetime(2026, 10, 19, 12, tzinfo=UTC)  # 19.00 WIB
    readings = [
        ReadingInput(
            value=Decimal(wh),
            unit="Wh",
            interval_start=first + timedelta(days=d),
            interval_end=first + timedelta(days=d, hours=1),
        )
        for d in range(days)
    ]
    async with get_session_factory()() as session:
        site = await SqlAlchemySiteRepository(session).lock(source.site_id)
        assert site is not None
        await build_ingest_service(session).ingest(site, source, readings, received_at=datetime.now(UTC))
        await session.commit()


async def test_household_change_is_one_observation_with_exact_evidence(client: AsyncClient) -> None:
    """
    Condition:
    - AT-17 on h-change over 19–25 Oktober.

    Expected:
    - One TV observation: 3.920 against 2.520 kWh, +1.400 kWh, 55.56%, r 0.168, threshold 0.840, policy change v1.
    """
    body = await _insights(client, await start_demo(client, "h-change"))

    assert len(body["observations"]) == 1
    insight = body["observations"][0]
    evidence = insight["evidence"]
    assert (insight["direction"], insight["revision"], insight["active"]) == ("increase", 1, True)
    assert evidence["asset"]["name"] == "TV"
    assert (evidence["current"]["mask_kwh"], evidence["baseline_kwh"], evidence["delta_kwh"]) == (
        "3.920",
        "2.520",
        "1.400",
    )
    assert (evidence["percent"], evidence["resolution_kwh"], evidence["threshold_kwh"]) == ("55.56", "0.168", "0.840")
    assert insight["policy"] == {"id": "change", "version": 1}
    assert insight["text"]["title"] == "TV naik 1,400 kWh (+55,56%)"
    assert "Penyebab perubahan belum diketahui" in insight["text"]["unknown"]
    assert len(evidence["series"]) == 7 and evidence["series"][0] == {
        "local_date": "2026-10-19",
        "comparison_kwh": "0.560",
        "reference_kwh": "0.360",
    }
    assert (body["comparable_count"], body["learning_count"]) == (4, 0)


@pytest.mark.parametrize("scenario", ["h-base", "i-base", "i-change", "h-zero"])
async def test_no_alert_is_invented(client: AsyncClient, scenario: str) -> None:
    """
    Condition:
    - Base fixtures, the industrial change without a schedule (3 kWh below 30% of 36 kWh), and all zeros.

    Expected:
    - No observation.
    """
    body = await _insights(client, await start_demo(client, scenario))

    assert body["observations"] == []


async def test_same_inputs_keep_the_revision(client: AsyncClient) -> None:
    """
    Condition:
    - The same period is evaluated twice, then read by ID.

    Expected:
    - Still revision 1; nothing new is written.
    """
    session = await start_demo(client, "h-change")
    first = (await _insights(client, session))["observations"][0]

    second = (await _insights(client, session))["observations"][0]
    detail = await client.get(f"/api/v1/insights/{first['id']}", headers=session["auth"])

    assert (second["id"], second["revision"], detail.json()["revision"]) == (first["id"], 1, 1)
    assert (await execute("SELECT count(*) FROM insight_revisions WHERE insight_id = :id", id=UUID(first["id"])))[0][
        0
    ] == 1


async def test_correction_creates_a_revision_and_keeps_the_old_one(client: AsyncClient) -> None:
    """
    Condition:
    - TV's 19.00 readings are corrected from 200 to 300 Wh, and two reads race to evaluate the change.

    Expected:
    - Exactly one revision 2 becomes current; revision 1 is superseded and stays readable unchanged.
    """
    session = await start_demo(client, "h-change")
    first = (await _insights(client, session))["observations"][0]
    await _correct_tv_19h(session["site_id"], 300)

    raced = await asyncio.gather(_insights(client, session), _insights(client, session))
    old = (await client.get(f"/api/v1/insights/{first['id']}?revision=1", headers=session["auth"])).json()

    assert {result["observations"][0]["revision"] for result in raced} == {2}
    assert raced[0]["observations"][0]["evidence"]["delta_kwh"] == "2.100"
    assert (old["revision"], old["superseded"], old["active"], old["current_revision"]) == (1, True, False, 2)
    assert old["evidence"]["delta_kwh"] == "1.400"
    assert (await execute("SELECT count(*) FROM insight_revisions WHERE insight_id = :id", id=UUID(first["id"])))[0][
        0
    ] == 2


async def test_ineligible_observation_is_retired_not_deleted(client: AsyncClient) -> None:
    """
    Condition:
    - A correction removes TV's extra use, so the observation no longer qualifies.

    Expected:
    - The next read lists nothing; reading the insight shows its last revision inactive and superseded.
    """
    session = await start_demo(client, "h-change")
    first = (await _insights(client, session))["observations"][0]
    await _correct_tv_19h(session["site_id"], 0)

    after = await _insights(client, session)
    detail = (await client.get(f"/api/v1/insights/{first['id']}", headers=session["auth"])).json()

    assert after["observations"] == []
    assert (detail["active"], detail["superseded"], detail["revision"]) == (False, True, 1)
    assert detail["evidence"]["delta_kwh"] == "1.400"


async def test_evidence_cannot_be_rewritten(client: AsyncClient) -> None:
    """
    Condition:
    - Something tries to edit a stored evidence snapshot.

    Expected:
    - The database refuses it.
    """
    session = await start_demo(client, "h-change")
    insight = (await _insights(client, session))["observations"][0]

    with pytest.raises(DBAPIError, match="immutable"):
        await execute("UPDATE insight_revisions SET evidence = '{}' WHERE insight_id = :id", id=UUID(insight["id"]))


async def test_notices_for_partial_stale_and_scope(client: AsyncClient) -> None:
    """
    Condition:
    - Learning-partial, stale-offline and scope scenarios over the week.

    Expected:
    - Partial notices name the asset and gaps, the stale Router says it is not a sign the device is off, the
      scope notice explains the refused total, and learning assets are counted without observations.
    """
    learning = await _insights(client, await start_demo(client, "h-learning-partial"))
    session = await start_demo(client, "h-stale-offline")
    stale = await _insights(client, session)
    quality = (await summary(client, session, **WEEK))["source_freshness"]
    scope = await _insights(client, await start_demo(client, "h-scope"), start_date="2026-10-25", end_date="2026-10-25")

    partial = {notice["title"]: notice["body"] for notice in learning["notices"] if notice["kind"] == "partial"}
    assert "Sebagian data belum tersedia · Pompa Air" in partial
    assert "24 Oktober 2026 – 25 Oktober 2026" in partial["Sebagian data belum tersedia · Pompa Air"]
    assert learning["learning_count"] >= 1 and learning["observations"] == []
    router = next(notice for notice in stale["notices"] if notice["kind"] == "stale")
    assert {n["id"] for n in stale["notices"] if n["kind"] == "stale"} == {
        f"stale:{source['source_id']}" for source in quality if source["state"] == "stale"
    }
    assert router["title"] == "Data belum diperbarui · Router"
    assert "25 Oktober 2026 18.00" in router["body"] and "bukan tanda perangkat mati" in router["body"]
    assert [notice["kind"] for notice in scope["notices"]][:1] == ["scope"]


async def test_foreign_insight_is_not_found(client: AsyncClient) -> None:
    """
    Condition:
    - Another session reads an insight by ID, current and frozen.

    Expected:
    - NOT_FOUND both ways.
    """
    owner, intruder = await start_demo(client, "h-change"), await start_demo(client)
    insight = (await _insights(client, owner))["observations"][0]

    for suffix in ("", "?revision=1"):
        response = await client.get(f"/api/v1/insights/{insight['id']}{suffix}", headers=intruder["auth"])
        assert response.status_code == 404
