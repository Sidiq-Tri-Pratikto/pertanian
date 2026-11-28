"""Engine inputs carry TKT and mandate minimum TKT without changing scores yet (spec 055, US3)."""

from dataclasses import replace
from uuid import uuid4

from app.intake.model.schema import OpportunityResponse, TargetAvailabilityResponse
from app.matching.engine.evaluate import evaluate
from app.matching.service.service import _invention_fields, target_of
from app.portfolio.model.schema import InventionVersionResponse, ReadinessResponse
from tests.unit.matching.builders import support, target


def _version(tkt_level: int | None) -> InventionVersionResponse:
    return InventionVersionResponse(
        number=1,
        state="published",
        title="Contoh",
        summary="Ringkasan",
        problem="Masalah",
        solution="Solusi",
        intended_users="Pengguna",
        sector="Air bersih",
        stage="PROTOTYPE",
        keywords=["air"],
        facts=[],
        claims=[],
        private_notes="",
        published_at=None,
        readiness=(
            ReadinessResponse(tkt_level=tkt_level, note="", has_evidence=False) if tkt_level is not None else None
        ),
    )


def test_invention_fields_picks_lowest_stated_tkt_or_none() -> None:
    """Single invention carries its TKT; multiple linked inventions pick the lowest stated TKT; none gives None."""
    assert _invention_fields([_version(6)])["tkt"] == 6
    assert _invention_fields([_version(7), _version(4), _version(None)])["tkt"] == 4
    assert _invention_fields([_version(None), _version(None)])["tkt"] is None
    assert _invention_fields([])["tkt"] is None


def test_target_of_carries_min_tkt() -> None:
    """Target.min_tkt reflects OpportunityResponse.min_tkt (int or None)."""
    opp = OpportunityResponse(
        id=uuid4(),
        partner_party_id=uuid4(),
        version=1,
        current_version_id=uuid4(),
        kind="SPECIFIC",
        status="ACTIVE",
        closes_at=None,
        target_availability=TargetAvailabilityResponse(available=True, reason=None),
        general_intake_label=None,
        number=1,
        title="Mandat A",
        outcome="Pilot",
        included="",
        excluded="",
        support="Hibah",
        accepted_stages=["PROTOTYPE"],
        relationship_forms=["PROJECT"],
        sectors=["Air bersih"],
        keywords=["air"],
        timing="2026",
        financial=None,
        requirements=[],
        min_tkt=5,
    )
    assert target_of(opp, "Mitra A").min_tkt == 5
    assert target_of(opp.model_copy(update={"min_tkt": None}), "Mitra A").min_tkt is None


def test_tkt_fields_do_not_change_matching_scores_in_spec_055() -> None:
    """Scores remain identical whether tkt/min_tkt are set or None (057 owns scoring)."""
    base_source = support("F01")
    base_target = target("A1")
    assert base_source.tkt is None
    assert base_target.min_tkt is None
    before = evaluate(base_source, base_target)
    after = evaluate(replace(base_source, tkt=6), replace(base_target, min_tkt=5))
    assert after == before
