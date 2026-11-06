# Feature Specification for the gated external calendar adapter

- **Feature branch** `043-calendar-adapter`
- **Created** 2026-11-05
- **Status** Local readiness planned. External connection and activation remain gated.
- **Milestone** M12 Gated adapters

**Depends on**: 028, 042

**Covers**: FR17, AC68
- **Flips after provider approval** Manifest adapter `calendar` and web registry `kalender` become available for an approved deployment.

- **Entry condition for external use.** A contracted calendar provider and approved consent wording for reading free and busy times. Local readiness uses an opt-in, development-only loopback provider double and synthetic calendars. The release profile keeps the adapter off.

## User Scenarios & Testing

### User Story 1 · See availability from your connected calendar (P1)

- **Independent test.** Connect a synthetic calendar from S18, propose slots in S14 and check the viewer's own busy and free results. Disconnect or interrupt the relay, then exercise slot acceptance, conflict handling and ICS.

1. **Given** the signed-in account has consented and connected, **when** it views an open proposal it is authorized to see, **then** its calendar's overlapping slots are marked busy for that viewer. Internal bookings still decide conflicts on acceptance.
2. **Given** the adapter is off, unconnected, revoked, expired or unavailable, **when** scheduling, **then** internal slots and ICS work and external availability reads “belum diketahui” (AC68).
3. **Given** the user disconnects, **when** a prior callback or lookup finishes, **then** it cannot restore the revoked connection or return its availability.

## Requirements

- **FR-001** The OAuth connection MUST use authorization code with PKCE, explicit free/busy consent, and expiring, single-use state tied to the initiating account and session. Credentials MUST be encrypted at rest and revocable. The application MUST stop using them immediately after disconnect.
- **FR-002** Only the authorized viewer's connected calendar is queried and shown. Requests and results MUST contain only the free/busy intervals required for the proposal and exclude other event data. Classifications are advisory and use half-open UTC overlap.
- **FR-003** Internal proposal, booking and ICS semantics MUST work in every adapter state. External failure MUST produce unknown availability with safe diagnostics. Disconnect MUST prevent in-flight results from being exposed.
- **FR-004** The manifest and S18 connection controls MUST reflect validated runtime availability. External activation requires the provider contract, consent approval and staging evidence.

## Success Criteria

- **SC-001** Local transport and callback tests pass, including callback replay, cross-account isolation, encrypted storage, expiry, revocation and failure privacy. The enabled and adapter-off scheduling and ICS journeys pass.
- **SC-002** The contracted provider separately demonstrates scope restriction, consent, disconnect and advisory availability in approved staging before activation.
