# Implementation Plan: Public profiles and relationship transparency

**Branch**: `031-public-profiles-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/relationships/router.py       # GET /profiles/{party_id} (public), GET and PUT /profiles/me
app/relationships/service/public_profile.py
app/access/repository/            # parties gains bio and published flag
migrations/versions/0017_public_profiles.py
```

## Prototype Reference

`publicRelationships` in `domain.js`; `vm.profile`.

## Test Plan

AC55–AC57; anonymous access; private-string leak test; labels per role.

## Integration decisions

Read current published invention titles from portfolio records on each request. The discovery worker can lag behind publication and archiving. Counterpart names, identifiers and their invention links require name consent. Send `Cache-Control: no-store` so the next signed-out read observes a restriction. The biography flag controls only the biography.

## Out of Scope

Web (032).

## Task Outline

1. Leak test and AC tests first.
2. Profile publication fields.
3. Public projection; contract.
