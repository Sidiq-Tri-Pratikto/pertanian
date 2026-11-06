"""Preflight and the template brief through HTTP against Postgres (spec 022)."""

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.briefs.service.service import REDACTED, OffSummarizer
from app.core.database import get_session_factory
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
    assert "7731" not in str(checked)
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


@pytest.mark.parametrize(
    ("summary", "status"),
    [
        (None, "off"),
        ("Kapasitas saring 10 L/jam saat ini.", "used"),
        ("Sertifikat SNI sudah terbit dan omzet 900 juta.", "refused"),
    ],
)
async def test_a_summary_is_used_only_when_every_claim_is_traceable(
    world: World, monkeypatch: pytest.MonkeyPatch, summary: str | None, status: str
) -> None:
    """
    Condition:
    - The summarizer is off, returns a traceable summary, or returns claims not in the facts (AC35, AC68).

    Expected:
    - Off and refused keep the template; only a traceable summary is used.
    """

    async def fake(self: Any, sentences: list[dict[str, Any]]) -> str | None:  # noqa: ARG001
        return summary

    monkeypatch.setattr(OffSummarizer, "summarize", fake)
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert response.json()["summarizer_status"] == status
    expected = summary if status == "used" else checked["brief"]["text"]
    assert response.json()["text"] == expected


async def test_a_failing_summarizer_keeps_the_template(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Condition:
    - The summarizer raises (AC35).

    Expected:
    - The template brief comes back, status ``off``.
    """

    async def broken(self: Any, sentences: list[dict[str, Any]]) -> str | None:  # noqa: ARG001
        raise TimeoutError

    monkeypatch.setattr(OffSummarizer, "summarize", broken)
    checked = await preflight(world, "F01", "A1")
    rani, _ = client_of(world, "F01")
    response = await rani.post(f"/api/v1/briefs/{checked['brief']['id']}/summary")

    assert (response.json()["summarizer_status"], response.json()["text"]) == ("off", checked["brief"]["text"])


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
