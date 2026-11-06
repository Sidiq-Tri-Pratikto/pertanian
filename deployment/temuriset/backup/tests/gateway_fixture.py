"""Prepare and verify a synthetic document through the actual HTTP gateway."""

import argparse
import asyncio
import hashlib
import json
import ssl
from pathlib import Path
from uuid import UUID


async def run(
    phase: str, inventory: Path, origin: str | None, certificate: Path | None
) -> None:
    """Use one synthetic grant, one stranger, and an actual stored PDF."""
    from app.core.database import get_engine
    from app.main import app
    from httpx import ASGITransport, AsyncClient, TransportError
    from tests.integration.conftest import WEB_ORIGIN, _sign_up
    from tests.integration.documents.test_documents import (
        _run_worker,
        _upload,
        text_pdf,
    )

    if origin and certificate:
        kwargs = {
            "base_url": origin,
            "headers": {"Origin": origin},
            "verify": ssl.create_default_context(cafile=str(certificate)),
            "trust_env": False,
        }
    else:
        kwargs = {
            "transport": ASGITransport(app=app),
            "base_url": "http://test",
            "headers": {"Origin": WEB_ORIGIN},
        }
    try:
        async with (
            AsyncClient(**kwargs) as rani,
            AsyncClient(**kwargs) as bima,
            AsyncClient(**kwargs) as stranger,
        ):
            if origin:
                for _ in range(30):
                    try:
                        if (await rani.get("/health/ready")).status_code == 200:
                            break
                    except TransportError:
                        pass
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError("Synthetic HTTPS gateway did not become ready.")
            if phase == "seed":
                me = await _sign_up(rani, "drill-owner@example.test")
                recipient = await _sign_up(bima, "drill-recipient@example.test")
                await _sign_up(stranger, "drill-stranger@example.test")
                rani.headers["X-Acting-Party"] = me["active_party_id"]
                payload = text_pdf("Paired synthetic recovery specimen")
                uploaded = await _upload(rani, payload)
                document = str(UUID(uploaded["document_id"]))
                if origin:
                    for _ in range(45):
                        response = await rani.get(f"/api/v1/documents/{document}")
                        assert response.status_code == 200, response.status_code
                        if response.json()["versions"][0]["file_state"] == "AVAILABLE":
                            break
                        await asyncio.sleep(1)
                    else:
                        raise RuntimeError(
                            "Synthetic document did not pass the Compose worker scan."
                        )
                else:
                    await _run_worker()
                grant = await rani.post(
                    f"/api/v1/documents/{document}/grants",
                    json={
                        "acting_party_id": me["active_party_id"],
                        "version": 1,
                        "grantee_party_id": recipient["active_party_id"],
                        "purpose": "pitch",
                    },
                    headers={"Idempotency-Key": "drill-document-grant"},
                )
                assert grant.status_code == 201, grant.status_code
                inventory.write_text(
                    json.dumps(
                        {
                            "document_id": document,
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "recipient_session": bima.cookies["tr_session"],
                            "stranger_session": stranger.cookies["tr_session"],
                        }
                    ),
                    encoding="utf-8",
                )
            data = json.loads(inventory.read_text(encoding="utf-8"))
            if phase == "verify":
                bima.cookies.set("tr_session", data["recipient_session"])
                stranger.cookies.set("tr_session", data["stranger_session"])
            path = f"/api/v1/documents/{data['document_id']}/versions/1/content"
            allowed = await bima.get(path)
            denied = await stranger.get(path)
            assert allowed.status_code == 200, allowed.status_code
            assert hashlib.sha256(allowed.content).hexdigest() == data["sha256"]
            assert allowed.headers["cache-control"] == "private, no-store"
            assert (
                denied.status_code == 404
                and denied.json()["error"]["code"] == "NOT_FOUND"
            )
            print(
                json.dumps(
                    {
                        "phase": phase,
                        "authorized": 200,
                        "ungranted": 404,
                        "document_sha256": data["sha256"],
                    }
                )
            )
    finally:
        if not origin:
            await get_engine().dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("seed", "verify"))
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--origin")
    parser.add_argument("--certificate", type=Path)
    args = parser.parse_args()
    if bool(args.origin) != bool(args.certificate):
        parser.error("Supply both --origin and --certificate for a Compose fixture.")
    asyncio.run(run(args.phase, args.inventory, args.origin, args.certificate))
