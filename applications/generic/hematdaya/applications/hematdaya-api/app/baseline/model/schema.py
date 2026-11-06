"""Comparison response schemas. Decimal strings; unavailable numbers are null beside the state and reason."""

from datetime import date, datetime

from pydantic import BaseModel

from app.baseline.service.compare import ComparisonState
from app.energy.model.schema import GapResponse, WindowResponse


class ComparisonWindowResponse(BaseModel):
    """One aligned window: the current one (0 weeks before) or a prior one."""

    weeks_before: int
    start_date: date
    end_date: date
    start: datetime
    end: datetime
    measured_kwh: str
    mask_kwh: str | None
    coverage: str
    eligible: bool


class ComparisonResponse(BaseModel):
    """A matched-baseline comparison. Full recorded totals stay separate from common-mask totals."""

    state: ComparisonState
    reason: str | None
    window: WindowResponse
    current: ComparisonWindowResponse | None
    historical: list[ComparisonWindowResponse]
    baseline_kwh: str | None
    mad_kwh: str | None
    delta_kwh: str | None
    percent: str | None
    resolution_kwh: str | None
    mask_coverage: str | None
    common_mask: list[GapResponse]
