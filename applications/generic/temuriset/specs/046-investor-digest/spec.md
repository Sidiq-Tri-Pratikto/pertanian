# Feature Specification: Investor quick subscription, topic alerts and weekly digest

**Feature Branch**: `046-investor-digest`
**Created**: 2026-11-15
**Status**: Built, awaiting review
**Milestone**: Post-M11 addition (not in the original roadmap)
**Depends on**: 009, 018, 027, 031
**Size**: L
**Covers**: FR10
**Flips**: web registry `kabar-investor` → `available`

## Context

Investors can already sign up normally. Some only want to hear about inventions in their field before committing to an account. A quick subscription takes an email and topics, and sends very brief information about matching inventions: what it is, a one-line introduction, the inventor, and why the investor got it. Anything more needs a normal signup.

## User Scenarios & Testing

### User Story 1 - Quick subscription with double opt-in (Priority: P1)

An investor gives an email and topics (sectors, stages, up to five keywords) on `/langganan`. Nothing is sent to them until they confirm from the email they receive.

**Acceptance Scenarios**:

1. **Given** a new email, **When** it subscribes, **Then** the answer is "Periksa email Anda" and one confirmation email arrives; no alert or digest is sent before confirmation.
2. **Given** an email that already has an account or a subscription, **When** it subscribes, **Then** the answer is the same, so nobody learns whether an email is registered.
3. **Given** a confirmation link, **When** the investor presses **Konfirmasi langganan**, **Then** the subscription is active; opening the link alone confirms nothing, so mail scanners cannot subscribe anyone.
4. **Given** repeated requests, **When** one email or one address asks too often, **Then** `RATE_LIMITED` with a wait time.
5. **Given** outbound email is disabled, **When** someone subscribes, **Then** `MAIL_UNAVAILABLE`, and nothing is stored as active.

### User Story 2 - Inventors choose to be included (Priority: P1)

Publishing an invention does not mean agreeing to be emailed to strangers. The managing party switches on **Kabar untuk investor** per invention; it is off by default.

**Acceptance Scenarios**:

1. **Given** a published invention with the switch off, **When** a matching subscriber exists, **Then** nothing is sent and its teaser page is not found.
2. **Given** the switch on, **When** read by anyone signed out, **Then** `/temuan/{id}` shows only the title, summary, sector, stage and keywords, and the inventor's name only if their public profile is published, otherwise "Inovator di TemuRiset".
3. **Given** a member without `edit_portfolio`, **When** it flips the switch, **Then** `FORBIDDEN`.

### User Story 3 - Direct alert for a specific match, weekly digest for the rest (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an active subscriber with sector "Air dan sanitasi" and stage "Prototipe", **When** a prototype in that sector is switched on, **Then** one alert email goes out within a minute, naming the invention, one line of introduction, the inventor, and "Anda menerima ini karena cocok dengan minat Anda: sektor Air dan sanitasi, tahap Prototipe".
2. **Given** a subscriber whose keywords or sectors match only partly, **When** the weekly digest runs, **Then** the invention is in that week's digest instead.
3. **Given** an invention already sent to a subscriber, **When** it is published again or the digest runs, **Then** it is never sent to that subscriber a second time.
4. **Given** more than three direct matches within 24 hours, **When** the fourth arrives, **Then** it waits for the weekly digest.
5. **Given** a week with no new matching invention, **When** the digest runs, **Then** no email is sent.
6. **Given** a demo deployment, **When** demo inventions are switched on, **Then** alerts and digests work the same way; demo fixtures are switched on.

### User Story 4 - Leave or change topics without an account (Priority: P1)

**Acceptance Scenarios**:

1. **Given** any alert or digest, **When** read, **Then** it ends with why the investor receives it and links to change topics and unsubscribe, which need no sign-in.
2. **Given** **Berhenti berlangganan**, **When** pressed, **Then** nothing more is sent to that email.
3. **Given** the investor wants more, **When** they press **Daftar untuk melihat detail**, **Then** normal signup opens and returns to the invention afterwards.

### Edge Cases

- A subscriber never sees anything that is not already public; the email and teaser read only the public projection and the opt-in switch.
- An archived or moderated invention is never sent, and its teaser page is not found.
- Free-text keywords are matched as words, never shown back to other people.
- The reason line states a topic match only; it never claims fit, readiness or trend (invariant 6).
- Demo accounts and fixture inventions are labelled as demo data in every email.

## Requirements

### Functional Requirements

- **FR-001**: Subscriptions MUST be confirmed by a one-time token before any alert or digest, and confirmation MUST be a deliberate POST.
- **FR-002**: Tokens MUST be stored as SHA-256 hashes; manage and unsubscribe links MUST work without sign-in.
- **FR-003**: Matching MUST be explainable: a direct alert when every topic group the subscriber filled in (sectors, stages, keywords) matches; the weekly digest when at least one group matches.
- **FR-004**: Each invention MUST reach each subscriber at most once, enforced by a database uniqueness rule.
- **FR-005**: Direct alerts MUST be capped at three per subscriber per 24 hours; the rest wait for the digest.
- **FR-006**: The weekly digest MUST run every Monday at 09:00 Asia/Jakarta through a self-renewing worker job, with at most five items.
- **FR-007**: Only inventions whose managing party switched on **Kabar untuk investor** MUST be sent or shown on the teaser page.
- **FR-008**: Outbound mail MUST go through the existing mailbox port: the development mailbox, the loopback relay, or refused when disabled.

### Key Entities

- **InvestorSubscription**, **SubscriptionDelivery**, the invention's **investor_digest** switch.

## Success Criteria

- **SC-001**: Every acceptance scenario above passes against Postgres; a leak test proves private invention fields never appear in an email or teaser.
- **SC-002**: The quick subscription, confirmation, manage and teaser pages pass axe and overflow checks, signed out.
