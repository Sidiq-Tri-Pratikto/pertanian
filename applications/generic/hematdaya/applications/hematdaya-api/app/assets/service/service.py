"""Asset, source and binding rules."""

import base64
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.assets.model.models import (
    AssetModel,
    BindingModel,
    ExpectedUse,
    MeasurementKind,
    RelationKind,
    ScopeKind,
    SourceModel,
    SourceOrigin,
    TransportStatus,
)
from app.assets.model.schema import CreateAssetRequest, CreateBindingRequest, UpdateAssetRequest
from app.assets.repository.base_repository import AssetRepository
from app.assets.service.errors import AssetCycleError
from app.assets.service.relations import would_create_cycle
from app.audit.service.service import AuditService
from app.core.errors.base import NotFoundError, RequestInvalidError
from app.identity.model.models import PrincipalModel
from app.sites.model.models import SiteModel
from app.sites.service.clock import site_clock
from app.sites.service.service import SiteService

_BINDING_NOT_STARTED = (
    "Sumber ini belum mulai tercatat sehingga belum dapat diakhiri. Coba lagi setelah waktu mulainya."
)
_CURSOR_INVALID = "Penanda halaman tidak valid. Muat ulang daftar dari awal."


class AssetDetail(BaseModel):
    """An asset with its bindings and their sources."""

    asset: AssetModel
    bindings: list[BindingModel]
    sources: list[SourceModel]


class AssetPage(BaseModel):
    """One page of assets."""

    items: list[AssetModel]
    next_cursor: str | None


def encode_cursor(asset: AssetModel) -> str:
    """Encode a page position. Opaque to clients.

    Args:
        asset (AssetModel): The last asset of the page.

    Returns:
        str: The cursor.
    """
    return base64.urlsafe_b64encode(json.dumps([asset.name, str(asset.id)]).encode()).decode()


def decode_cursor(cursor: str) -> tuple[str, UUID]:
    """Decode a page position.

    Args:
        cursor (str): The cursor.

    Returns:
        tuple[str, UUID]: The last (name, ID) returned.

    Raises:
        RequestInvalidError: When the cursor was not issued by this API.
    """
    try:
        name, asset_id = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return str(name), UUID(asset_id)
    except (ValueError, TypeError) as error:
        raise RequestInvalidError(_CURSOR_INVALID, error=error) from error


class AssetService:
    """Owns the asset model. Every change takes the site lock and writes one audit event."""

    def __init__(self, repository: AssetRepository, sites: SiteService, audit: AuditService) -> None:
        """Bind to storage and neighbouring services.

        Args:
            repository (AssetRepository): Asset storage.
            sites (SiteService): Site ownership, lock and revisions.
            audit (AuditService): Audit trail.
        """
        self.repository = repository
        self.sites = sites
        self.audit = audit

    async def list_assets(
        self, site_id: UUID, principal: PrincipalModel, *, include_archived: bool, limit: int, cursor: str | None
    ) -> AssetPage:
        """Return one page of an owned site's assets.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.
            include_archived (bool): Also list archived assets.
            limit (int): Page size, at most 100.
            cursor (str | None): Position from the previous page.

        Returns:
            AssetPage: The page.
        """
        site = await self.sites.get_owned(site_id, principal)
        after = decode_cursor(cursor) if cursor else None
        items = await self.repository.list_assets(
            site.id, include_archived=include_archived, limit=limit + 1, after=after
        )
        more = len(items) > limit
        items = items[:limit]
        return AssetPage(items=items, next_cursor=encode_cursor(items[-1]) if more else None)

    async def create_asset(self, site_id: UUID, principal: PrincipalModel, request: CreateAssetRequest) -> AssetModel:
        """Create an asset in an owned site.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.
            request (CreateAssetRequest): The asset.

        Returns:
            AssetModel: The new asset.

        Raises:
            NotFoundError: When the site or the parent is not the principal's.
        """
        site = await self.sites.lock_owned(site_id, principal)
        if request.parent_asset_id is not None:
            await self._asset_in_site(site, request.parent_asset_id)
        asset = await self.repository.add_asset(site.id, request.model_dump())
        await self._record(site, principal, "asset.created", "asset", asset.id, {"name": asset.name})
        await self.sites.advance_binding_revision(site)  # A new asset joins the default scope.
        return asset

    async def get_asset_detail(self, asset_id: UUID, principal: PrincipalModel) -> AssetDetail:
        """Return an owned asset with its bindings and sources.

        Args:
            asset_id (UUID): The asset.
            principal (PrincipalModel): The acting principal.

        Returns:
            AssetDetail: The asset.
        """
        asset, _ = await self._owned_asset(asset_id, principal, lock=False)
        bindings = await self.repository.list_bindings(asset.id)
        sources = await self.repository.list_sources(sorted({binding.source_id for binding in bindings}))
        return AssetDetail(asset=asset, bindings=bindings, sources=sources)

    async def update_asset(self, asset_id: UUID, principal: PrincipalModel, request: UpdateAssetRequest) -> AssetModel:
        """Rename, recategorize, relocate, set expected use, archive or restore an owned asset.

        Args:
            asset_id (UUID): The asset.
            principal (PrincipalModel): The acting principal.
            request (UpdateAssetRequest): The changes.

        Returns:
            AssetModel: The asset; unchanged values write nothing.
        """
        asset, site = await self._owned_asset(asset_id, principal, lock=True)
        changes: dict[str, Any] = {
            key: value
            for key, value in request.model_dump(exclude_unset=True, exclude={"archived"}).items()
            if value is not None and getattr(asset, key) != value
        }
        if request.archived is not None and request.archived != (asset.archived_at is not None):
            changes["archived_at"] = site_clock(site) if request.archived else None
        if not changes:
            return asset
        updated = await self.repository.update_asset(asset.id, changes)
        detail = {key: None if value is None else str(value) for key, value in changes.items()}
        await self._record(site, principal, "asset.updated", "asset", asset.id, detail)
        if "archived_at" in changes:
            await self.sites.advance_binding_revision(site)
        return updated

    async def bind_source(
        self, asset_id: UUID, principal: PrincipalModel, request: CreateBindingRequest
    ) -> BindingModel:
        """Attribute a source of the asset's site to the asset.

        Args:
            asset_id (UUID): The asset.
            principal (PrincipalModel): The acting principal.
            request (CreateBindingRequest): The binding.

        Returns:
            BindingModel: The new binding.

        Raises:
            NotFoundError: When the asset or the source is not in the principal's site.
            BindingOverlapError: When another authoritative binding covers the same instant.
        """
        asset, site = await self._owned_asset(asset_id, principal, lock=True)
        source = await self.repository.get_source_in_site(site.id, request.source_id)
        if source is None:
            raise NotFoundError()
        binding = await self.repository.add_binding(
            site_id=site.id,
            source_id=source.id,
            asset_id=asset.id,
            effective_from=request.effective_from,
            authoritative=request.authoritative,
        )
        await self._record(
            site,
            principal,
            "binding.created",
            "binding",
            binding.id,
            {"source_id": str(source.id), "authoritative": binding.authoritative},
            affected_from=binding.effective_from,
        )
        await self.sites.advance_binding_revision(site)
        return binding

    async def unlink_source(self, asset_id: UUID, binding_id: UUID, principal: PrincipalModel) -> BindingModel:
        """End a binding at site time. The row and its readings stay; a repeat changes nothing.

        Args:
            asset_id (UUID): The asset.
            binding_id (UUID): The binding.
            principal (PrincipalModel): The acting principal.

        Returns:
            BindingModel: The binding with its end.

        Raises:
            NotFoundError: When the binding is not the named owned asset's.
            RequestInvalidError: When the binding has not started, so ending it would leave an empty range.
        """
        asset, site = await self._owned_asset(asset_id, principal, lock=True)
        binding = await self.repository.get_binding(asset.id, binding_id)
        if binding is None:
            raise NotFoundError()
        if binding.effective_to is not None:
            return binding
        now = site_clock(site)
        if binding.effective_from >= now:
            raise RequestInvalidError(_BINDING_NOT_STARTED)
        closed = await self.repository.close_binding(binding.id, now)
        if closed is None:  # Closed meanwhile; the site lock makes this unreachable in practice.
            current = await self.repository.get_binding(asset.id, binding_id)
            assert current is not None
            return current
        await self._record(site, principal, "binding.closed", "binding", binding.id, {}, affected_from=now)
        await self.sites.advance_binding_revision(site)
        return closed

    async def create_source(
        self,
        site: SiteModel,
        *,
        label: str,
        origin: SourceOrigin,
        measurement_kind: MeasurementKind,
        cadence_seconds: int | None = None,
        resolution_mwh: int | None = None,
        transport_status: TransportStatus = TransportStatus.NONE,
    ) -> SourceModel:
        """Create a source in a site the caller has already resolved. Demo, CSV and enrollment call this.

        Args:
            site (SiteModel): The site.
            label (str): Display label.
            origin (SourceOrigin): Where readings come from.
            measurement_kind (MeasurementKind): What raw values mean.
            cadence_seconds (int | None, optional): Expected interval. Defaults to None.
            resolution_mwh (int | None, optional): Smallest step; None when unknown. Defaults to None.
            transport_status (TransportStatus, optional): How it arrives. Defaults to none.

        Returns:
            SourceModel: The source.
        """
        return await self.repository.add_source(
            site.id,
            {
                "label": label,
                "origin": origin.value,
                "measurement_kind": measurement_kind.value,
                "cadence_seconds": cadence_seconds,
                "resolution_mwh": resolution_mwh,
                "transport_status": transport_status.value,
            },
        )

    async def add_asset(
        self,
        site: SiteModel,
        *,
        name: str,
        scope_kind: ScopeKind,
        category: str | None = None,
        location: str | None = None,
        expected_use: ExpectedUse = ExpectedUse.UNKNOWN,
    ) -> AssetModel:
        """Create an asset in a site the caller has locked, without an audit event. Seeding calls this.

        Args:
            site (SiteModel): The site.
            name (str): Name.
            scope_kind (ScopeKind): Scope kind.
            category (str | None, optional): Category. Defaults to None.
            location (str | None, optional): Location. Defaults to None.
            expected_use (ExpectedUse, optional): Expected use. Defaults to unknown.

        Returns:
            AssetModel: The asset.
        """
        return await self.repository.add_asset(
            site.id,
            {
                "name": name,
                "scope_kind": scope_kind.value,
                "category": category,
                "location": location,
                "expected_use": expected_use.value,
            },
        )

    async def add_binding(
        self, site: SiteModel, *, asset_id: UUID, source_id: UUID, effective_from: datetime, authoritative: bool
    ) -> BindingModel:
        """Bind within a site the caller has locked, without an audit event. Seeding calls this.

        Args:
            site (SiteModel): The site.
            asset_id (UUID): Asset of that site.
            source_id (UUID): Source of that site.
            effective_from (datetime): Start of the range.
            authoritative (bool): Reference source or candidate.

        Returns:
            BindingModel: The binding.
        """
        return await self.repository.add_binding(
            site_id=site.id,
            source_id=source_id,
            asset_id=asset_id,
            effective_from=effective_from,
            authoritative=authoritative,
        )

    async def relate(self, site: SiteModel, from_asset_id: UUID, to_asset_id: UUID, kind: RelationKind) -> None:
        """Record what is known about two assets of a locked site.

        Args:
            site (SiteModel): The site.
            from_asset_id (UUID): The container for ``contains``.
            to_asset_id (UUID): The other asset.
            kind (RelationKind): The relation.

        Raises:
            NotFoundError: When either asset is not in the site.
            AssetCycleError: When ``contains`` would make an asset contain itself.
        """
        await self._asset_in_site(site, from_asset_id)
        await self._asset_in_site(site, to_asset_id)
        if from_asset_id == to_asset_id or (
            kind is RelationKind.CONTAINS
            and would_create_cycle(await self.repository.containment(site.id), from_asset_id, to_asset_id)
        ):
            raise AssetCycleError()
        await self.repository.add_relation(site.id, from_asset_id, to_asset_id, kind)

    async def clear(self, site: SiteModel) -> None:
        """Remove a locked site's assets, sources, bindings, relations and readings. Demo reset uses this.

        Args:
            site (SiteModel): The locked site.
        """
        await self.repository.clear(site.id)

    async def _asset_in_site(self, site: SiteModel, asset_id: UUID) -> AssetModel:
        asset = await self.repository.get_asset_in_site(site.id, asset_id)
        if asset is None:
            raise NotFoundError()
        return asset

    async def _owned_asset(
        self, asset_id: UUID, principal: PrincipalModel, *, lock: bool
    ) -> tuple[AssetModel, SiteModel]:
        asset = await self.repository.get_asset(asset_id)
        if asset is None:
            raise NotFoundError()
        if lock:
            site = await self.sites.lock_owned(asset.site_id, principal)
            asset = await self._asset_in_site(site, asset_id)  # Re-read under the lock.
        else:
            site = await self.sites.get_owned(asset.site_id, principal)
        return asset, site

    async def _record(
        self,
        site: SiteModel,
        principal: PrincipalModel,
        action: str,
        subject_type: str,
        subject_id: UUID,
        detail: dict[str, Any],
        *,
        affected_from: datetime | None = None,
    ) -> None:
        await self.audit.record(
            site_id=site.id,
            actor_principal_id=principal.id,
            action=action,
            subject_type=subject_type,
            subject_id=subject_id,
            affected_from=affected_from,
            detail=detail,
        )
