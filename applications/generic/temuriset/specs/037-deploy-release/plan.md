# Implementation Plan: Deployment and release

**Branch**: `037-deploy-release` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
applications/temuriset-api/Dockerfile          # one image, entrypoints: api, worker, migrate
applications/temuriset-web/Dockerfile          # next build output standalone
deployment/temuriset/                          # at the pertanian root, next to existing deployment/
├── compose.staging.yml                        # api, worker, web, postgres, SeaweedFS, ClamAV, HTTPS edge
├── release-manifest.schema.json
└── RUNBOOK.md
.github/workflows/temuriset-release.yml
```

## Decisions to make in this PR

Use the binding 037 architecture: Compose on Linux, operator-provided domain and TLS, private S3-compatible SeaweedFS, ClamAV, and a build-time same-origin rewrite to the internal API. Record hosting and secret-store ownership in `deployment/temuriset/RUNBOOK.md` and the version inventory in the release manifest. Existing production promotion checks depend on actual staging, 038 recovery evidence and trusted release compatibility.

## Test Plan

Repeat API/web checks, image builds and scans, migration idempotence, manifest validation and synthetic Compose smoke against the integrated source. Preserve earlier runs with their original build identifiers. Map staging coverage to the real M7 journey tests and require actual 003/J01–J05 results on the approved HTTPS origin. Capture Editor Play and supported exports in independent prototype records.

## Task Outline

1. Images and entrypoints.
2. Staging compose and runbook.
3. Release workflow and manifest.
4. Integrated synthetic verification, followed by actual staging and independent prototype evidence when their prerequisites are available.
