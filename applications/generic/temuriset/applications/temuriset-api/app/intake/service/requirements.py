"""Which requirements exist: operators, value shapes and fields (FR-003, D9, D15). Evaluating them is spec 019's."""

from typing import Any, get_args

from app.core.types import parse_decimal
from app.intake.model.schema import RequirementInput
from app.portfolio.model.schema import Stage

NARRATIVE = "narrative"
MAX_TEXT = 200
MAX_ITEMS = 50

_STAGES = frozenset(get_args(Stage))
_FIELD_OPERATORS = {
    "stage": {"equals", "in_set", "intersects"},
    "relationship": {"equals", "in_set"},
    "budget": {"minimum", "maximum", "range_overlap"},
    "contribution": {"minimum", "maximum", "range_overlap"},
    "authority": {"equals"},
    "entity": {"equals"},
}
_PREFIX_OPERATORS = {"document": {"exists"}, "feature": {"equals", "exists"}}


def _error(index: int, where: str, message: str) -> dict:
    return {"loc": ["body", "requirements", index, where], "msg": message, "type": "requirement"}


def _operators_of(field: str) -> set[str] | None:
    """Return what a field may use, or None for a field nobody defined."""
    if field in _FIELD_OPERATORS:
        return _FIELD_OPERATORS[field]
    prefix, separator, name = field.partition(":")
    if separator and name and prefix in _PREFIX_OPERATORS:
        return _PREFIX_OPERATORS[prefix]
    return None


def _text_item(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= MAX_TEXT


def _value_problem(field: str, operator: str, value: Any, financial: dict[str, Any] | None) -> tuple[str, str] | None:
    """Say where a value does not fit its operator.

    Args:
        field (str): The requirement's field.
        operator (str): Its operator.
        value (Any): Its value.
        financial (dict[str, Any] | None): The version's financial basis.

    Returns:
        tuple[str, str] | None: Where the problem is and its message, or None when it fits.
    """
    if operator == "equals":
        if isinstance(value, bool) or _text_item(value):
            if field == "stage" and value not in _STAGES:
                return "value", "Pilih tahap yang dikenal."
            return None
        return "value", "Isi satu nilai untuk dibandingkan."
    if operator in ("in_set", "intersects"):
        if (
            not isinstance(value, list)
            or not 0 < len(value) <= MAX_ITEMS
            or not all(_text_item(item) for item in value)
        ):
            return "value", "Isi daftar nilai untuk dibandingkan."
        if field == "stage" and not set(value) <= _STAGES:
            return "value", "Pilih tahap yang dikenal."
        return None
    if operator in ("minimum", "maximum"):
        if isinstance(value, str) and parse_decimal(value) is not None:
            return None
        return "value", "Isi angka desimal, misalnya 20000 atau 20000.50."
    if operator == "exists":
        return None if value is True else ("value", "Syarat keberadaan hanya bernilai benar.")
    if value is not None:
        return "value", "Syarat ini tidak memakai nilai."
    if operator == "range_overlap" and (financial is None or financial.get("min") is None):
        return "operator", "Isi kisaran pada dasar keuangan sebelum memakai syarat ini."
    return None


def _problem(request: RequirementInput, financial: dict[str, Any] | None) -> tuple[str, str] | None:
    operator = request.operator
    if request.field == NARRATIVE:
        return None if operator == "manual_review" else ("operator", "Syarat naratif hanya bisa ditinjau manual.")
    operators = _operators_of(request.field or "")
    if operators is None:
        return "field", "Pilih bidang syarat yang dikenal."
    if operator != "manual_review" and operator not in operators:
        return "operator", "Bidang ini tidak memakai operator tersebut."
    return _value_problem(request.field, operator, request.value, financial)


def validate_requirements(
    requirements: list[RequirementInput], financial: dict[str, Any] | None
) -> tuple[list[dict], list[dict[str, Any]]]:
    """Check requirements and normalize narrative ones into review questions that cannot block.

    Args:
        requirements (list[RequirementInput]): The requirements as sent.
        financial (dict[str, Any] | None): The version's financial basis, which ``range_overlap`` compares against.

    Returns:
        tuple[list[dict], list[dict[str, Any]]]: Field errors, and one row of columns per requirement; the rows are
            only meaningful when there are no errors.
    """
    errors: list[dict] = []
    rows: list[dict[str, Any]] = []
    for index, request in enumerate(requirements):
        narrative = request.operator is None or request.field == NARRATIVE
        problem = None if request.operator is None else _problem(request, financial)
        if problem is not None:
            errors.append(_error(index, *problem))
        mandatory = request.mandatory and not narrative
        if mandatory and request.visibility != "PUBLIC":
            errors.append(_error(index, "visibility", "Syarat wajib harus terlihat oleh pelamar."))
        rows.append(
            {
                "label": request.label,
                "field": NARRATIVE if request.operator is None else request.field,
                "operator": request.operator or "manual_review",
                "value": None if request.operator is None else request.value,
                "mandatory": mandatory,
                "applies_at": request.applies_at,
                "verification_mode": request.verification_mode,
                "visibility": request.visibility,
                "reason": request.reason,
            }
        )
    return errors, rows
