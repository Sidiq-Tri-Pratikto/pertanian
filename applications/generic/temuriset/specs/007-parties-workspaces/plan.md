# Implementation Plan: Parties, organizations and memberships

**Branch**: `007-parties-workspaces` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/access/
├── router.py                     # /organizations, /organizations/{id}/members, /invitations, /me/context
├── model/{models.py, schema.py}  # Principal, PartyReference, Capability enum
├── repository/sqlalchemy/{models.py, repository.py}   # organizations, memberships, invitations; parties gains organization kind
├── service/service.py            # create organization, invite, accept, revoke, remove member, set context
└── service/policy.py             # require(principal, action, resource); visible(principal, resource)
app/core/security.py              # principal now carries active party and capabilities; STALE_CONTEXT check helper
tests/integration/test_isolation.py   # walks the route table as an unrelated party
migrations/versions/0003_access.py
```

## API Contract

- `POST /api/v1/organizations` `{name, kind}` → organization with party id.
- `GET /api/v1/organizations/{id}/members`; `DELETE /api/v1/organizations/{id}/members/{account_id}` with `expected_version`.
- `POST /api/v1/organizations/{id}/invitations` `{email, capabilities}` → invitation; the mailbox receives the link.
- `POST /api/v1/invitations/{token}/accept`; `POST /api/v1/invitations/{id}/revoke`.
- `PUT /api/v1/me/context` `{party_id}` → `Me` with `active_party_id` and `capabilities`.

Codes: `FORBIDDEN`, `STALE_CONTEXT` (409), `INVITATION_EXPIRED` (410).

## Test Plan

AC04, AC05, AC06 (job from 005 started by a removed member); invitation expiry and revocation; last manager protected; stale context; isolation harness with a fixture route.

## Out of Scope

Organization review gates (033), web screens (008).

## Task Outline

1. Migration, policy tests first.
2. Organizations, memberships, invitations.
3. Active context and stale-context check.
4. Isolation harness.
5. Codes, catalog, contract.
