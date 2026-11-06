"""HTTP contracts for staged workspace portability."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

MAX_SELECTIONS = 100
ExternalKey = Annotated[str, StringConstraints(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
StageStatus = Literal["NOT_STARTED", "PENDING", "SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"]
ExportStatus = Literal["PENDING", "SUCCEEDED", "FAILED", "EXPIRED"]
PreviewAction = Literal["CREATE", "UPDATE", "UNCHANGED", "CONFLICT"]
ConflictField = Literal["facts", "rights_claims", "destination", "partner_profile"]


class PortabilityInput(BaseModel):
    """Reject unexpected request properties."""

    model_config = ConfigDict(extra="forbid")


class StartImportRequest(PortabilityInput):
    """Metadata for a bounded raw JSON upload."""

    acting_party_id: UUID
    expected_version: None = None
    map_private_notes: bool = False


class ImportActionRequest(PortabilityInput):
    """Act on the version of the run the requester reviewed."""

    acting_party_id: UUID
    expected_version: Annotated[int, Field(ge=1)]


class StageProgress(BaseModel):
    """Independent state and processed work of one stage."""

    status: StageStatus
    processed: int
    error_code: str | None = None


class PreviewRow(BaseModel):
    """Review summary without source labels, free-form values or private notes."""

    external_id: ExternalKey
    resource: Literal["INVENTION", "PARTNER_PROFILE"]
    action: PreviewAction
    mapped_fields: list[str]
    skipped_fields: list[str]
    conflicts: list[ConflictField]
    outcome: Literal["COMMITTED", "SKIPPED", "UNCHANGED"] | None = None


class ImportStatusResponse(BaseModel):
    """Private import status and a bounded page of preview decisions."""

    id: UUID
    version: int
    validation: StageProgress
    preview: StageProgress
    apply: StageProgress
    total: int
    committed: int
    skipped: int
    expires_at: datetime
    rows: list[PreviewRow] = Field(default_factory=list)
    next_offset: int | None = None
    operation_id: UUID | None = None


class InventionSelection(PortabilityInput):
    """An invention in the acting party's portfolio, from its draft or published pointer."""

    kind: Literal["INVENTION"]
    invention_id: UUID
    version: Literal["DRAFT", "PUBLISHED"]
    include_private_notes: bool = False


class DocumentSelection(PortabilityInput):
    """The exact version of a document the requester can download."""

    kind: Literal["DOCUMENT"]
    document_id: UUID
    version: Annotated[int, Field(ge=1, le=2_147_483_647)]


ResourceSelection = Annotated[InventionSelection | DocumentSelection, Field(discriminator="kind")]


class CreateExportRequest(PortabilityInput):
    """Create a job for explicit, unique resource references."""

    acting_party_id: UUID
    expected_version: None
    selections: Annotated[list[ResourceSelection], Field(min_length=1, max_length=MAX_SELECTIONS)]

    @model_validator(mode="after")
    def unique_resources(self) -> "CreateExportRequest":
        """Reject repeated references independently of field options."""
        references = {
            (row.kind, row.invention_id if isinstance(row, InventionSelection) else row.document_id, row.version)
            for row in self.selections
        }
        if len(references) != len(self.selections):
            raise ValueError("Duplicate resource selection")
        return self


class ExportStatusResponse(BaseModel):
    """Job status without a direct link to private storage."""

    id: UUID
    status: ExportStatus
    expires_at: datetime
    error_code: str | None = None
    operation_id: UUID | None = None
