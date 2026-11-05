"""What the engine reads: authorized projections of one source and one target. No I/O reaches past these."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class Money:
    """An exact range with what it means. ``low`` and ``high`` are None when the amount is unknown.

    Attributes:
        low (Decimal | None): Minimum.
        high (Decimal | None): Maximum.
        currency (str | None): ISO currency.
        subject (str | None): Whose amount it is, such as ``partner`` or ``investorCheck``.
        basis (str | None): ``total_period``, ``monthly``, ``yearly`` or ``per_investment``.
        months (int | None): Months a ``total_period`` amount covers.
        scope (str): What the amount pays for.
    """

    low: Decimal | None
    high: Decimal | None
    currency: str | None = None
    subject: str | None = None
    basis: str | None = None
    months: int | None = None
    scope: str = ""

    @property
    def known(self) -> bool:
        """bool: Whether both bounds are stated."""
        return self.low is not None and self.high is not None


@dataclass(frozen=True)
class Source:
    """The applicant's need or raise at one version, with the invention facts it may rely on.

    Attributes:
        type (str): ``SUPPORT_REQUEST`` or ``FUNDING_REQUEST``.
        id (str): Its id.
        version (int): Its version.
        stage (str | None): Stage of the (first linked) invention version.
        sector (str): Its sector.
        keywords (tuple[str, ...]): Published keywords of every linked invention version.
        relationship (str | None): ``PROJECT``, ``LICENSE`` or ``EQUITY``.
        facts (tuple[tuple[str, str], ...]): Fact key and timing pairs.
        authority (tuple[str, ...]): Status of each authority claim.
        entity (str | None): ``IDENTIFIED``, ``PROPOSED`` or None when unconfirmed.
        budget (Money | None): A support request's cost range.
        accepts_partial (bool): Whether partial support is accepted.
        contribution (Money | None): A raise's desired contribution per investor.
        documents (dict[str, tuple[dict[str, str], ...]]): Per fact key, the evaluation of each linked file.
    """

    type: str
    id: str
    version: int
    stage: str | None
    sector: str
    keywords: tuple[str, ...]
    relationship: str | None
    facts: tuple[tuple[str, str], ...] = ()
    authority: tuple[str, ...] = ()
    entity: str | None = None
    budget: Money | None = None
    accepts_partial: bool = False
    contribution: Money | None = None
    documents: dict[str, tuple[dict[str, str], ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Target:
    """One active opportunity version as an applicant may read it.

    Attributes:
        opportunity_id (str): The opportunity.
        version_id (str): Its current version.
        number (int): The version number.
        partner_party_id (str): The partner.
        partner_name (str): The partner's name.
        title (str): Title.
        active (bool): Whether its effective status is active.
        accepted_stages (tuple[str, ...]): Accepted stages.
        sectors (tuple[str, ...]): Sectors.
        keywords (tuple[str, ...]): Keywords.
        relationship_forms (tuple[str, ...]): Relationship forms.
        financial (Money | None): Its financial basis, when it states a range.
        requirements (tuple[dict[str, Any], ...]): Public requirements in order.
        availability (dict[str, Any]): Whether a pitch may target it now, from intake.
    """

    opportunity_id: str
    version_id: str
    number: int
    partner_party_id: str
    partner_name: str
    title: str
    active: bool
    accepted_stages: tuple[str, ...]
    sectors: tuple[str, ...]
    keywords: tuple[str, ...]
    relationship_forms: tuple[str, ...]
    financial: Money | None
    requirements: tuple[dict[str, Any], ...]
    availability: dict[str, Any] = field(default_factory=dict)
