# Implementation Plan: Backup, restore and migration safety

**Branch**: `038-backup-restore` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
deployment/temuriset/backup/{backup.sh, restore.sh, drill.md}
.github/workflows/temuriset-migration-compat.yml   # previous release code + new migration
```

## Task Outline

1. Backup and restore scripts for Postgres and storage.
2. Drill on staging, timings recorded.
3. Expand-migrate-contract compatibility workflow.
4. Forward-repair procedure documented and tested once.
