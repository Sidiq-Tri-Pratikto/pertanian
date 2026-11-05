# Feature Specification: Private documents, grants and download gateway

**Feature Branch**: `010-documents-api`
**Created**: 2026-11-05
**Status**: Seeded, not started
**Milestone**: M2 Portfolio and evidence
**Depends on**: 009
**Size**: L
**Covers**: FR05, AC13, AC14, AC15, AC65
**Flips**: manifest adapters `object-storage` and `file-scanner` → `available` with their configured implementations

## User Scenarios & Testing

### User Story 1 - Upload safely; availability is earned (Priority: P1)

A party uploads PDF, DOCX or images. A finished transfer is not available evidence until security and format checks pass. File, extraction and review states are separate.

**Why this priority**: FR05; preflight and pitch grants need available document versions.

**Independent Test**: Upload intent, transfer, scan and read through the API with the development scanner and the ClamAV adapter.

**Acceptance Scenarios**:

1. **Given** an upload intent declaring a 25 MB PDF, **When** it is created, **Then** `FILE_TOO_LARGE` states the 20 MB limit before any byte is sent.
2. **Given** a completed transfer still in quarantine, **When** a requirement checks document presence, **Then** the file is not `AVAILABLE` and presence is `UNKNOWN` (AC13).
3. **Given** an available but unreviewed file, **When** a `DOCUMENT_PRESENT` and a `REVIEWER_CONFIRMED` requirement are evaluated, **Then** the first passes and the second stays `UNKNOWN` (AC14).
4. **Given** a scan without supported text, **When** checks pass, **Then** the file is `AVAILABLE`, extraction is `NEEDS_MANUAL_INPUT`, and no extracted facts are invented (AC15).
5. **Given** a file whose signature does not match its extension, **When** it is checked, **Then** it becomes `REJECTED` and other draft content is unchanged.

### User Story 2 - Share one version with one recipient; revoke honestly (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a grant of version 1 to Mitra A, **When** Mitra A downloads version 1, **Then** the gateway serves it and records a download event; version 2 and other documents stay denied.
2. **Given** the grant is revoked after a download, **When** Mitra A requests the content again, including a range request, **Then** it is refused; the earlier download stays recorded, and the response and UI copy state that copies already delivered cannot be recalled (AC65).
3. **Given** an unrelated party, **When** it requests document metadata or content, **Then** it gets `NOT_FOUND` with no title.

### Edge Cases

- An interrupted transfer keeps the draft and the intent can be retried until it expires.
- A new version supersedes the old version's review state but never its grants.
- `development-accept` scanner marks files available after format checks, only in development; startup refuses it elsewhere (rule from 004).
- Media type is sniffed from bytes, not trusted from the client.

## Requirements

### Functional Requirements

- **FR-001**: Documents MUST default to private, owned by a party, versioned, with checksum and generated storage keys.
- **FR-002**: File states MUST be `CREATED`, `UPLOADING`, `QUARANTINED`, `AVAILABLE`, `REJECTED`; extraction `NOT_REQUESTED`, `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`, `NEEDS_MANUAL_INPUT`; review `PROVIDED_UNREVIEWED`, `REVIEWED_SUPPORTED`, `REVIEWED_UNSUPPORTED`, `NEEDS_CLARIFICATION`, `EXPIRED`, `SUPERSEDED`.
- **FR-003**: Limits MUST be 20 MB for PDF and DOCX and 5 MB for images, announced before upload; video is an HTTPS link only.
- **FR-004**: Scanning and extraction MUST run as worker jobs; macros and embedded HTML are never executed.
- **FR-005**: Grants MUST name one version, one grantee party and one purpose; revocation MUST block every new request.
- **FR-006**: The gateway MUST re-authorize every request, including ranges, and never issue a client-visible storage URL.

### Key Entities

- **Document**, **DocumentVersion**, **UploadIntent**, **Grant**, **DownloadEvent**, **StorageAdapter**, **ScannerAdapter**.

## Success Criteria

### Measurable Outcomes

- **SC-001**: AC13–AC15 and AC65 pass; a fake secret in a filename appears in no log.
- **SC-002**: A 20 MB upload completes and streams back without loading the whole file into memory.
