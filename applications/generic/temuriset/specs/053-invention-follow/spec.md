# Feature Specification: Follow an invention by email (revamp R6)

**Feature Branch**: `053-invention-follow`
**Created**: 2026-11-27
**Status**: Built, awaiting review
**Milestone**: Post-M11 revamp, seventh PR of the revamps; stacked on 052
**Depends on**: 046, 050, 051, 052
**Covers**: S01, UX-01
**Size**: L
**Sources**: `reports/temuriset-invention-follow-handoff/IMPLEMENTATION-PLAN.md` and `UI-COPY.json`

## Context

The handoff's core: a signed-out visitor follows one invention from its public page with only an email, confirms by email, and gets each public update (052) the inventor publishes, in the language they chose, with links to change that language or unfollow. No account is needed. The demo seed gains public pages, illustrations and updates, so the whole path can be shown right after "Atur ulang demo".

## User Scenarios & Testing

### User Story 1 - Follow and confirm (Priority: P1)

1. **Given** an invention whose public page is on, **When** a visitor enters an email under "Ikuti inovasi ini" / "Follow this invention", **Then** the page says to check the inbox, and a confirmation email in the page's language links to `/ikuti/konfirmasi` or `/en/follow/confirm`.
2. **Given** that link, **When** opened, **Then** it shows the invention and the masked email and confirms nothing until "Konfirmasi langganan" is pressed; a used or expired link says so.
3. **Given** any address, new, pending or already following, **Then** the answer is the same `check_email`; an address that already follows gets a manage link instead of a new confirmation. An invention without a public page answers `NOT_FOUND`. Rate limits are shared with quick subscriptions.

### User Story 2 - One email per update (Priority: P1)

1. **Given** an active follower, **When** the inventor first publishes an update, **Then** the follower gets one email with the update's text, a link to the page and a manage link; a retried event sends nothing twice.
2. **Given** a follower confirmed after an update was published, **Then** that update is not sent.
3. **Given** a queued email, **When** the follower unfollows, the update is withdrawn, or the page goes off before delivery, **Then** it is dropped. Queued investor alerts and digests now also drop when an invention leaves investor news (the gap noted in revamp plan item 5).

### User Story 3 - Manage without an account (Priority: P1)

**Given** the manage link, **When** opened, **Then** the follower can change the email language or unfollow; unfollowing one invention leaves other follows and topic subscriptions untouched.

### User Story 4 - Demo-ready (Priority: P2)

**Given** "Atur ulang demo", **Then** ClearSpring and FieldDry have their public page on, a generated illustration described as one, a field-test summary and published updates.

## Requirements

- **FR-001**: Migration 0025 adds `invention_follows` (unique per invention and email), `invention_follow_links` (hashes only) and `invention_follow_deliveries` (unique per follow and update).
- **FR-002**: `POST /api/v1/follows`, `/follows/preview`, `/follows/confirm`, `/follows/manage` (read), `PUT /follows/manage` (language), `/follows/unfollow`; tokens travel in request bodies and are listed as non-data routes in the isolation harness.
- **FR-003**: Consumer `follows.update_fanout` on `invention.update_published`; mail kind `follow` carries the update id, and `deliver_secret` rechecks the follow, the update and the page before relaying.
- **FR-004**: Token pages send `Referrer-Policy: no-referrer`, are not indexed, and are left out of request logs.
- **FR-005**: Plain-text emails only, in Indonesian or English; the text-only mailbox port cannot set `List-Unsubscribe` (release risk until spec 042).
