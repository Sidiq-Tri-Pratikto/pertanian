"""Demo session failures."""

from app.core.errors import codes
from app.core.errors.base import AppError


class DemoCapacityError(AppError):
    """No active slot or creation budget remains."""

    code = codes.APP_DEMO_CAPACITY


class SessionExpiredError(AppError):
    """A known demo token whose session has expired."""

    code = codes.APP_SESSION_EXPIRED
    headers = {"WWW-Authenticate": "Bearer"}


class ScenarioUnknownError(AppError):
    """The scenario is not in the catalog."""

    code = codes.APP_SCENARIO_UNKNOWN


class ReplayProofMismatchError(AppError):
    """A known operation was repeated without its proof. Indistinguishable from a missing one."""

    code = codes.APP_DEMO_REPLAY_PROOF_MISMATCH


class ReplayConflictError(AppError):
    """A proven replay that changed its payload, outlived its window or names an ended session."""

    code = codes.APP_DEMO_REPLAY_CONFLICT
