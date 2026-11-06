"""Site endpoints."""

from uuid import UUID

from fastapi import APIRouter

from app.identity.dependencies import PrincipalDep
from app.sites.dependencies import SiteServiceDep
from app.sites.model.models import SiteModel
from app.sites.model.schema import SiteResponse, UpdateSiteRequest
from app.sites.service.clock import site_clock

router = APIRouter(prefix="/sites", tags=["sites"])


def to_response(site: SiteModel) -> SiteResponse:
    """Render a site with its product time.

    Args:
        site (SiteModel): The site.

    Returns:
        SiteResponse: The response.
    """
    return SiteResponse(
        id=site.id,
        name=site.name,
        kind=site.kind,
        context=site.context,
        timezone=site.timezone,
        currency=site.currency,
        now=site_clock(site),
    )


@router.get("/{site_id}", summary="Read a site")
async def get_site(site_id: UUID, principal: PrincipalDep, service: SiteServiceDep) -> SiteResponse:
    """Return an owned site.

    Args:
        site_id (UUID): The site.
        principal (PrincipalModel): The acting principal.
        service (SiteService): Site rules.

    Returns:
        SiteResponse: The site.
    """
    return to_response(await service.get_owned(site_id, principal))


@router.patch("/{site_id}", summary="Change site settings")
async def update_site(
    site_id: UUID, request: UpdateSiteRequest, principal: PrincipalDep, service: SiteServiceDep
) -> SiteResponse:
    """Change an owned site's name, context or timezone.

    Args:
        site_id (UUID): The site.
        request (UpdateSiteRequest): The changes.
        principal (PrincipalModel): The acting principal.
        service (SiteService): Site rules.

    Returns:
        SiteResponse: The updated site.
    """
    return to_response(await service.update(site_id, principal, request))
