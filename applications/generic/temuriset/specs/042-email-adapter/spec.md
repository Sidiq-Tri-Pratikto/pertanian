# Feature Specification for the gated email delivery adapter

- **Feature branch** `042-email-adapter`
- **Created** 2026-11-05
- **Status** Local readiness implemented. External delivery and activation remain gated.
- **Milestone** M12 Gated adapters
- **Flips after provider approval** Manifest adapter `email` and web registry `pemberitahuan-email` become available for an approved deployment.

**Depends on**: 027, 037

**Covers**: FR16, AC46

- **Entry condition for external delivery.** An approved provider, sender domain with SPF, DKIM and DMARC, and accepted processing terms. Local readiness uses synthetic accounts and an explicitly enabled development-only loopback relay. The release profile keeps external email off.

## User Scenarios & Testing

### User Story 1 · Codes and notifications by email, with one decision (P1)

- **Independent test.** Use the normal sign-in and invitation routes with a local relay. Verify that a delivered code works. Opt in from S18, trigger a pitch decision, make delivery fail and then retry. Count the decision, in-app notification and accepted email independently. Disable the preference before another retry and verify the relay is skipped.

1. **Given** the relay is enabled, **when** a code or invitation is requested, **then** the worker can deliver the message after the corresponding state commits, and the development mailbox is unused.
2. **Given** an opted-in account currently authorized for a notification, **when** delivery fails transiently, **then** only delivery retries and the relay accepts at most one message per event, recipient and channel (AC46).
3. **Given** preferences are off or a recipient loses access before a retry, **when** notification delivery is due, **then** the optional email is skipped and the in-app flow stays available.

## Requirements

- **FR-001** The delivery adapter MUST implement the existing `MailboxAdapter` port and be selected by validated startup configuration. Preserve development and disabled behavior. In relay mode, store only encrypted short-lived delivery material for authentication and invitations and send after the originating transaction commits.
- **FR-002** All templates MUST be Indonesian. Optional notifications send a generic action notice and an authenticated app destination. Private titles, document contents, discussion messages and decision reasons stay in the application.
- **FR-003** The account preference MUST default off, support versioned changes in S18 and govern optional notifications independently of sign-in and invitation mail. The worker MUST check live preference, verified active non-demo account and authorization for the destination party before sending. Organization delivery is limited to opted-in current members authorized for the event.
- **FR-004** Delivery MUST use an independent worker side effect with bounded backoff and stable provider idempotency keys. Retries, timeout after provider acceptance and concurrent workers MUST keep the underlying decision and the accepted email single.
- **FR-005** External delivery and launch claims MUST wait for provider and sender-domain approval and sandbox evidence. Account deletion fulfilment keeps its existing independent behavior. A production erasure receipt requires its own approved delivery policy.

## Success Criteria

- **SC-001** The loopback relay contract and local integration journey demonstrate verified code and invitation delivery, preference and authorization checks, one accepted email after retry, and the existing in-app path.
- **SC-002** An approved provider sandbox separately demonstrates delivery, sender authentication and the relay's idempotency guarantee over the retry window before activation.
