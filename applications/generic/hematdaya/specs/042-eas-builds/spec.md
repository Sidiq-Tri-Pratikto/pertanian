# Feature Specification: Native builds

**Feature Branch**: `042-eas-builds`
**Created**: 2026-10-30
**Status**: Seeded, not started
**Milestone**: M10 Platforms and usability
**Depends on**: 016, 023, 027, 029, 034, 037, 039
**Size**: M
**Covers**: AT-48
**Flips**: none

**Entry condition**: an Expo account, and Apple Developer and Google Play accounts for store builds. These are owner decisions and may cost money.

## User Scenarios & Testing

### User Story 1 - Installable builds (Priority: P1)

**Why this priority**: AT-48: Android, iOS and web individually evidenced or honestly not run.

**Independent Test**: Install on a real device.

**Acceptance Scenarios**:

1. **Given** the preview profile, **When** built, **Then** an Android APK and an iOS build install on named devices and reach the HTTPS API.
2. **Given** a release build, **When** it tries cleartext HTTP, **Then** it is blocked.
3. **Given** the platform evidence, **When** reviewed, **Then** Android, iOS and web each name the exercised runtime and build or explicitly show not run.

### User Story 2 - A real identity (Priority: P2)

**Why this priority**: The base uses solid-colour placeholders.

**Independent Test**: See icon and splash on a device.

**Acceptance Scenarios**:

1. **Given** approved brand assets, **When** built, **Then** icon, adaptive icon and splash replace the placeholders.
2. **Given** `id.hematdaya.app`, **When** confirmed by the owner, **Then** it is used for the first store upload, after which it is permanent.

### Edge Cases

- Android release builds enable R8 by default in SDK 58; test the release build, not only debug.
- iOS scene lifecycle and safe areas are checked on a device.

## Requirements

### Functional Requirements

- **FR-001**: `eas.json` MUST define development, preview and production profiles.
- **FR-002**: Evidence MUST name device, OS and build.

### Key Entities

None.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The household and industry core journeys pass on one Android and one iOS device against the HTTPS deployment from 039.
