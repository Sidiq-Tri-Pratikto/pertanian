"""Frozen match breakdown on pitch submission and resubmission (spec 057, AC79)."""

from collections.abc import Awaitable, Callable

import pytest

from tests.integration.matching.conftest import World

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("clean_tables")]


async def test_pitch_submission_freezes_match_breakdown_across_resubmission(
    world: World, make_world: Callable[..., Awaitable[World]]
) -> None:
    """
    Condition:
    - Rani submits F01 to Mitra A (A1), Mitra A requests a revision, Rani answers and resubmits after editing F01.

    Expected:
    - Submission 1 keeps the breakdown frozen at submission 1, and submission 2 freezes the recomputed breakdown.
    """
    rani = world.inventors.clients["rani"]
    rani_party = world.inventors.parties["rani"]
    mitra_a = world.recipients.clients["A"]
    mitra_party = world.recipients.parties["A"]
    support_id = world.inventors.support_requests["F01"]
    opp_id = world.opportunity("A1")

    preflight = await rani.post(
        "/api/v1/pitches/preflight",
        json={
            "acting_party_id": rani_party,
            "source_type": "SUPPORT_REQUEST",
            "source_id": support_id,
            "opportunity_id": opp_id,
        },
    )
    assert preflight.status_code == 200, preflight.text
    pf = preflight.json()
    files = [{"document_id": f["document_id"], "version": f["version"]} for f in pf["shareable_files"]]

    submitted = await rani.post(
        "/api/v1/pitches",
        json={
            "acting_party_id": rani_party,
            "preflight_token": pf["token"],
            "brief": pf["brief"]["text"],
            "files": files,
        },
        headers={"Idempotency-Key": "submit-057"},
    )
    assert submitted.status_code == 201, submitted.text
    pitch_id = submitted.json()["pitch_id"]

    recipient_view = (await mitra_a.get(f"/api/v1/pitches/{pitch_id}")).json()
    sub1_match = recipient_view["submissions"][0]["snapshot"]["match"]
    assert sub1_match["label"] == "Kecocokan kuat"
    assert len(sub1_match["breakdown"]) == 8
    assert [d["id"] for d in sub1_match["breakdown"]] == [
        "sector",
        "topic",
        "readiness",
        "money",
        "form",
        "requirements",
        "evidence",
        "availability",
    ]
    assert "recommendations" not in sub1_match

    # Request a revision, then change F01's budget so money drops to partial (50) on resubmission.
    rev = await mitra_a.post(
        f"/api/v1/pitches/{pitch_id}/revision-rounds",
        json={
            "acting_party_id": mitra_party,
            "expected_version": recipient_view["version"],
            "submission": 1,
            "items": [
                {
                    "category": "Anggaran",
                    "question": "Apakah menerima dukungan sebagian?",
                    "reason": "Perlu kejelasan ruang lingkup.",
                    "required": True,
                }
            ],
        },
        headers={"Idempotency-Key": "rev-057"},
    )
    assert rev.status_code == 201, rev.text
    after_rev = (await rani.get(f"/api/v1/pitches/{pitch_id}")).json()
    item_id = after_rev["rounds"][0]["items"][0]["id"]

    ans = await rani.put(
        f"/api/v1/pitches/{pitch_id}/revision-items/{item_id}/answer",
        json={
            "acting_party_id": rani_party,
            "expected_version": None,
            "response": "CAN",
            "text": "Kami sesuaikan kisaran biaya.",
            "files": [],
        },
    )
    assert ans.status_code == 200, ans.text

    current_need = (await rani.get(f"/api/v1/support-requests/{support_id}")).json()
    updated_budget = {
        **current_need["budget"],
        "min": "50000",
        "max": "60000",
    }
    saved_need = await rani.put(
        f"/api/v1/support-requests/{support_id}",
        json={
            "acting_party_id": rani_party,
            "expected_version": current_need["version"],
            "outcome": current_need["outcome"],
            "support_forms": current_need["support_forms"],
            "relationship_form": current_need["relationship_form"],
            "scope": current_need["scope"],
            "months": current_need["months"],
            "region": current_need["region"],
            "accepts_partial": True,
            "accepts_noncash": current_need["accepts_noncash"],
            "noncash_description": current_need["noncash_description"],
            "budget": updated_budget,
        },
        headers={"Idempotency-Key": "need-057"},
    )
    assert saved_need.status_code == 200, saved_need.text

    resub = await rani.post(
        f"/api/v1/pitches/{pitch_id}/resubmit",
        json={
            "acting_party_id": rani_party,
            "expected_version": after_rev["version"],
            "brief": pf["brief"]["text"],
            "files": files,
        },
        headers={"Idempotency-Key": "resub-057"},
    )
    assert resub.status_code == 200, resub.text

    final_view = (await mitra_a.get(f"/api/v1/pitches/{pitch_id}")).json()
    assert len(final_view["submissions"]) == 2
    sub1_money = next(d for d in final_view["submissions"][0]["snapshot"]["match"]["breakdown"] if d["id"] == "money")
    sub2_money = next(d for d in final_view["submissions"][1]["snapshot"]["match"]["breakdown"] if d["id"] == "money")
    assert sub1_money["score"] == 100
    assert sub2_money["score"] == 50


async def test_investor_invention_fit_preview_reads_public_only_and_hides_drafts(world: World) -> None:
    """
    Condition:
    - Mitra A previews fit for F01 (published) and for a draft invention of Rani; Rani also checks her own invention.

    Expected:
    - Mitra A gets one preview result per own active mandate with money and form UNKNOWN;
      draft returns 404; own invention returns [].
    """
    mitra_a = world.recipients.clients["A"]
    rani = world.inventors.clients["rani"]
    rani_party = world.inventors.parties["rani"]

    preview = await mitra_a.get(f"/api/v1/inventions/{world.inventors.inventions['F01']}/fit")
    assert preview.status_code == 200, preview.text
    items = preview.json()
    assert len(items) == 3  # A1, A2, A3
    a1 = next(item for item in items if item["opportunity_id"] == world.opportunity("A1"))
    dims = {d["id"]: d for d in a1["breakdown"]}
    assert dims["money"]["score"] is None and dims["money"]["status"] == "UNKNOWN"
    assert dims["form"]["score"] is None and dims["form"]["status"] == "UNKNOWN"
    assert dims["sector"]["score"] == 100

    # Own invention returns empty list (no self-matching).
    own = await rani.get(f"/api/v1/inventions/{world.inventors.inventions['F01']}/fit")
    assert own.status_code == 200 and own.json() == []

    # Draft invention is 404 to another party.
    draft = (
        await rani.post(
            "/api/v1/inventions", json={"acting_party_id": rani_party}, headers={"Idempotency-Key": "draft-057"}
        )
    ).json()
    hidden = await mitra_a.get(f"/api/v1/inventions/{draft['id']}/fit")
    assert hidden.status_code == 404
