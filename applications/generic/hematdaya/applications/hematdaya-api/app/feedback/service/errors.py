"""Feedback failures."""

from app.core.errors import codes
from app.core.errors.base import AppError


class FeedbackKeyConflictError(AppError):
    """An ``Idempotency-Key`` already used for a different insight, revision or action."""

    code = codes.APP_FEEDBACK_KEY_CONFLICT
