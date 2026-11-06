"""Preflight and the template brief through HTTP against Postgres (spec 022)."""

import asyncio
import hashlib
import json
import logging
from collections.abc import Awaitable, Callable

import pytest
from httpx import AsyncClient, ConnectError, MockTransport, ReadTimeout, Request, Response
from pydantic import SecretStr
from sqlalchemy import text

from app.briefs.model.schema import SummaryProvenance
from app.briefs.router import get_summarizer
from app.briefs.service import summarizer_service
from app.briefs.service.service import REDACTED
from app.briefs.service.summarizer_service import SummaryCandidate
from app.capabilities.service.configuration import validate_configuration
from app.core.database import get_session_factory
from app.core.security import SESSION_COOKIE
from app.core.settings import get_settings
from app.main import app
from tests.factories.moderation import grant_operator, suspend_listing
from tests.integration.conftest import SignUp
from tests.integration.matching.conftest import World
from tests.integration.pitches.conftest import client_of, preflight

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_f01_to_a1_shows_exactly_what_would_be_sent(world: World) -> None:
    """
    Condition:
    - Rani preflights F01 against A1 (scenario 1).

    Expected:
    - Ready, Mitra A as recipient and Rani as sender, version pins, the test report as one shareable file, and a
      brief built only from supplied facts, each sentence with references; the private note never appears.
    """
    checked = await preflight(world, "F01", "A1")

    assert checked["readiness"] == "READY_TO_SUBMIT"
    assert (checked["recipient"]["name"], checked["sender"]["name"]) == ("Mitra A", "Rani")
    assert (checked["opportunity"]["version"], checked["source"]["version"]) == (1, 2)
    assert [(item["title"], item["version"], item["fact_keys"]) for item in checked["shareable_files"]] == [
        ("Laporan uji fungsi ClearSpring", 1, ["function"])
    ]
    assert checked["duplicate_pitch_id"] is None
    lines = checked["brief"]["text"].splitlines()
    assert lines[0] == "Masalah: Keluarga tanpa akses air bersih perlu cara menyaring air yang mudah dirawat."
    assert "Saat ini: Kapasitas saring 10 L/jam." in lines
    assert "Direncanakan: Kapasitas saring 20 L/jam." in lines
    assert "Dukungan yang diminta: Validasi prototipe enam bulan." in lines
    assert "Kebutuhan USD 20.000–30.000, total 6 bulan untuk biaya pilot enam bulan." in lines
    assert any(line.startswith("Relevansi: Validasi prototipe enam bulan.") for line in lines)
    assert any(line.startswith("Belum selesai: Sertifikat komersialisasi.") for line in lines)
    assert lines[-1] == "Tim: Rani (pembuat)."
    assert all(sentence["refs"] for sentence in checked["brief"]["sentences"])
    assert "harga bahan rahasia 7731" not in str(checked)
    assert "7731" not in checked["brief"]["text"]
    assert checked["brief"]["summarizer"] == "off"


async def test_not_ready_preflights_are_returned(world: World) -> None:
    """
    Condition:
    - Dewi preflights F02 against A2, whose authority requirement is unknown.

    Expected:
    - ``NEEDS_INFORMATION`` with the gap, a template brief, and no shareable file.
    """
    checked = await preflight(world, "F02", "A2")

    assert checked["readiness"] == "NEEDS_INFORMATION"
    assert checked["gap"]["label"] == "Wewenang atas inovasi"
    assert checked["shareable_files"] == []
    assert "Kebutuhan dana belum ditentukan." in checked["brief"]["text"]


async def test_a_raise_brief_states_target_and_contribution_apart(world: World) -> None:
    """
    Condition:
    - Bima preflights FRaise01 against B1.

    Expected:
    - Both inventions' problems, and the target and per-investor contribution in one sentence apart.
    """
    checked = await preflight(world, "FRaise01", "B1")

    assert checked["readiness"] == "READY_TO_SUBMIT"
    assert [item["title"] for item in checked["inventions"]] == ["LoopMaterial", "ReFormPress"]
    assert (
        "Target Pendanaan USD 500.000 untuk satu perusahaan; kontribusi yang diinginkan USD 50.000–100.000 per "
        "investor." in checked["brief"]["text"]
    )
    assert "Masalah (LoopMaterial): Kemasan sekali pakai sulit didaur ulang." in checked["brief"]["text"]


async def test_nobody_preflights_another_partys_source_or_their_own_mandate(world: World) -> None:
    """
    Condition:
    - Galih preflights Rani's need; Peserta P preflights against Mitra A's own opportunity with nothing.

    Expected:
    - NOT_FOUND, with nothing about F01 in the answer.
    """
    galih, party = client_of(world, "F03")
    response = await galih.post(
        "/api/v1/pitches/preflight",
        json={
            "acting_party_id": party,
            "source_type": "SUPPORT_REQUEST",
            "source_id": world.inventors.support_requests["F01"],
            "opportunity_id": world.opportunity("A1"),
        },
    )

    assert response.status_code == 404
    assert "ClearSpring" not in response.text


class FakeSummarizer:
    """Synthetic provider that records the exact input it received."""

    name = "synthetic"
    provenance = SummaryProvenance(model_id="test-model", model_version="test-v1", prompt_version="test-prompt-v1")

    def __init__(self, respond: Callable[[tuple[SummaryCandidate, ...]], Awaitable[object]]) -> None:
        self.calls: list[tuple[SummaryCandidate, ...]] = []
        self.respond = respond

    async def summarize(self, candidates: tuple[SummaryCandidate, ...]) -> object:
        self.calls.append(candidates)
        return await self.respond(candidates)


def _inject(monkeypatch: pytest.MonkeyPatch, fake: FakeSummarizer) -> None:
    monkeypatch.setitem(app.dependency_overrides, get_summarizer, lambda: fake)


async def _change(sql: str, identifier: str) -> None:
    async with get_session_factory()() as session, session.begin():
        await session.execute(text(sql), {"id": identifier})


async def test_summary_is_off_by_default_and_keeps_the_template(world: World) -> None:
    """
    Condition:
    - A summary is requested with the default adapter.

    Expected:
    - The unchanged, editable template comes back with off status.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert response.status_code == 200
    assert response.json() == checked["brief"]
    assert response.json()["summarizer_status"] == "off"


@pytest.fixture
def local_relay(monkeypatch: pytest.MonkeyPatch) -> Callable[[Callable[[Request], Response]], None]:
    """Configure the real route and substitute only the relay's HTTP transport."""
    settings = get_settings()
    monkeypatch.setattr(settings, "summary_adapter", "local-relay")
    monkeypatch.setattr(settings, "summary_relay_url", SecretStr("http://127.0.0.1:54321/select"))
    monkeypatch.setattr(settings, "summary_model_id", "synthetic-selector")
    monkeypatch.setattr(settings, "summary_model_version", "model-v2")
    monkeypatch.setattr(settings, "summary_prompt_version", "prompt-v3")
    validate_configuration(settings)

    def connect(handler: Callable[[Request], Response]) -> None:
        def client(**kwargs: object) -> AsyncClient:
            assert kwargs.get("trust_env") is False
            assert kwargs.get("follow_redirects") is False
            return AsyncClient(
                transport=MockTransport(handler),
                trust_env=False,
                follow_redirects=False,
            )

        monkeypatch.setattr(summarizer_service, "AsyncClient", client)

    return connect


async def test_configured_relay_receives_only_authorized_candidates(
    world: World, local_relay: Callable[[Callable[[Request], Response]], None]
) -> None:
    """
    Condition:
    - The local relay selects one candidate from a brief after the supporting file is revoked.

    Expected:
    - The route publishes local availability, excludes the revoked sentence and sends only opaque IDs and text.
    - The response contains the original sentence, original references and trusted configured provenance.
    - The brief stored for manual editing remains unchanged.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    galih, _ = client_of(world, "F03")
    path = f"/api/v1/briefs/{checked['brief']['id']}"
    version_id = checked["shareable_files"][0]["version_id"]
    await _change("UPDATE document_versions SET file_state = 'REJECTED' WHERE id = :id", version_id)
    observed = []

    def select(request: Request) -> Response:
        assert request.method == "POST"
        assert str(request.url) == "http://127.0.0.1:54321/select"
        assert "cookie" not in request.headers and "authorization" not in request.headers
        assert request.headers["content-type"] == "application/json"
        payload = json.loads(request.content)
        assert set(payload) == {"candidates"}
        candidates = payload["candidates"]
        assert all(set(item) == {"id", "text"} for item in candidates)
        assert all(len(item["id"]) == 32 for item in candidates)
        assert version_id not in request.content.decode()
        assert "Laporan uji fungsi ClearSpring" not in request.content.decode()
        observed.extend(candidates)
        return Response(200, json={"sentence_ids": [candidates[0]["id"]]})

    local_relay(select)
    manifest = await rani.get("/api/v1/capabilities")
    adapter = next(item for item in manifest.json()["adapters"] if item["id"] == "ai-summary")
    assert adapter == {"id": "ai-summary", "implementation": "local-relay", "status": "available"}
    assert "54321" not in manifest.text and "synthetic-selector" not in manifest.text

    denied = await galih.post(f"{path}/summary")
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "NOT_FOUND"
    assert observed == []
    response = await rani.post(f"{path}/summary")
    assert response.status_code == 200
    assert observed[0]["text"] == checked["brief"]["sentences"][0]["text"]
    assert response.json()["sentences"] == checked["brief"]["sentences"][:1]
    assert response.json()["summarizer_status"] == "used"
    assert response.json()["summarizer_provenance"] == {
        "model_id": "synthetic-selector",
        "model_version": "model-v2",
        "prompt_version": "prompt-v3",
    }
    assert (await rani.get(path)).json() == checked["brief"]


@pytest.mark.parametrize(
    ("failure", "status", "attempts"),
    [
        ("connect", "unavailable", 2),
        ("timeout", "unavailable", 2),
        ("redirect", "unavailable", 1),
        ("rate-limit", "unavailable", 1),
        ("malformed", "refused", 1),
        ("duplicate-key", "refused", 1),
        ("oversized", "refused", 1),
    ],
)
async def test_relay_failure_is_bounded_and_diagnostics_exclude_wire_content(
    world: World,
    local_relay: Callable[[Callable[[Request], Response]], None],
    caplog: pytest.LogCaptureFixture,
    failure: str,
    status: str,
    attempts: int,
) -> None:
    """
    Condition:
    - The local relay fails or violates the response contract.

    Expected:
    - Only connection failure retries, once with new opaque IDs.
    - The template is preserved and exactly one safe terminal record matches the response reference.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    marker = "fake-confidential-relay-payload-4719"
    candidate_ids = []
    caplog.set_level(logging.DEBUG)

    def broken(request: Request) -> Response:
        candidate_ids.append({item["id"] for item in json.loads(request.content)["candidates"]})
        if failure == "connect":
            raise ConnectError(marker, request=request)
        if failure == "timeout":
            raise ReadTimeout(marker, request=request)
        if failure == "redirect":
            return Response(302, headers={"Location": f"https://example.invalid/{marker}"})
        if failure == "rate-limit":
            return Response(429, text=marker, extensions={"reason_phrase": marker.encode()})
        if failure == "duplicate-key":
            identifier = next(iter(candidate_ids[-1]))
            return Response(
                200,
                content=f'{{"sentence_ids":[],"sentence_ids":["{identifier}"]}}',
                headers={"content-type": "application/json"},
            )
        content = marker.encode()
        if failure == "oversized":
            content = json.dumps({"sentence_ids": [next(iter(candidate_ids[-1]))]}).encode() + b" " * 16384
        return Response(200, content=content, headers={"content-type": "application/json"})

    local_relay(broken)
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")
    assert response.status_code == 200
    result = response.json()
    assert result["text"] == checked["brief"]["text"]
    assert result["summarizer_status"] == status
    assert result["summarizer_provenance"] is None
    assert len(candidate_ids) == attempts
    if attempts == 2:
        assert candidate_ids[0].isdisjoint(candidate_ids[1])
    error = result["summarizer_error"]
    assert error["code"] == f"SUMMARY_{status.upper()}"
    assert error["recovery"]["retryable"] is False
    expected = "Ringkasan otomatis tidak tersedia" if status == "unavailable" else "Ringkasan otomatis ditolak"
    assert error["message"] == f"{expected}. Lanjutkan dengan menyunting brief."
    assert caplog.text.count(error["request_id"]) == 1
    assert f"APP-SUMMARY-{status.upper()}" in caplog.text
    assert marker not in response.text + caplog.text


async def test_summary_returns_only_selected_sentences_with_trusted_provenance(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - The provider selects two sentences in reverse order.

    Expected:
    - The route returns exact text and references in template order, with trusted provenance. The stored brief stays.
    """

    async def select(candidates: tuple[SummaryCandidate, ...]) -> object:
        return {"sentence_ids": [candidates[-1].id, candidates[0].id]}

    fake = FakeSummarizer(select)
    _inject(monkeypatch, fake)
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    path = f"/api/v1/briefs/{checked['brief']['id']}"
    response = await rani.post(f"{path}/summary")

    assert response.status_code == 200
    body = response.json()
    original = checked["brief"]["sentences"]
    assert [candidate.text for candidate in fake.calls[0]] == [sentence["text"] for sentence in original]
    assert set(fake.calls[0][0].__slots__) == {"id", "text"}
    assert body["summarizer_status"] == "used"
    assert body["summarizer"] == "synthetic"
    assert body["summarizer_provenance"] == fake.provenance.model_dump()
    assert body["sentences"] == [original[0], original[-1]]
    assert body["text"] == "\n".join([original[0]["text"], original[-1]["text"]])
    assert (await rani.get(path)).json() == checked["brief"]


@pytest.mark.parametrize("lost", ["before", "during", "retry"])
async def test_summary_rechecks_document_access(world: World, monkeypatch: pytest.MonkeyPatch, lost: str) -> None:
    """
    Condition:
    - The brief references another party's file, or a file becomes unavailable during or between attempts.

    Expected:
    - The first case excludes the sentence. In-flight loss refuses the suggestion and redacts the fallback.
      A retry sees fresh permissions and opaque IDs, and only sends authorized facts.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    path = f"/api/v1/briefs/{checked['brief']['id']}/summary"
    report = "Laporan uji fungsi ClearSpring"
    version_id = checked["shareable_files"][0]["version_id"]
    calls = 0

    async def lose_document() -> None:
        await _change("UPDATE document_versions SET file_state = 'REJECTED' WHERE id = :id", version_id)

    async def select(candidates: tuple[SummaryCandidate, ...]) -> object:
        nonlocal calls
        calls += 1
        if lost == "before" or calls == 2:
            assert all(report not in candidate.text for candidate in candidates)
            return {"sentence_ids": [candidates[0].id]}
        document = next(candidate for candidate in candidates if report in candidate.text)
        await lose_document()
        if lost == "retry":
            raise ConnectionError
        return {"sentence_ids": [document.id]}

    fake = FakeSummarizer(select)
    _inject(monkeypatch, fake)
    if lost == "before":
        await _change(
            "UPDATE documents SET owner_party_id = "
            "(SELECT id FROM parties WHERE id <> documents.owner_party_id LIMIT 1) "
            "WHERE id = :id",
            checked["shareable_files"][0]["document_id"],
        )
    response = await rani.post(path)

    assert response.status_code == 200
    assert report not in response.text
    assert version_id not in response.text
    if lost == "during":
        assert response.json()["summarizer_status"] == "refused"
        assert response.json()["summarizer_error"]["code"] == "SUMMARY_REFUSED"
        assert {"text": REDACTED, "refs": []} in response.json()["sentences"]
    else:
        assert response.json()["summarizer_status"] == "used"
    assert calls == (2 if lost == "retry" else 1)
    if lost == "retry":
        assert {item.id for item in fake.calls[0]}.isdisjoint(item.id for item in fake.calls[1])


@pytest.mark.parametrize(
    ("query", "key"),
    [
        ("UPDATE preflights SET expires_at = NOW() WHERE id = :id", "preflight"),
        ("UPDATE support_requests SET version = version + 1 WHERE id = :id", "source"),
        ("UPDATE opportunities SET status = 'DRAFT' WHERE id = :id", "opportunity"),
    ],
)
async def test_expired_or_stale_pins_never_reach_the_provider(
    world: World, monkeypatch: pytest.MonkeyPatch, query: str, key: str
) -> None:
    """
    Condition:
    - The preflight expires, its source changes, or its target becomes private.

    Expected:
    - The adapter receives no candidates and the fallback shows only still-authorized facts.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    identifier = checked["preflight_id"] if key == "preflight" else checked[key]["id"]
    await _change(query, identifier)

    async def select(candidates: tuple[SummaryCandidate, ...]) -> object:
        return {"sentence_ids": [candidates[0].id]}

    fake = FakeSummarizer(select)
    _inject(monkeypatch, fake)
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert response.status_code == 200
    assert response.json()["summarizer_status"] == "refused"
    assert fake.calls == []
    if key == "opportunity":
        assert checked["opportunity"]["version_id"] not in response.text
        assert all(sentence["refs"] == [] for sentence in response.json()["sentences"])


@pytest.mark.parametrize("suspend_during_request", [False, True])
async def test_suspended_invention_cannot_supply_an_automatic_summary(
    world: World, client: AsyncClient, sign_up: SignUp, monkeypatch: pytest.MonkeyPatch, suspend_during_request: bool
) -> None:
    """Withhold a suspended source from the adapter and discard results if suspension happens during selection."""
    checked = await preflight(world, "F01", "A1")
    sender, _ = client_of(world, "F01")
    operator_party = await grant_operator(client, sign_up)
    invention = world.inventors.inventions["F01"]

    if not suspend_during_request:
        await suspend_listing(client, operator_party, "INVENTION", invention)

    async def select(candidates: tuple[SummaryCandidate, ...]) -> object:
        await suspend_listing(client, operator_party, "INVENTION", invention)
        return {"sentence_ids": [candidates[0].id]}

    fake = FakeSummarizer(select)
    _inject(monkeypatch, fake)
    response = await sender.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert response.status_code == 200, response.text
    assert response.json()["summarizer_status"] == "refused"
    assert all(sentence["refs"] == [] for sentence in response.json()["sentences"])
    assert "ClearSpring" not in response.text
    assert len(fake.calls) == int(suspend_during_request)


async def test_revoked_session_cannot_receive_a_summary_or_its_template(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Condition:
    - The signed-in session is revoked during the provider call.

    Expected:
    - The request loses authentication and receives no brief facts.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    token = rani.cookies[SESSION_COOKIE]

    async def revoke(candidates: tuple[SummaryCandidate, ...]) -> object:
        await _change(
            "UPDATE sessions SET revoked_at = NOW() WHERE token_sha256 = :id",
            hashlib.sha256(token.encode()).hexdigest(),
        )
        return {"sentence_ids": [candidates[0].id]}

    _inject(monkeypatch, FakeSummarizer(revoke))
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert "Kapasitas" not in response.text


@pytest.mark.parametrize(
    ("failure", "status", "code", "attempts"),
    [
        ("timeout", "unavailable", "SUMMARY_UNAVAILABLE", 2),
        ("unexpected", "unavailable", "SUMMARY_UNAVAILABLE", 1),
        ("malformed", "refused", "SUMMARY_REFUSED", 1),
    ],
)
async def test_terminal_summary_failure_is_safe_and_keeps_the_editable_template(
    world: World,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure: str,
    status: str,
    code: str,
    attempts: int,
) -> None:
    """
    Condition:
    - An adapter times out, raises an unexpected error, or returns untrusted text.

    Expected:
    - Only the transient timeout retries, and once. The safe error resolves to one privacy-safe record.
    """
    confidential = "confidential-invention-measurement-9938"

    async def broken(candidates: tuple[SummaryCandidate, ...]) -> object:
        if failure == "timeout":
            await asyncio.Event().wait()
        if failure == "unexpected":
            raise ValueError(confidential)
        return {"sentence_ids": [candidates[0].id], "text": confidential}

    fake = FakeSummarizer(broken)
    _inject(monkeypatch, fake)
    monkeypatch.setattr(summarizer_service, "SUMMARY_ATTEMPT_TIMEOUT_SECONDS", 0.01)
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == checked["brief"]["text"]
    assert body["summarizer_status"] == status
    assert body["summarizer_provenance"] is None
    assert len(fake.calls) == attempts
    error = body["summarizer_error"]
    assert error["code"] == code
    expected = "Ringkasan otomatis tidak tersedia" if status == "unavailable" else "Ringkasan otomatis ditolak"
    assert error["message"] == f"{expected}. Lanjutkan dengan menyunting brief."
    assert error["recovery"]["retryable"] is False
    assert caplog.text.count(error["request_id"]) == 1
    assert f"APP-{code.replace('_', '-')}" in caplog.text
    assert confidential not in response.text + caplog.text
    assert "Laporan uji fungsi ClearSpring" not in caplog.text


async def test_export_follows_todays_access_and_redacts_what_depends_on_a_lost_file(world: World) -> None:
    """
    Condition:
    - Rani exports her brief, then the test report stops being available, then she exports again (AC36, US2).

    Expected:
    - The first export names its source versions and includes the report sentence; the second redacts exactly
      that sentence with a label; another party cannot export it.
    """
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    path = f"/api/v1/briefs/{checked['brief']['id']}/export"
    before = await rani.get(path, params={"format": "md"})
    version_id = checked["shareable_files"][0]["version_id"]
    async with get_session_factory()() as session, session.begin():
        await session.execute(
            text("UPDATE document_versions SET file_state = 'REJECTED' WHERE id = :id"), {"id": version_id}
        )
    after = await rani.get(path, params={"format": "txt"})
    stranger = await world.inventors.clients["galih"].get(path)

    assert before.headers["content-type"].startswith("text/markdown")
    assert "_Sumber: SUPPORT_REQUEST versi 2; mandat Validasi prototipe enam bulan versi 1_" in before.text
    assert "- Saat ini: Laporan uji fungsi Laporan uji fungsi ClearSpring." in before.text
    assert "Laporan uji fungsi ClearSpring" not in after.text
    assert after.text.count(REDACTED) == 1
    assert "Saat ini: Kapasitas saring 10 L/jam." in after.text
    assert stranger.status_code == 404


@pytest.mark.parametrize("kind", ["INVENTION", "OPPORTUNITY", "PARTNER_PROFILE"])
async def test_suspended_listings_do_not_prepare_new_pitches_or_matches(
    world: World, client: AsyncClient, sign_up: SignUp, kind: str
) -> None:
    """
    Condition:
    - A source invention, target mandate or target partner is suspended.

    Expected:
    - New preflight is refused. New matching refuses the source or omits suspended targets.
    """
    party = await grant_operator(client, sign_up)
    subject = {
        "INVENTION": world.inventors.inventions["F01"],
        "OPPORTUNITY": world.opportunity("A1"),
        "PARTNER_PROFILE": world.recipients.parties["A"],
    }[kind]
    await suspend_listing(client, party, kind, subject)
    sender, sender_party = client_of(world, "F01")
    response = await sender.post(
        "/api/v1/pitches/preflight",
        json={
            "acting_party_id": sender_party,
            "source_type": "SUPPORT_REQUEST",
            "source_id": world.inventors.support_requests["F01"],
            "opportunity_id": world.opportunity("A1"),
        },
    )
    code = "LISTING_SUSPENDED" if kind == "INVENTION" else "NOT_FOUND"
    assert response.json()["error"]["code"] == code, response.text
    match = await world.match("rani", "SUPPORT_REQUEST", world.inventors.support_requests["F01"])
    if kind == "INVENTION":
        assert match.json()["error"]["code"] == code, match.text
    else:
        assert match.status_code == 201, match.text
        shown = {item["opportunity_id"] for item in match.json()["results"] + match.json()["excluded"]}
        assert world.opportunity("A1") not in shown
        assert (world.opportunity("A2") in shown) == (kind == "OPPORTUNITY")
