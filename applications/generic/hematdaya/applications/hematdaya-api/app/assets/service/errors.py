"""Asset failures."""

from app.core.errors import codes
from app.core.errors.base import AppError


class AssetCycleError(AppError):
    """A relation would make an asset contain itself."""

    code = codes.APP_ASSET_CYCLE


class BindingOverlapError(AppError):
    """Two authoritative sources would cover one asset at the same instant."""

    code = codes.APP_BINDING_OVERLAP
