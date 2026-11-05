"""Capability manifest response schemas."""

from enum import StrEnum

from pydantic import BaseModel


class CapabilityStatus(StrEnum):
    """What a capability or adapter can honestly claim today."""

    PLANNED = "planned"
    SIMULATED = "simulated"
    AVAILABLE = "available"


class CompositionResponse(BaseModel):
    """The validated product composition of this deployment."""

    id: str
    version: int


class CapabilityResponse(BaseModel):
    """One product capability."""

    id: str
    optional: bool
    status: CapabilityStatus


class AdapterResponse(BaseModel):
    """One data source adapter."""

    id: str
    status: CapabilityStatus


class PolicyResponse(BaseModel):
    """One versioned product policy, such as matching weights or proposal expiry."""

    id: str
    version: int


class CapabilityManifestResponse(BaseModel):
    """Non-secret explanation of this deployment. It grants nothing; the service still authorizes every request."""

    schema_version: int
    source_release: str
    composition: CompositionResponse
    default_locale: str
    supported_currencies: list[str]
    capabilities: list[CapabilityResponse]
    adapters: list[AdapterResponse]
    policies: list[PolicyResponse]
