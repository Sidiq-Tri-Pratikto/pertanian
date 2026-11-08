"""Scope route wiring on the shared request transaction."""

from typing import Annotated

from fastapi import Depends

from app.assets.dependencies import AssetServiceDep
from app.audit.dependencies import build_audit_service
from app.core.database import SessionDep
from app.energy.dependencies import EnergyServiceDep
from app.scope.selection_dependencies import SelectionServiceDep
from app.scope.service.service import ScopeService
from app.sites.dependencies import SiteServiceDep


def get_scope_service(
    session: SessionDep,
    sites: SiteServiceDep,
    assets: AssetServiceDep,
    energy: EnergyServiceDep,
    selections: SelectionServiceDep,
) -> ScopeService:
    """Build scope operations without coupling selection lookup to preview."""
    return ScopeService(selections, sites, assets, energy, build_audit_service(session))


ScopeServiceDep = Annotated[ScopeService, Depends(get_scope_service)]
