# Tasks: Backup, restore and migration safety

**Input:** `specs/038-backup-restore/spec.md`, `plan.md`, and spec 037 deployment artifacts. The combined M11 Part 1 branch starts from M10 `eeab59e`; 038 follows 037 on this branch. Paths are relative to the pertanian repository root unless defined as an alias.

| Alias | Path |
|---|---|
| API | `applications/generic/temuriset/applications/temuriset-api` |
| PROJECT | `applications/generic/temuriset` |
| DEPLOY | `deployment/temuriset` |
| BACKUP | `deployment/temuriset/backup` |

## Phase 1: Setup

- [x] T001 Confirm the 037 services, dependency versions and local synthetic stack in `DEPLOY/compose.staging.yml` and `DEPLOY/RUNBOOK.md`. Identify the actual Alembic head under `API/migrations/versions/` and whether a trusted previous TemuRiset release exists. Do not alter existing migration revisions.

## Phase 2: Foundation

- [x] T002 Define inputs and safety preconditions in `BACKUP/README.md` and `BACKUP/.env.example`. Document compatible PostgreSQL tools, S3-compatible CLI, authenticated backup encryption tooling and key handling, source and target separation, write quiescence, bounded retention, and permission requirements. Define how the operator verifies bundle provenance from a trusted, access-controlled inventory independently of the archive. Use a dedicated backup destination and isolated empty restore targets, and reject an ambiguous or production target.

## Phase 3: User Story 1 - Restore is a rehearsed procedure (P1)

**Independent test:** In an isolated synthetic stack, quiesce writers, capture paired DB/object data, write post-snapshot sentinels, restore the encrypted pair into empty isolated targets, and verify row and object checksums, schema, and a gateway fetch. Measure the snapshot point and restore duration. Separately run old-code compatibility against the candidate schema and exercise recovery from a simulated destructive migration on disposable data.

### Tests first

- [x] T003 [P] [US1] Add backup/restore contract tests in `BACKUP/tests/test_backup_restore.sh`. Assert missing encryption keys, unverified/tampered archives, malicious archive paths or links, unsafe restore targets, partial backup failure and expired-bundle handling fail closed without overwriting data.
- [x] T004 [P] [US1] Add an integration drill in `BACKUP/tests/drill.sh` covering paired synthetic data, an authorized object, snapshot cutoff, missing/wrong objects, verification before reopening the restored instance, and recovery after a deliberately destructive change in a disposable database.
- [x] T005 [P] [US1] Add migration compatibility smoke checks in `DEPLOY/tests/migration_compat.sh`. Exercise previous-code read/write before and after the candidate upgrade, new-code reads of old writes, and blocking contract changes while the previous version remains supported.

### Implementation

- [x] T006 [US1] Implement `BACKUP/backup.sh` using a PostgreSQL custom-format dump and private S3 object copy from one coordinated recovery point. Do not bundle role passwords, environment secrets, or decrypted manifests as retained artifacts. Require proven writer quiescence for paired capture, identify source environment and actual schema/release versions, and collect an integrity manifest with schema, snapshot identifier, object paths and checksums. Register the final encrypted bundle digest in the trusted inventory. Encrypt before retaining or uploading a bundle. Use restricted temporary files, clean them on exit, and publish a bundle atomically only when both parts succeed.
- [x] T007 [US1] Implement `BACKUP/restore.sh` to verify the trusted inventory digest and authenticated encryption, reject unexpected paths and links, and check the decrypted manifest and all checksums before mutation. Use least-privilege credentials to restore to new explicitly isolated PostgreSQL and S3 destinations. Refuse nonempty/ambiguous destinations, preserve private object keys/access, and verify the restored pair before any cutover. Failed or partial restoration must never report success.
- [x] T008 [US1] Add configured retention and operator-visible failure handling in `BACKUP/backup.sh` and `BACKUP/README.md`. Apply retention only to named encrypted backup artifacts, after successful creation, with a safe dry-run path and no deletes on the live object store or database. Document key loss/rotation, role permissions, and provider-native encrypted storage as applicable.
- [x] T009 [US1] Add `.github/workflows/temuriset-migration-compat.yml` using a disposable PostgreSQL database. Resolve a trusted previous-release ref and candidate ref, apply previous migrations first and the candidate migration chain second, then run supported old API/worker compatibility checks against the upgraded DB without starting old migrations. Verify an old write survives and is readable from the new code, and check a new write through an old supported read path. Retain gate evidence with both immutable commit IDs and Alembic heads.
- [x] T010 [US1] Implement trusted ref and first-release behavior in `.github/workflows/temuriset-migration-compat.yml` and `DEPLOY/RUNBOOK.md`. PR base is acceptable for a clearly labelled development comparison. It does not count as the previous release. Require an actual previous-release comparison for AC71 once available; otherwise document the operator-approved first-release bootstrap and keep AC71 release evidence open. A candidate with the same migration head can demonstrate a no-change comparison only. Require a release comparison with a new candidate revision before marking the expand migration scenario verified. Do not execute untrusted PR code with deployment secrets.
- [x] T011 [US1] Document expand/migrate/contract and rollback vs forward repair in `BACKUP/drill.md` and `DEPLOY/RUNBOOK.md`. Require evidence of supported old/new code coexistence for expand, verify backfills before promoting new code, and require recorded retirement before destructive contract changes. Document the irreversible migration decision, recovery-data loss window and escalation owner.

### Evidence and operational gates

- [x] T012 [US1] Run the drill against an isolated synthetic 037 stack from `BACKUP/tests/drill.sh`. Record source/restore environments, matching row/object checksums, restore validation, measured UTC snapshot point, elapsed time from restore start to verified recovery, and the observed loss window between the snapshot and a post-snapshot sentinel in `BACKUP/drill.md`. If staging is available with explicit approval, repeat there and label the evidence separately. Never use real pilot data for this rehearsal. Local 037 Compose evidence is recorded in `BACKUP/drill.md`. Staging evidence remains open.
- [x] T013 [US1] Run the AC72 forward-repair or restore path once with a simulated irreversible migration on disposable synthetic data. Verify pre-change state is restored or repaired and document the measured loss window and limitations in `BACKUP/drill.md`. Keep existing migrations immutable.
- [x] T014 [US1] Run the migration compatibility smoke with available branch refs and document measured results and known limitations in `BACKUP/drill.md`. Record the exact previous release for staging acceptance or keep that evidence blocked where no trusted release exists. Use separate rows for PR-base smoke and actual release evidence.

## Phase 4: Polish

- [x] T015 Validate shell syntax, backup/restore safety, and workflow configuration; run the available checks and `PROJECT/docs/roadmap/check_traceability.py`. Update `PROJECT/specs/038-backup-restore/spec.md` to match the evidence and record remaining real-staging or previous-release gates in `BACKUP/drill.md`. Do not schedule jobs, touch existing environments, or claim a production backup was performed by this implementation.

## Dependencies & Execution Order

- T001/T002 depend on 037's usable deployment settings and runbook. T003–T005 can be written in parallel after the operational contract is defined.
- T006–T008 implement the paired backup/restore path. T009–T010 implement the independent compatibility workflow. T011 binds both to one operator procedure.
- T012–T014 collect distinct restore, irreversible-recovery, and compatibility evidence. T015 follows them. The local MVP is a measured synthetic drill and a runnable compatibility gate; actual staging acceptance remains separate.

## Requirements Coverage

| Requirement | Tasks | Evidence |
|---|---|---|
| FR-001 | T002–T004, T006–T008, T012 | Paired encrypted archive, retention, safe restore |
| FR-002 and AC71 | T005, T009–T011, T014 | Previous code against candidate schema; retirement gate |
| AC72 | T004, T007, T011, T013 | Tested forward-repair/restore and measured data-loss window |
| SC-001 and acceptance 1 | T004, T012–T015 | Measured drill using synthetic data, local vs staging distinguished |
