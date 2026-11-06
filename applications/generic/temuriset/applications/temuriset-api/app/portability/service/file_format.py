"""The bounded v1 JSON file and its source-only assertions."""

import json
from datetime import timedelta
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.errors.base import RequestInvalidError
from app.documents.service.service import FileTooLargeError
from app.intake.model.schema import PartnerProfileContent
from app.portability.model.schema import ExternalKey
from app.portfolio.model.schema import ClaimInput, DraftRequest, FactInput

MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 2_000
STAGING_LIFETIME = timedelta(hours=24)
PORTABLE_FIELDS = frozenset(
    {"title", "summary", "problem", "solution", "intended_users", "sector", "stage", "keywords"}
)
PORTABLE_CONTENT = PORTABLE_FIELDS | {"facts", "private_notes"}
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class SourceModel(BaseModel):
    """File envelope elements declare their fields explicitly."""

    model_config = ConfigDict(extra="forbid")


class SourceProvenance(SourceModel):
    """Where the source says it obtained the record."""

    source: ShortText
    observed_at: AwareDatetime | None = None


class RelationshipAssertion(SourceModel):
    """An assertion from a source, including when it claims confirmation."""

    organization_name: ShortText
    kind: ShortText
    reported_status: ShortText
    provenance: Literal["SOURCE_REPORTED"] = "SOURCE_REPORTED"


class SourceFact(FactInput):
    """A source can report a fact, but cannot assign its verification or link a private document."""

    model_config = ConfigDict(extra="ignore")

    provenance: Literal["SOURCE_REPORTED"] = "SOURCE_REPORTED"
    document_version_id: None = None


class SourceClaim(ClaimInput):
    """A source rights assertion is kept separate from the owner's claims."""

    model_config = ConfigDict(extra="ignore")

    party_id: None = None


class PortableDraft(DraftRequest):
    """Reuse portfolio constraints while treating unknown properties as unmapped."""

    acting_party_id: None = Field(default=None, exclude=True)
    expected_version: None = Field(default=None, exclude=True)
    facts: Annotated[list[SourceFact], Field(max_length=50)] = []  # type: ignore[assignment]
    claims: None = Field(default=None, exclude=True)  # type: ignore[assignment]

    @model_validator(mode="before")
    @classmethod
    def mapped_fields_only(cls, value: object) -> object:
        """Limit destination fields even when the input supplies IDs or versions."""
        if isinstance(value, dict):
            return {field: value[field] for field in PORTABLE_CONTENT if field in value}
        return value


class ExternalRow(SourceModel):
    """A source reference and the data's claimed provenance."""

    external_id: ExternalKey
    provenance: SourceProvenance


class InventionRow(ExternalRow):
    """A partial draft and claims retained independently as source metadata."""

    fields: PortableDraft
    rights_claims: Annotated[list[SourceClaim], Field(max_length=50)] = []
    relationship_assertions: Annotated[list[RelationshipAssertion], Field(max_length=50)] = []

    @model_validator(mode="after")
    def unique_fact_keys(self) -> "InventionRow":
        """Reject two inputs competing for the same stable fact key."""
        facts = self.fields.facts
        if any(same_fact(first, second) for index, first in enumerate(facts) for second in facts[index + 1 :]):
            raise ValueError("Duplicate fact key")
        return self


class PartnerRow(ExternalRow):
    """An optional profile for the already-authorized acting party."""

    organization_name: ShortText | None = None
    fields: PartnerProfileContent


class ImportFile(SourceModel):
    """The complete v1 upload envelope."""

    schema_version: Literal[1]
    external_system: ExternalKey
    provenance: SourceProvenance
    inventions: Annotated[list[InventionRow], Field(max_length=MAX_ROWS)]
    partner_profile: PartnerRow | None = None
    # Exports can carry attachments alongside inventions. Attachments are never imported as evidence.
    documents: Annotated[list[dict[str, object]], Field(max_length=100)] = []

    @model_validator(mode="after")
    def bounded_unique_rows(self) -> "ImportFile":
        """Check the combined row limit and shared external-key namespace."""
        keys = [row.external_id for row in self.inventions]
        if self.partner_profile is not None:
            keys.append(self.partner_profile.external_id)
        if not 1 <= len(keys) <= MAX_ROWS or len(keys) != len(set(keys)):
            raise ValueError("Invalid external references")
        return self


def _unique_keys(items: list[tuple[str, object]]) -> dict[str, object]:
    fields = dict(items)
    if len(items) != len(fields):
        raise ValueError("Duplicate JSON key")
    return fields


def parse_file(raw: bytes) -> ImportFile:
    """Parse the versioned file without retaining sensitive parser diagnostics."""
    if len(raw) > MAX_BYTES:
        raise FileTooLargeError("20 MiB")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
        if not isinstance(value, dict) or type(value.get("schema_version")) is not int:
            raise ValueError("Missing integer version")
        _validate_text(value)
        return ImportFile.model_validate(value)
    except (ValueError, RecursionError):
        # ValidationError and JSONDecodeError contain the supplied values.
        raise RequestInvalidError("Berkas JSON tidak sesuai skema versi 1. Periksa format lalu unggah ulang.") from None


def _reject_constant(_: str) -> None:
    raise ValueError("Nonfinite JSON number")


def same_fact(first: FactInput, second: FactInput) -> bool:
    """Use explicit keys when both facts have them, or label and timing for older facts."""
    if first.key and second.key:
        return first.key == second.key
    return (first.label.casefold(), first.timing) == (second.label.casefold(), second.timing)


def _validate_text(value: object) -> None:
    """Reject values PostgreSQL cannot store even when valid JSON escapes produced them."""
    if isinstance(value, str):
        if "\x00" in value:
            raise ValueError("NUL in JSON string")
        value.encode("utf-8")
    elif isinstance(value, list):
        for item in value:
            _validate_text(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_text(key)
            _validate_text(item)
