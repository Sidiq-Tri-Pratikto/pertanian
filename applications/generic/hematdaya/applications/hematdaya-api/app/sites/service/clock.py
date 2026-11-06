"""The one source of product time."""

from datetime import datetime

from app.core.clock import wall_now
from app.sites.model.models import SiteKind, SiteModel


def site_clock(site: SiteModel) -> datetime:
    """Return product time for a site: the virtual clock of a demo, the wall clock otherwise.

    Periods, staleness, snooze and "today" use this. Audit, expiry and security use ``wall_now``.

    Args:
        site (SiteModel): The site.

    Returns:
        datetime: Timezone-aware now for that site.

    Raises:
        ValueError: When a demo site has no virtual time. The database forbids it, so this signals corruption.
    """
    if site.kind is SiteKind.DEMO:
        if site.virtual_now is None:
            raise ValueError("A demo site must carry its virtual time.")
        return site.virtual_now
    return wall_now()
