"""Fixtures for matching: Recipients A–E and inventors F01–F06, loaded through the API."""

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import pytest
from httpx import AsyncClient

from tests.factories.inventors import LoadedInventors, load_inventors
from tests.factories.recipients import LoadedRecipients, load_recipients


@dataclass
class World:
    """Both sides of the fixtures.

    Attributes:
        recipients (LoadedRecipients): Partners and opportunities.
        inventors (LoadedInventors): Inventions, needs and the raise.
    """

    recipients: LoadedRecipients
    inventors: LoadedInventors

    async def match(self, account: str, source_type: str, source_id: str, key: str = "m") -> Any:
        """Run matching as an inventor account."""
        client = self.inventors.clients[account]
        return await client.post(
            "/api/v1/matches",
            json={
                "acting_party_id": self.inventors.parties[account],
                "source_type": source_type,
                "source_id": source_id,
            },
            headers={"Idempotency-Key": f"{key}-{source_id}"},
        )

    async def support(self, fixture: str, key: str = "m") -> dict[str, Any]:
        """Match a fixture's support request and return the run."""
        from tests.factories.inventors import INVENTIONS  # noqa: PLC0415

        response = await self.match(
            INVENTIONS[fixture]["account"], "SUPPORT_REQUEST", self.inventors.support_requests[fixture], key
        )
        assert response.status_code == 201, response.text
        return response.json()

    async def funding(self, key: str = "m") -> dict[str, Any]:
        """Match FRaise01 and return the run."""
        response = await self.match("bima", "FUNDING_REQUEST", self.inventors.funding, key)
        assert response.status_code == 201, response.text
        return response.json()

    def opportunity(self, key: str) -> str:
        """Opportunity id of a target such as ``A1``."""
        return self.recipients.opportunities[key]


def result_for(run: dict[str, Any], opportunity_id: str) -> dict[str, Any]:
    """Find a target's result, shown or excluded."""
    return next(item for item in run["results"] + run["excluded"] if item["opportunity_id"] == opportunity_id)


def row(result: dict[str, Any], label: str) -> dict[str, Any]:
    """Find a requirement row by label."""
    return next(item for item in result["rows"] if item["label"] == label)


async def _world(
    new_client: Callable[[], AsyncClient], sign_up: Callable[..., Awaitable[dict]], **variants: bool
) -> World:
    recipients = await load_recipients(new_client, sign_up)
    inventors = await load_inventors(new_client, sign_up, **variants)
    return World(recipients, inventors)


@pytest.fixture
async def world(new_client: Callable[[], AsyncClient], sign_up) -> AsyncIterator[World]:
    """The baseline fixtures."""
    loaded = await _world(new_client, sign_up)
    yield loaded
    await loaded.recipients.close()
    await loaded.inventors.close()


@pytest.fixture
def make_world(new_client: Callable[[], AsyncClient], sign_up) -> Callable[..., Awaitable[World]]:
    """Load the fixtures with variants, such as ``gap=True``. The caller closes the clients."""
    return lambda **variants: _world(new_client, sign_up, **variants)
