"""Recipients A–E from the fixtures, as plain data and as a loader through the API (spec 016, used by 019 and 021).

The data lives in ``app/demo/service/data.py`` so demo seeding (021) uses the same values.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.demo.service.data import INVESTOR_CHECK, OPPORTUNITIES, PROFILES  # noqa: F401 - re-exported for tests


@dataclass
class LoadedRecipients:
    """What ``load_recipients`` made.

    Attributes:
        parties (dict[str, str]): Party id per recipient, such as ``A``.
        opportunities (dict[str, str]): Opportunity id per target, such as ``A1``.
        clients (dict[str, Any]): A signed-in client acting for each recipient. The caller closes them.
    """

    parties: dict[str, str] = field(default_factory=dict)
    opportunities: dict[str, str] = field(default_factory=dict)
    clients: dict[str, Any] = field(default_factory=dict)

    async def close(self) -> None:
        """Close every client."""
        for client in self.clients.values():
            await client.aclose()


async def save_profile(
    client: Any,
    party_id: str,
    content: dict[str, Any],
    *,
    version: int | None = None,
    key: str = "profile",
    **extra: Any,
) -> Any:
    """Save a party's profile through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The party.
        content (dict[str, Any]): Profile content.
        version (int | None, optional): ``expected_version``. Defaults to None, for a first save.
        key (str, optional): Idempotency key. Defaults to "profile".
        **extra (Any): More body fields, such as ``intake_status``.

    Returns:
        Any: The response.
    """
    body = {"acting_party_id": party_id, "expected_version": version, **content, **extra}
    return await client.put(f"/api/v1/partners/{party_id}", json=body, headers={"Idempotency-Key": key})


async def create_opportunity(client: Any, party_id: str, content: dict[str, Any], *, key: str = "create") -> Any:
    """Start an opportunity through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The acting party.
        content (dict[str, Any]): Opportunity content, optionally with ``kind``.
        key (str, optional): Idempotency key. Defaults to "create".

    Returns:
        Any: The response.
    """
    body = {"acting_party_id": party_id, **content}
    return await client.post("/api/v1/opportunities", json=body, headers={"Idempotency-Key": key})


async def save_opportunity(
    client: Any, party_id: str, opportunity_id: str, content: dict[str, Any], version: int, *, key: str = "save"
) -> Any:
    """Save an opportunity through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The acting party.
        opportunity_id (str): The opportunity.
        content (dict[str, Any]): Opportunity content.
        version (int): ``expected_version``.
        key (str, optional): Idempotency key. Defaults to "save".

    Returns:
        Any: The response.
    """
    body = {"acting_party_id": party_id, "expected_version": version, **content}
    return await client.put(f"/api/v1/opportunities/{opportunity_id}", json=body, headers={"Idempotency-Key": key})


async def move_opportunity(
    client: Any, party_id: str, opportunity_id: str, action: str, version: int, *, key: str | None = None
) -> Any:
    """Activate, pause or close an opportunity through the API.

    Args:
        client (Any): A client acting for the party.
        party_id (str): The acting party.
        opportunity_id (str): The opportunity.
        action (str): ``activate``, ``pause`` or ``close``.
        version (int): ``expected_version``.
        key (str | None, optional): Idempotency key. Defaults to one per action and version.

    Returns:
        Any: The response.
    """
    return await client.post(
        f"/api/v1/opportunities/{opportunity_id}/{action}",
        json={"acting_party_id": party_id, "expected_version": version},
        headers={"Idempotency-Key": key or f"{opportunity_id}-{action}-{version}"},
    )


async def _party_for(client: Any, key: str, sign_up: Callable[..., Awaitable[dict]]) -> str:
    party = PROFILES[key]["party"]
    me = await sign_up(client, f"recipient-{key.lower()}@example.com", persona="mitra", name=party["name"])
    if party["kind"] == "personal":
        client.headers["X-Acting-Party"] = me["active_party_id"]
        return me["active_party_id"]
    organization = await client.post(
        "/api/v1/organizations",
        json={"name": party["name"], "kind": party["organization_kind"]},
        headers={"Idempotency-Key": f"organization-{key}"},
    )
    assert organization.status_code == 201, organization.text  # noqa: S101 - a test fixture stops on a broken setup
    party_id = organization.json()["party_id"]
    await client.put("/api/v1/me/context", json={"party_id": party_id})
    client.headers["X-Acting-Party"] = party_id
    return party_id


async def load_recipients(
    new_client: Callable[[], Any], sign_up: Callable[..., Awaitable[dict]], *, activate: bool = True
) -> LoadedRecipients:
    """Create Recipients A–E: A–D through the API, as a partner would, and E as a directory entry.

    E has no route of its own because nobody may claim a source through the API, so it goes through the service with
    an organization owned by a test operator account.

    Args:
        new_client (Callable[[], Any]): Makes a client with its own cookie jar.
        sign_up (Callable[..., Awaitable[dict]]): Signs a client up.
        activate (bool, optional): Whether to activate the opportunities. Defaults to True.

    Returns:
        LoadedRecipients: Parties, opportunities and a client per recipient.
    """
    # Imported here so that reading the plain data above needs no application or database.
    from app.core.database import get_session_factory  # noqa: PLC0415
    from app.intake.model.schema import PartnerProfileContent  # noqa: PLC0415
    from app.intake.service.service import IntakeService  # noqa: PLC0415

    loaded = LoadedRecipients()
    for key, profile in PROFILES.items():
        client = new_client()
        loaded.clients[key] = client
        party_id = await _party_for(client, key, sign_up)
        loaded.parties[key] = party_id
        if key == "E":
            async with get_session_factory()() as session, session.begin():
                content = PartnerProfileContent.model_validate(profile["content"])
                await IntakeService(session).record_directory_profile(party_id, content)
            continue
        saved = await save_profile(client, party_id, profile["content"])
        assert saved.status_code == 200, saved.text  # noqa: S101 - a test fixture stops on a broken setup
    for key, opportunity in OPPORTUNITIES.items():
        partner = opportunity["partner"]
        client, party_id = loaded.clients[partner], loaded.parties[partner]
        created = await create_opportunity(client, party_id, opportunity["content"], key=f"create-{key}")
        assert created.status_code == 201, created.text  # noqa: S101 - a test fixture stops on a broken setup
        loaded.opportunities[key] = created.json()["id"]
        if activate:
            moved = await move_opportunity(client, party_id, created.json()["id"], "activate", 1)
            assert moved.status_code == 200, moved.text  # noqa: S101 - a test fixture stops on a broken setup
    return loaded
