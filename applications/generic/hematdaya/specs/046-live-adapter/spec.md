# Feature Specification: Live meter adapter

**Feature Branch**: `046-live-adapter`
**Created**: 2026-10-30
**Status**: Seeded, gated
**Milestone**: M11 Live meter
**Depends on**: 006, 035
**Size**: L
**Covers**: FR-04, FR-05, AT-42, S05, P07
**Flips**: lab enrollment behind the pilot flag. Verified model release support follows G3–G5.

## Isolated lab scope

Shelly Plug PM Gen3 only. An operator provisions a real-time standard site, assigns one meter UUID and issues an expiring, revocable opaque code for the owner. Keep the code only in client memory and scope it to that assignment. The feature is disabled by default. Public enrollment uses the separate owner account and release lane.

The pilot monitors one compatible plug-in appliance as one new asset. Verify the actual meter and installation against a reference meter before field sign-off.

## User Scenarios & Testing

### User Story 1 - First real reading (Priority: P1)

1. An eligible owner enters the lab code and starts enrollment. The app shows waiting until the server validates a reading from the assigned meter.
2. With a valid reading, the app shows ready to confirm. Confirmation creates one asset, source, effective binding and accepted first cumulative-energy reading atomically. The first reading anchors the counter. Interval energy requires a later valid reading. Only then does the app show connected and link to the monitored asset.
3. A retry with the same operation identity and payload returns the original result. An expired pending enrollment cannot create data. A revoked credential or wrong site/meter cannot read or change the enrollment.
4. Subsequent accepted readings appear through the existing energy and history views. If readings stop for more than two expected intervals, show stale data with the last reading time.

### User Story 2 - Preserve telemetry provenance (Priority: P1)

1. Resolve site and meter from authenticated server assignments. Reject wrong, revoked or forged identities and invalid readings.
2. Preserve the source and measurement timestamps. Handle duplicate deliveries without counting energy twice.
3. Verify that the credentials and routes grant access to measurement only. Device and collector secrets stay out of the app.

## Requirements

- **FR-001**: Use `IngestService` for normalized readings. Show historical CSV and simulated data with their existing provenance.
- **FR-002**: Use an authenticated, TLS-protected collection boundary with per-source authorization. A device path that exposes control capabilities to the collector is ineligible for field sign-off.
- **FR-003**: Apply the pilot flag and the owner, assignment, expiry and revocation checks at the server boundary. Confirmations MUST be atomic and replay-safe.

## Release gates

The isolated lab validates the integration without opening a public saved-data service. User-facing release requires owner accounts and recovery (036/037), data rights (038), HTTPS deployment (039), retention and restore evidence (040), platform/usability evidence (042–044), and physical reference comparison and quality evidence (G5). Record tested firmware, load, installation and reference conditions. Label missing physical or platform evidence as pending.
