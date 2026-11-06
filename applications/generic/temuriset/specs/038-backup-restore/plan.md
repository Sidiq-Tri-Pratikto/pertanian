# Implementation Plan: Backup, restore and migration safety

**Branch**: `038-backup-restore` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
deployment/temuriset/backup/{backup.sh, restore.sh, backup_tools.py, drill.md}
deployment/temuriset/{backup/tests/drill.sh, tests/migration_compat.sh}
.github/workflows/temuriset-migration-compat.yml   # previous release code + new migration
```

## Task Outline

1. Backup and restore scripts for Postgres and storage.
2. Rehearse the paired restore and irreversible-migration recovery on a disposable 037 topology using the current migration head. Preserve the historical M10 evidence and repeat on approved staging before pilot data.
3. Run the expand-migrate-contract compatibility workflow against the M7 base and the integrated schema. Treat an existing constraint change as an explicit compatibility decision. Separately require the protected previous release and a real changed head for release-level AC71 evidence.
4. Forward-repair procedure documented and tested once.
