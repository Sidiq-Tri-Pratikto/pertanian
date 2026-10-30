# Implementation Plan: Deployment and release

**Branch**: `039-deploy-release` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
deploy/compose.yml
deploy/Caddyfile
deploy/.env.example
docs/operations/runbook.md
.github/workflows/release.yml
```

## Summary

Docker Compose pilot behind Caddy for automatic TLS, tagged images, one error tracker.

## Decisions to Take in This PR

- Host and domain, which the owner must supply. This is a paid decision and needs owner approval.
- Error tracker for EH-08. Recommended: self-hosted or free-tier Sentry-compatible.

## Test Plan

Clean-host deploy; failed migration; rollback; manifest equals record; reference ID lookup; HTTPS from a phone.

## Out of Scope

Kubernetes, fleet management, SaaS tenancy, billing.

## Task Outline

1. Compose and proxy.
2. Release workflow with tags.
3. Error tracker in `record_failure`.
4. Runbook with rollback.
5. Rehearsal.
