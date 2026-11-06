"""Asset and binding endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.assets.dependencies import AssetServiceDep
from app.assets.model.models import AssetModel, BindingModel, SourceModel
from app.assets.model.schema import (
    AssetDetailResponse,
    AssetPageResponse,
    AssetResponse,
    BindingResponse,
    CreateAssetRequest,
    CreateBindingRequest,
    SourceResponse,
    UpdateAssetRequest,
)
from app.identity.dependencies import PrincipalDep

router = APIRouter(tags=["assets"])


def to_asset_response(asset: AssetModel) -> AssetResponse:
    """Render an asset.

    Args:
        asset (AssetModel): The asset.

    Returns:
        AssetResponse: The response.
    """
    return AssetResponse(**asset.model_dump(exclude={"site_id", "archived_at"}), archived=asset.archived_at is not None)


def to_binding_response(binding: BindingModel) -> BindingResponse:
    """Render a binding.

    Args:
        binding (BindingModel): The binding.

    Returns:
        BindingResponse: The response.
    """
    return BindingResponse(**binding.model_dump(exclude={"site_id", "asset_id"}))


def to_source_response(source: SourceModel) -> SourceResponse:
    """Render a source.

    Args:
        source (SourceModel): The source.

    Returns:
        SourceResponse: The response.
    """
    return SourceResponse(**source.model_dump(exclude={"site_id"}))


@router.get("/sites/{site_id}/assets", summary="List a site's assets")
async def list_assets(
    site_id: UUID,
    principal: PrincipalDep,
    service: AssetServiceDep,
    include_archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=400)] = None,
) -> AssetPageResponse:
    """Return one page of assets, active ones unless archived are asked for.

    Args:
        site_id (UUID): The site.
        principal (PrincipalModel): The acting principal.
        service (AssetService): Asset rules.
        include_archived (bool, optional): Add archived assets. Defaults to False.
        limit (int, optional): Page size up to 100. Defaults to 50.
        cursor (str | None, optional): ``next_cursor`` of the previous page. Defaults to None.

    Returns:
        AssetPageResponse: The page.
    """
    page = await service.list_assets(site_id, principal, include_archived=include_archived, limit=limit, cursor=cursor)
    return AssetPageResponse(items=[to_asset_response(item) for item in page.items], next_cursor=page.next_cursor)


@router.post("/sites/{site_id}/assets", status_code=status.HTTP_201_CREATED, summary="Add an asset")
async def create_asset(
    site_id: UUID, request: CreateAssetRequest, principal: PrincipalDep, service: AssetServiceDep
) -> AssetResponse:
    """Create an asset in an owned site.

    Args:
        site_id (UUID): The site.
        request (CreateAssetRequest): The asset.
        principal (PrincipalModel): The acting principal.
        service (AssetService): Asset rules.

    Returns:
        AssetResponse: The asset.
    """
    return to_asset_response(await service.create_asset(site_id, principal, request))


@router.get("/assets/{asset_id}", summary="Read an asset with its sources")
async def get_asset(asset_id: UUID, principal: PrincipalDep, service: AssetServiceDep) -> AssetDetailResponse:
    """Return an owned asset, its bindings and their sources.

    Args:
        asset_id (UUID): The asset.
        principal (PrincipalModel): The acting principal.
        service (AssetService): Asset rules.

    Returns:
        AssetDetailResponse: The asset.
    """
    detail = await service.get_asset_detail(asset_id, principal)
    return AssetDetailResponse(
        **to_asset_response(detail.asset).model_dump(),
        bindings=[to_binding_response(binding) for binding in detail.bindings],
        sources=[to_source_response(source) for source in detail.sources],
    )


@router.patch("/assets/{asset_id}", summary="Change an asset")
async def update_asset(
    asset_id: UUID, request: UpdateAssetRequest, principal: PrincipalDep, service: AssetServiceDep
) -> AssetResponse:
    """Change an owned asset's name, category, location, expected use or archive state.

    Args:
        asset_id (UUID): The asset.
        request (UpdateAssetRequest): The changes.
        principal (PrincipalModel): The acting principal.
        service (AssetService): Asset rules.

    Returns:
        AssetResponse: The asset.
    """
    return to_asset_response(await service.update_asset(asset_id, principal, request))


@router.post("/assets/{asset_id}/bindings", status_code=status.HTTP_201_CREATED, summary="Bind a source")
async def create_binding(
    asset_id: UUID, request: CreateBindingRequest, principal: PrincipalDep, service: AssetServiceDep
) -> BindingResponse:
    """Attribute a source of the same site to an owned asset.

    Args:
        asset_id (UUID): The asset.
        request (CreateBindingRequest): The binding.
        principal (PrincipalModel): The acting principal.
        service (AssetService): Asset rules.

    Returns:
        BindingResponse: The binding.
    """
    return to_binding_response(await service.bind_source(asset_id, principal, request))


@router.delete("/assets/{asset_id}/bindings/{binding_id}", summary="End a binding")
async def delete_binding(
    asset_id: UUID, binding_id: UUID, principal: PrincipalDep, service: AssetServiceDep
) -> BindingResponse:
    """End a binding at site time. History stays; repeating it changes nothing.

    Args:
        asset_id (UUID): The asset.
        binding_id (UUID): The binding.
        principal (PrincipalModel): The acting principal.
        service (AssetService): Asset rules.

    Returns:
        BindingResponse: The binding with its end.
    """
    return to_binding_response(await service.unlink_source(asset_id, binding_id, principal))
