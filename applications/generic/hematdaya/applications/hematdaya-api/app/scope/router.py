"""Read, preview and confirm the scope of an owned site."""

from uuid import UUID

from fastapi import APIRouter

from app.identity.dependencies import PrincipalDep
from app.scope.dependencies import ScopeServiceDep
from app.scope.model.schema import (
    ConfirmScopeRequest,
    ScopePreviewResponse,
    ScopeProposalRequest,
    ScopeSelectionResponse,
)

router = APIRouter(prefix="/sites/{site_id}/aggregation-selection", tags=["scope"])
_SCOPE_ERROR = {"$ref": "#/components/schemas/ErrorEnvelope"}


@router.get("")
async def get_selection(site_id: UUID, principal: PrincipalDep, service: ScopeServiceDep) -> ScopeSelectionResponse:
    """Return raw membership, scope revisions, and current authority and validity."""
    return await service.get(site_id, principal)


@router.post(
    "/preview",
    responses={409: {"description": "SCOPE_CONFLICT", "content": {"application/json": {"schema": _SCOPE_ERROR}}}},
)
async def preview_selection(
    site_id: UUID, proposal: ScopeProposalRequest, principal: PrincipalDep, service: ScopeServiceDep
) -> ScopePreviewResponse:
    """Calculate a draft with its resolved period and base revisions without persisting it."""
    return await service.preview(site_id, principal, proposal)


@router.put(
    "",
    responses={
        409: {"description": "SCOPE_CONFLICT or SCOPE_STALE", "content": {"application/json": {"schema": _SCOPE_ERROR}}}
    },
)
async def confirm_selection(
    site_id: UUID, proposal: ConfirmScopeRequest, principal: PrincipalDep, service: ScopeServiceDep
) -> ScopeSelectionResponse:
    """Revalidate and atomically apply a proposal with the preview period and revisions."""
    return await service.confirm(site_id, principal, proposal)
