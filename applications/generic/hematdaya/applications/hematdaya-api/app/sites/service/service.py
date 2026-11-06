"""Site rules: ownership, settings and creation for the modules that own a site's lifecycle."""

from datetime import datetime
from uuid import UUID

from app.core.errors.base import NotFoundError
from app.identity.model.models import PrincipalModel
from app.sites.model.models import SiteContext, SiteKind, SiteModel
from app.sites.model.schema import UpdateSiteRequest
from app.sites.repository.base_repository import SiteRepository


class SiteService:
    """Resolves sites through their owner. A foreign site is indistinguishable from a missing one."""

    def __init__(self, repository: SiteRepository) -> None:
        """Bind to storage.

        Args:
            repository (SiteRepository): Site storage.
        """
        self.repository = repository

    async def get_owned(self, site_id: UUID, principal: PrincipalModel) -> SiteModel:
        """Return a site the principal owns.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.

        Returns:
            SiteModel: The site.

        Raises:
            NotFoundError: When it does not exist or belongs to someone else.
        """
        site = await self.repository.get_owned(site_id, principal.id)
        if site is None:
            raise NotFoundError()
        return site

    async def lock_owned(self, site_id: UUID, principal: PrincipalModel) -> SiteModel:
        """Take the shared site write lock on a site the principal owns.

        Binding, scope, measurement and reset changes hold this lock until their transaction ends.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.

        Returns:
            SiteModel: The site, current as of the lock.

        Raises:
            NotFoundError: When it does not exist or belongs to someone else.
        """
        site = await self.repository.get_owned(site_id, principal.id, lock=True)
        if site is None:
            raise NotFoundError()
        return site

    async def update(self, site_id: UUID, principal: PrincipalModel, request: UpdateSiteRequest) -> SiteModel:
        """Change an owned site's settings.

        Args:
            site_id (UUID): The site.
            principal (PrincipalModel): The acting principal.
            request (UpdateSiteRequest): The validated changes.

        Returns:
            SiteModel: The updated site.

        Raises:
            NotFoundError: When it does not exist or belongs to someone else.
        """
        site = await self.lock_owned(site_id, principal)
        values = {key: value for key, value in request.model_dump(exclude_unset=True).items() if value is not None}
        changed = {key: value for key, value in values.items() if getattr(site, key) != value}
        return await self.repository.update(site.id, changed) if changed else site

    async def create(
        self,
        owner: PrincipalModel,
        *,
        kind: SiteKind,
        name: str,
        context: SiteContext = SiteContext.UNSPECIFIED,
        timezone: str = "Asia/Jakarta",
        currency: str = "IDR",
        virtual_now: datetime | None = None,
    ) -> SiteModel:
        """Create a site. Demo creation (008) and accounts (036) call this; there is no public route.

        Args:
            owner (PrincipalModel): The owner.
            kind (SiteKind): Demo or standard.
            name (str): Display name.
            context (SiteContext, optional): Usage context. Defaults to unspecified.
            timezone (str, optional): IANA timezone. Defaults to Asia/Jakarta.
            currency (str, optional): Currency code. Defaults to IDR.
            virtual_now (datetime | None, optional): Demo clock. Defaults to None.

        Returns:
            SiteModel: The new site.
        """
        return await self.repository.add(
            owner_id=owner.id,
            kind=kind,
            name=name,
            context=context,
            timezone=timezone,
            currency=currency,
            virtual_now=virtual_now,
        )
