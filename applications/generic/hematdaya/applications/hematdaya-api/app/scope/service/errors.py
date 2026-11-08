"""Failures specific to reviewing and confirming aggregation scope."""

from app.core.errors import codes
from app.core.errors.base import AppError
from app.energy.model.schema import ScopeIssueResponse

_MAX_DETAILS = 20


class ScopeConflictError(AppError):
    """The proposal cannot be confirmed because at least one scope issue remains."""

    code = codes.APP_SCOPE_OVERLAP

    def __init__(self, issues: list[ScopeIssueResponse], *, field: str = "selected_asset_ids") -> None:
        """Send only bounded, sanitized issue messages in the public field detail shape."""
        ordered = sorted(issues, key=lambda issue: (issue.type, issue.asset_ids))
        super().__init__(
            details=[
                {"loc": ["body", field], "msg": issue.message, "type": issue.type.value}
                for issue in ordered[:_MAX_DETAILS]
            ]
        )


class ScopeStaleError(AppError):
    """The confirmed proposal's base revisions or resolved local period have changed."""

    code = codes.APP_SCOPE_STALE
