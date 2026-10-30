# Implementation Plan: Backup and restore

**Branch**: `040-backup-restore` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
deploy/backup/{backup.sh, restore.sh}
applications/hematdaya-api/scripts/reconcile.py
docs/operations/backup-restore.md
```

## Summary

`pg_dump` to off-host storage, a restore procedure, and a reconciliation check.

## Test Plan

Backup, destroy, restore, reconcile; replay; deletion after restore.

## Out of Scope

Point-in-time recovery unless a pilot needs it.

## Task Outline

1. Backup job.
2. Restore script.
3. Reconciliation.
4. Rehearsal record.
