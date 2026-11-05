# Implementation Plan: Deployment and release

**Branch**: `037-deploy-release` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-api/Dockerfile          # one image, entrypoints: api, worker, migrate
applications/temuriset-web/Dockerfile          # next build output standalone
deployment/temuriset/                          # at the pertanian root, next to existing deployment/
├── compose.staging.yml                        # api, worker, web, postgres, minio, clamav
├── release-manifest.schema.json
└── RUNBOOK.md
.github/workflows/temuriset-release.yml
```

## Decisions to make in this PR

Hosting target, domain and TLS, object storage provider, and how the web image reaches the API (build-time `API_URL` per environment versus a Route Handler proxy). Record each in `architecture.md`.

## Test Plan

Images build and pass Trivy; migrate job idempotent; staging smoke; 003 suite and journeys against staging; release manifest validated against its schema.

## Task Outline

1. Images and entrypoints.
2. Staging compose and runbook.
3. Release workflow and manifest.
4. Staging verification; architecture decisions recorded.
