"""Requirement operators, value shapes and fields without a database (spec 016, US2, D9, D15)."""

from typing import Any

import pytest

from app.intake.model.schema import RequirementInput
from app.intake.service.requirements import validate_requirements

CASH = {"subject": "partner", "basis": "total_period", "min": "1.0000", "max": "2.0000", "currency": "USD"}


def _one(financial: dict | None = CASH, **content: Any) -> tuple[list[dict], list[dict]]:
    return validate_requirements([RequirementInput(label="Syarat", reason="Alasan", **content)], financial)


@pytest.mark.parametrize(
    ("field", "operator", "value"),
    [
        ("authority", "equals", "REVIEWED"),
        ("feature:sso", "equals", "CURRENT"),
        ("relationship", "equals", "EQUITY"),
        ("stage", "in_set", ["PROTOTYPE", "PILOT"]),
        ("stage", "intersects", ["IDEA"]),
        ("budget", "minimum", "1000"),
        ("budget", "maximum", "1000.50"),
        ("budget", "range_overlap", None),
        ("contribution", "range_overlap", None),
        ("document:function", "exists", True),
        ("feature:sso", "exists", True),
        ("document:function", "manual_review", None),
    ],
)
def test_each_operator_accepts_its_value_shape(field: str, operator: str, value: Any) -> None:
    """
    Condition:
    - A requirement with each operator and a value of the right shape.

    Expected:
    - No errors, and the row keeps what was sent.
    """
    errors, rows = _one(field=field, operator=operator, value=value)

    assert errors == []
    assert (rows[0]["field"], rows[0]["operator"], rows[0]["value"]) == (field, operator, value)


@pytest.mark.parametrize(
    ("field", "operator", "value", "where"),
    [
        ("authority", "equals", None, "value"),
        ("authority", "equals", ["REVIEWED"], "value"),
        ("authority", "equals", 5, "value"),
        ("authority", "equals", "x" * 201, "value"),
        ("stage", "equals", "BUKAN_TAHAP", "value"),
        ("stage", "in_set", [], "value"),
        ("stage", "in_set", "PILOT", "value"),
        ("stage", "in_set", ["BUKAN_TAHAP"], "value"),
        ("stage", "intersects", [1], "value"),
        ("relationship", "in_set", ["x"] * 51, "value"),
        ("budget", "minimum", 1000, "value"),
        ("budget", "minimum", "banyak", "value"),
        ("budget", "maximum", True, "value"),
        ("budget", "range_overlap", {"min": 1}, "value"),
        ("document:function", "exists", False, "value"),
        ("document:function", "manual_review", "x", "value"),
        ("stage", "exists", True, "operator"),
        ("document:function", "equals", "x", "operator"),
        ("nama:karangan", "equals", "x", "field"),
        ("document:", "exists", True, "field"),
        ("karangan", "equals", "x", "field"),
        (None, "equals", "x", "field"),
    ],
)
def test_a_wrong_value_shape_or_field_is_refused(field: str | None, operator: str, value: Any, where: str) -> None:
    """
    Condition:
    - A value of the wrong shape, an operator the field does not take, or a field nobody defined.

    Expected:
    - One error that names where the problem is.
    """
    errors, _ = _one(field=field, operator=operator, value=value)

    assert [error["loc"] for error in errors] == [["body", "requirements", 0, where]]
    assert all(error["msg"] for error in errors)


def test_a_range_needs_a_comparable_financial_basis() -> None:
    """
    Condition:
    - ``range_overlap`` on an opportunity with no financial basis, and with non-cash support only.

    Expected:
    - Both are refused, because there is nothing to compare against.
    """
    for financial in (None, {"subject": "partner", "noncash": "Fasilitas", "min": None}):
        errors, _ = _one(financial, field="budget", operator="range_overlap")
        assert [error["loc"] for error in errors] == [["body", "requirements", 0, "operator"]]


@pytest.mark.parametrize("field", [None, "narrative", "stage", "karangan"])
def test_no_operator_becomes_a_review_question_that_cannot_block(field: str | None) -> None:
    """
    Condition:
    - A requirement has no operator, even if it says it is mandatory and carries a value (D15).

    Expected:
    - It is a non-mandatory ``narrative`` ``manual_review`` with no value.
    """
    errors, rows = _one(field=field, value="Harus punya pengalaman", mandatory=True)

    assert errors == []
    assert (rows[0]["field"], rows[0]["operator"], rows[0]["value"], rows[0]["mandatory"]) == (
        "narrative",
        "manual_review",
        None,
        False,
    )


def test_narrative_with_manual_review_cannot_be_mandatory() -> None:
    """
    Condition:
    - ``narrative`` is sent with ``manual_review`` and marked mandatory.

    Expected:
    - It is stored as non-mandatory.
    """
    errors, rows = _one(field="narrative", operator="manual_review", mandatory=True)

    assert errors == []
    assert rows[0]["mandatory"] is False


@pytest.mark.parametrize("operator", ["equals", "in_set", "exists", "range_overlap"])
def test_narrative_with_a_typed_operator_is_refused(operator: str) -> None:
    """
    Condition:
    - ``narrative`` is sent with a typed operator (D15).

    Expected:
    - It is refused on the operator; narrative text has no approved mapping.
    """
    errors, _ = _one(field="narrative", operator=operator, value=True)

    assert [error["loc"] for error in errors] == [["body", "requirements", 0, "operator"]]


def test_a_mandatory_requirement_cannot_be_hidden() -> None:
    """
    Condition:
    - A mandatory requirement is ``PARTNER_ONLY`` (D9); a non-mandatory one is too.

    Expected:
    - The first is refused on ``visibility``, because no secret criterion may reject a pitch; the second is kept.
    """
    secret, _ = _one(field="authority", operator="equals", value="REVIEWED", visibility="PARTNER_ONLY")
    note, rows = _one(
        field="authority", operator="equals", value="REVIEWED", visibility="PARTNER_ONLY", mandatory=False
    )

    assert [error["loc"] for error in secret] == [["body", "requirements", 0, "visibility"]]
    assert note == []
    assert rows[0]["visibility"] == "PARTNER_ONLY"


def test_every_error_names_its_own_row() -> None:
    """
    Condition:
    - Two requirements, of which the second is wrong.

    Expected:
    - The error names row 1.
    """
    good = RequirementInput(label="A", field="authority", operator="equals", value="REVIEWED")
    bad = RequirementInput(label="B", field="authority", operator="equals")

    errors, _ = validate_requirements([good, bad], None)

    assert [error["loc"] for error in errors] == [["body", "requirements", 1, "value"]]
