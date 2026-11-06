"""Recipients A–E as plain data (spec 016, SC-001)."""

import json
from typing import Any, get_args

from app.intake.model.schema import RequirementInput
from app.intake.service.requirements import validate_requirements
from app.portfolio.model.schema import Stage
from tests.factories.recipients import OPPORTUNITIES, PROFILES


def _cash_ranges() -> list[dict[str, Any]]:
    ranges = [opportunity["content"]["financial"] for opportunity in OPPORTUNITIES.values()]
    ranges += [
        profile["content"]["check_range"] for profile in PROFILES.values() if "check_range" in profile["content"]
    ]
    return [item for item in ranges if item.get("min") is not None]


def test_eight_targets_and_each_recipient_as_the_fixtures_describe_it() -> None:
    """
    Condition:
    - The plain recipient data.

    Expected:
    - Seven opportunities and directory entry E make eight targets; A has three opportunities; B is a personal party
      with a USD 50000–150000 check; E is external, with no opportunity.
    """
    assert sorted(OPPORTUNITIES) == ["A1", "A2", "A3", "B1", "B2", "C1", "D1"]
    assert sum(opportunity["partner"] == "A" for opportunity in OPPORTUNITIES.values()) == 3
    assert PROFILES["B"]["party"]["kind"] == "personal"
    check = PROFILES["B"]["content"]["check_range"]
    assert (check["min"], check["max"], check["currency"]) == ("50000.0000", "150000.0000", "USD")
    assert PROFILES["E"]["content"]["contact_route"] == "EXTERNAL"
    assert not any(opportunity["partner"] == "E" for opportunity in OPPORTUNITIES.values())


def test_every_stage_is_a_stage_value() -> None:
    """
    Condition:
    - Every stage in the profiles and opportunities.

    Expected:
    - Each is a value of ``Stage``, not the prototype's free text.
    """
    allowed = set(get_args(Stage))
    stages = [stage for profile in PROFILES.values() for stage in profile["content"]["stages"]]
    stages += [stage for item in OPPORTUNITIES.values() for stage in item["content"]["accepted_stages"]]

    assert set(stages) <= allowed


def test_unknown_is_never_stored_as_a_value() -> None:
    """
    Condition:
    - The whole data set.

    Expected:
    - No field holds the prototype's "Belum diketahui" or "Belum ditentukan" (constitution principle 7).
    """
    text = json.dumps({"profiles": PROFILES, "opportunities": OPPORTUNITIES})

    assert "Belum diketahui" not in text
    assert "Belum ditentukan" not in text


def test_every_cash_range_states_what_it_means() -> None:
    """
    Condition:
    - Every range with amounts.

    Expected:
    - Each has a subject, basis, currency and period, and a ``total_period`` range has its months (principle 8).
    """
    ranges = _cash_ranges()

    assert ranges
    for item in ranges:
        assert item["subject"] and item["basis"] and item["currency"] and item["period"]
        assert (item["basis"] == "total_period") == (item.get("months") is not None)


def test_every_requirement_passes_validation_and_keeps_its_stage() -> None:
    """
    Condition:
    - Every recipient requirement, against its opportunity's financial basis (SC-001).

    Expected:
    - None is refused and all have a reason. A1's certificate applies at commercialization and C1's at submission, and
      nothing keeps the prototype's ``current`` operator or ``doc:`` field.
    """
    for item in OPPORTUNITIES.values():
        content = item["content"]
        requirements = [RequirementInput.model_validate(row) for row in content["requirements"]]
        errors, rows = validate_requirements(requirements, content["financial"])
        assert errors == []
        assert all(row["reason"] for row in rows)
        assert all(row["operator"] != "current" and not row["field"].startswith("doc:") for row in rows)

    def certificate(key: str) -> dict[str, Any]:
        rows = OPPORTUNITIES[key]["content"]["requirements"]
        return next(row for row in rows if row["field"] == "document:certificate")

    assert certificate("A1")["applies_at"] == "COMMERCIALIZATION"
    assert certificate("C1")["applies_at"] == "SUBMISSION"
