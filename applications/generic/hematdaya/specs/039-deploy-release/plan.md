# Implementation Plan: Deployment and release

**Branch**: `039-deploy-release` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
deploy/compose.yml
deploy/Caddyfile
deploy/.env.example
docs/operations/runbook.md
../../../.github/workflows/hematdaya-release.yml
```

## Summary

Docker Compose pilot behind Caddy for automatic TLS, tagged images, one error tracker.

## Rollout

Build from a tagged source and pin the image digest. Keep the existing API serving while a one-shot migration runs. Require migrations to be compatible with the current API during the rollout. A change that cannot meet that condition needs a separate rollout plan. Start the candidate behind the proxy only after migration succeeds, and switch traffic only after readiness and contract checks pass. A failed migration or candidate health check leaves the existing proxy target in place. Rehearse switching back and verify the old API can still use the migrated schema.

Run the household and industrial oracles on `core-only` and `core-plus-optional` from the same release with the same core fixture inputs. Verify separate databases, storage, secrets and access, including a cross-deployment authorization denial. Record source tag, image digest, manifest fields, database migration head and rollback target for each installation. Preserve a synthetic-data rehearsal environment until the saved-data gates in 038 and 040 pass.

## Decisions to Take in This PR

- Host and domain, which the owner must supply. This is a paid decision and needs owner approval.
- Error tracker for EH-08. Recommended: self-hosted or free-tier Sentry-compatible.

## Test Plan

- Clean-host deploy, failed migration while the old API keeps serving, unready candidate, rollback after successful migration.
- Manifest and database match the inventory, both compositions and H/I oracles, deployment isolation, reference ID lookup.
- Https from a named phone runtime.
- 042 records the installed release builds.

## Out of Scope

Kubernetes, fleet management, SaaS tenancy, billing.

## Task Outline

1. Compose and proxy.
2. Release workflow with tags.
3. Error tracker in `record_failure`.
4. Runbook with rollback.
5. Rehearsal.
