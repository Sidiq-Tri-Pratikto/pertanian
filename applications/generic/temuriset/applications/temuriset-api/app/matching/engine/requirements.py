"""Evaluate one typed requirement: ``PASS``, ``FAIL`` or ``UNKNOWN`` with a reason. Unknown is never a failure."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.matching.engine.inputs import Money, Source, Target

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"
MANUAL = "Perlu ditinjau secara manual."
_DIFFERENT_CURRENCY = "Mata uang berbeda dan tidak ada dasar konversi yang disetujui."


@dataclass(frozen=True)
class Outcome:
    """One requirement's result.

    Attributes:
        result (str): ``PASS``, ``FAIL`` or ``UNKNOWN``.
        reason (str): Why, in Indonesian.
        action (str | None): What the applicant can do about it, such as ``complete-budget``.
        feature (Decimal | None): Financial compatibility for fit: 1, 0.5, 0, or None when unknown.
    """

    result: str
    reason: str
    action: str | None = None
    feature: Decimal | None = None


def _overlaps(first: Money, second: Money) -> bool:
    return first.low <= second.high and second.low <= first.high  # type: ignore[operator]


def compare_budget(source: Source, target: Target) -> Outcome:
    """Compare a project budget with a partner's support on the same subject, currency, basis, period and scope.

    Args:
        source (Source): The applicant.
        target (Target): The opportunity.

    Returns:
        Outcome: Overlap passes with feature 1; no overlap passes at 0.5 when partial support is accepted, else fails.
    """
    budget, offered = source.budget, target.financial
    if budget is None or not budget.known:
        return Outcome(UNKNOWN, "Kisaran biaya pilot untuk kebutuhan ini belum diisi.", "complete-budget")
    if offered is None or not offered.known or offered.subject != "partner":
        return Outcome(UNKNOWN, "Mitra tidak menyatakan kisaran yang sebanding.")
    if budget.currency != offered.currency:
        return Outcome(UNKNOWN, _DIFFERENT_CURRENCY)
    same_period = budget.basis == offered.basis and (
        budget.basis != "total_period" or (budget.months is not None and budget.months == offered.months)
    )
    scopes = budget.scope.strip().casefold(), offered.scope.strip().casefold()
    if not same_period or (all(scopes) and scopes[0] != scopes[1]):
        return Outcome(UNKNOWN, "Periode atau cakupan berbeda, jadi jumlahnya belum sebanding.")
    if _overlaps(budget, offered):
        return Outcome(PASS, "Kisaran biaya beririsan pada cakupan dan periode yang sama.", feature=Decimal(1))
    if source.accepts_partial:
        return Outcome(PASS, "Kisaran tidak beririsan, tetapi dukungan sebagian diterima.", feature=Decimal("0.5"))
    return Outcome(FAIL, "Kisaran biaya tidak beririsan dan dukungan penuh diwajibkan.", feature=Decimal(0))


def compare_contribution(source: Source, target: Target) -> Outcome:
    """Compare an investor's check with the desired contribution per investor, never with the whole target (AC20).

    Args:
        source (Source): The applicant.
        target (Target): The opportunity.

    Returns:
        Outcome: As for budgets.
    """
    wanted, check = source.contribution, target.financial
    if source.type != "FUNDING_REQUEST":
        return Outcome(UNKNOWN, "Dasar kontribusi belum jelas.")
    if wanted is None or not wanted.known:
        return Outcome(UNKNOWN, "Kisaran kontribusi per investor belum diisi.", "complete-contribution")
    if check is None or not check.known or check.subject != "investorCheck":
        return Outcome(UNKNOWN, "Mitra tidak menyatakan kisaran yang sebanding.")
    if wanted.currency != check.currency:
        return Outcome(UNKNOWN, _DIFFERENT_CURRENCY)
    if _overlaps(wanted, check):
        return Outcome(
            PASS,
            "Kisaran investasi beririsan dengan kontribusi yang diinginkan, bukan dengan seluruh target.",
            feature=Decimal(1),
        )
    if source.accepts_partial:
        return Outcome(PASS, "Tidak beririsan, tetapi pendanaan sebagian diterima.", feature=Decimal("0.5"))
    return Outcome(FAIL, "Kisaran tidak beririsan dan pendanaan penuh diwajibkan.", feature=Decimal(0))


def _bound(source: Source, operator: str, value: Any) -> Outcome:
    """``minimum`` or ``maximum`` on the applicant's own amount, in the target's currency only."""
    money = source.contribution if source.type == "FUNDING_REQUEST" else source.budget
    if money is None or not money.known:
        return Outcome(UNKNOWN, "Jumlah untuk kebutuhan ini belum diisi.", "complete-budget")
    limit = Decimal(value)
    passed = money.low >= limit if operator == "minimum" else money.high <= limit  # type: ignore[operator]
    if passed:
        return Outcome(PASS, "Jumlah memenuhi batas mandat ini.")
    return Outcome(FAIL, "Jumlah berada di luar batas mandat ini.")


def _listed(actual: str | None, operator: str, value: Any) -> bool:
    return actual == value if operator == "equals" else actual in (value or [])


def _feature(source: Source, key: str, operator: str, value: Any) -> Outcome:
    timings = [timing for fact_key, timing in source.facts if fact_key == key]
    if not timings:
        return Outcome(UNKNOWN, "Belum ada informasi tentang fitur ini.", "add-fact")
    # A required CURRENT fact is never satisfied by a PLANNED one; CURRENT satisfies any timing.
    if operator == "exists" or "CURRENT" in timings or value in timings:
        return Outcome(PASS, "Fitur sudah ada saat ini." if "CURRENT" in timings else "Fitur sesuai mandat ini.")
    return Outcome(FAIL, "Fitur baru direncanakan, sedangkan mandat ini memerlukan fitur yang sudah berjalan.")


def _document(source: Source, key: str, mode: str) -> Outcome:
    files = source.documents.get(key, ())
    if mode == "REVIEWER_CONFIRMED":
        if any(file["REVIEWER_CONFIRMED"] == PASS for file in files):
            return Outcome(PASS, "Sudah diperiksa untuk kriteria ini.")
        return Outcome(UNKNOWN, "Belum ada dokumen yang diperiksa untuk kriteria ini.")
    if any(file["DOCUMENT_PRESENT"] == PASS for file in files):
        return Outcome(PASS, "Berkas tersedia. Isinya belum diperiksa.")
    if files:
        return Outcome(UNKNOWN, "Berkas belum lolos pemeriksaan keamanan.")
    return Outcome(UNKNOWN, "Berkas belum disediakan.", "add-document")


def _entity(source: Source, value: Any) -> Outcome:
    if source.entity == value:
        return Outcome(PASS, "Badan usaha sudah disebutkan.")
    if source.entity == "PROPOSED" and value == "IDENTIFIED":
        return Outcome(FAIL, "Perusahaan belum didirikan, sedangkan mandat ini memerlukan badan usaha.")
    return Outcome(UNKNOWN, "Status badan hukum belum dikonfirmasi.")


def evaluate_requirement(requirement: dict[str, Any], source: Source, target: Target) -> Outcome:  # noqa: PLR0911 - one return per field
    """Evaluate one requirement against the applicant's authorized facts.

    Args:
        requirement (dict[str, Any]): ``field``, ``operator``, ``value``, ``verification_mode`` and ``reason``.
        source (Source): The applicant.
        target (Target): The opportunity.

    Returns:
        Outcome: The result. A narrative or unmapped requirement is ``UNKNOWN`` for manual review (AC27).
    """
    name, operator, value = requirement["field"], requirement["operator"], requirement["value"]
    why = requirement.get("reason") or ""
    if operator == "manual_review":
        return Outcome(UNKNOWN, MANUAL)
    if name == "stage":
        if source.stage is None:
            return Outcome(UNKNOWN, "Tahap inovasi belum dinyatakan.")
        if _listed(source.stage, operator, value):
            return Outcome(PASS, "Tahap inovasi diterima mandat ini.")
        return Outcome(FAIL, why or "Tahap inovasi tidak diterima mandat ini.")
    if name == "relationship":
        if _listed(source.relationship, operator, value):
            return Outcome(PASS, "Bentuk kerja sama sesuai.")
        return Outcome(FAIL, why or "Bentuk kerja sama tidak sesuai dengan mandat ini.")
    if name in ("budget", "contribution"):
        if operator in ("minimum", "maximum"):
            return _bound(source, operator, value)
        return compare_budget(source, target) if name == "budget" else compare_contribution(source, target)
    if name == "authority":
        if any(status.upper() == str(value).upper() for status in source.authority):
            return Outcome(PASS, "Wewenang sudah diperiksa.")
        return Outcome(
            UNKNOWN,
            "Wewenang atas inovasi belum dikonfirmasi. Ini bukan berarti wewenang tidak ada.",
            "clarify-authority",
        )
    if name == "entity":
        return _entity(source, value)
    prefix, _, key = name.partition(":")
    if prefix == "feature":
        return _feature(source, key, operator, value)
    if prefix == "document":
        return _document(source, key, requirement["verification_mode"])
    return Outcome(UNKNOWN, MANUAL)
