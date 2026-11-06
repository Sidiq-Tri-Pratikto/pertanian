"""The change rule and its evidence snapshot. One rule for small and large loads (PRD §12.2)."""

import hashlib
import json
from collections import defaultdict
from datetime import timedelta
from fractions import Fraction
from typing import Any

from app.assets.model.models import AssetModel
from app.baseline.service.compare import Comparison, ComparisonState, median
from app.baseline.service.service import comparison_response
from app.energy.service.format import kwh
from app.energy.service.periods import Window
from app.insights.model.models import POLICY_ID, POLICY_VERSION

RULE_TEXT = "Perubahan dihitung bila |C − B| > 0 dan |C − B| ≥ maks(30% × B; 3 × MAD; 5 × r)."


def threshold(comparison: Comparison) -> Fraction | None:
    """Return the gate ``max(0.30 × B, 3 × MAD, 5 × r)``, or None without a known resolution.

    Args:
        comparison (Comparison): A comparison with a baseline.

    Returns:
        Fraction | None: The threshold in mWh.
    """
    if comparison.baseline_mwh is None or comparison.mad_mwh is None or comparison.resolution_mwh is None:
        return None
    return max(
        Fraction(3, 10) * comparison.baseline_mwh, 3 * comparison.mad_mwh, Fraction(5 * comparison.resolution_mwh)
    )


def direction(comparison: Comparison) -> str | None:
    """Apply the rule. Only a comparable result can qualify; descriptive ones never alert.

    Args:
        comparison (Comparison): The comparison.

    Returns:
        str | None: ``increase`` or ``decrease``, or None when nothing qualifies.
    """
    gate = threshold(comparison)
    delta = comparison.delta_mwh
    if comparison.state is not ComparisonState.COMPARABLE or gate is None or delta is None or delta == 0:
        return None
    if abs(delta) < gate:
        return None
    return "increase" if delta > 0 else "decrease"


def evidence(
    comparison: Comparison, window: Window, asset: AssetModel, kind: str, change: str, origins: list[str]
) -> dict[str, Any]:
    """Freeze everything a reader needs to check the observation, built only from computed values.

    Args:
        comparison (Comparison): The qualifying comparison.
        window (Window): The period.
        asset (AssetModel): The asset.
        kind (str): Insight kind.
        change (str): ``increase`` or ``decrease``.
        origins (list[str]): Origins of the asset's readings in the period.

    Returns:
        dict[str, Any]: JSON-ready evidence.
    """
    rendered = comparison_response(comparison, window).model_dump(mode="json")
    gate = threshold(comparison)
    assert comparison.current is not None and gate is not None
    by_day: dict[int, list] = defaultdict(list)
    for key in comparison.mask:
        by_day[key[0]].append(key)
    eligible = [w for w in comparison.historical if w.index in comparison.eligible]
    series = [
        {
            "local_date": str(window.start_date + timedelta(days=day)),
            "comparison_kwh": kwh(comparison.mask_sum(comparison.current, keys)),
            "reference_kwh": kwh(median([comparison.mask_sum(w, keys) for w in eligible])),
        }
        for day, keys in sorted(by_day.items())
    ]
    return {
        "kind": kind,
        "direction": change,
        "asset": {
            "id": str(asset.id),
            "name": asset.name,
            "scope_kind": asset.scope_kind.value,
            "expected_use": asset.expected_use.value,
        },
        "scope": {"type": "asset", "asset_ids": [str(asset.id)]},
        "period": rendered["window"],
        "current": rendered["current"],
        "historical": [w for w in rendered["historical"] if w["eligible"]],
        "skipped": [w for w in rendered["historical"] if not w["eligible"]],
        "baseline_kwh": rendered["baseline_kwh"],
        "mad_kwh": rendered["mad_kwh"],
        "delta_kwh": rendered["delta_kwh"],
        "percent": rendered["percent"],
        "percent_unavailable_reason": None if rendered["percent"] is not None else "zero_baseline",
        "resolution_kwh": rendered["resolution_kwh"],
        "threshold_kwh": kwh(gate),
        "mask_coverage": rendered["mask_coverage"],
        "common_mask": rendered["common_mask"],
        "series": series,
        "origins": origins,
        "policy": {"id": POLICY_ID, "version": POLICY_VERSION},
        "rule": RULE_TEXT,
    }


def evidence_hash(snapshot: dict[str, Any]) -> str:
    """Hash the semantic snapshot. Generation time is stored apart, so equal evidence keeps its revision.

    Args:
        snapshot (dict[str, Any]): The evidence.

    Returns:
        str: SHA-256 hex digest of canonical JSON.
    """
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
