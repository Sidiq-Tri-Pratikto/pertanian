# Implementation Plan: Public profiles and relationship transparency

**Branch**: `031-public-profiles-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/relationships/router.py       # GET /profiles/{party_id} (public), PATCH /profiles/me (bio, published flag)
app/relationships/service/public_profile.py
app/access/repository/            # parties gains bio and published flag
migrations/versions/0017_public_profiles.py
```

## Prototype Reference

`publicRelationships` in `domain.js`; `vm.profile`.

## Test Plan

AC55–AC57; anonymous access; private-string leak test; labels per role.

## Out of Scope

Web (032).

## Task Outline

1. Leak test and AC tests first.
2. Profile publication fields.
3. Public projection; contract.
