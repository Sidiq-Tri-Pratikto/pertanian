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

Restore to an isolated database. Bring in the current deletion ledger kept separately under 038, reapply outstanding deletions and revoke associated export access before any restored API is made ready. Reconcile scope-safe summaries with raw readings for retained sites and rerun import replay. An unavailable ledger, failed check or unexplained difference keeps traffic disabled. Record the snapshot cutoff, recovery time, retention settings and evidence of deletion reconciliation.

## Test Plan

On a disposable environment, back up before a site deletion, delete the site, restore the older snapshot and apply the latest deletion ledger. Verify retained totals, replay idempotency and denial of both site and old export access. Test a missing ledger and an expired backup. Record date, size and restore duration.

## Out of Scope

Point-in-time recovery unless a pilot needs it.

## Task Outline

1. Backup job.
2. Restore script.
3. Reconciliation.
4. Rehearsal record.
