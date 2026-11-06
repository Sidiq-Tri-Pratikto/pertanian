# TemuRiset recovery rehearsal

## Historical local synthetic evidence on the M10 base

Run `deployment/temuriset/backup/tests/drill.sh --compose` with Docker Compose, OpenSSL, GnuPG, PostgreSQL client tools, and the locked API Python environment. Set `TEMURISET_API_IMAGE` and `TEMURISET_WEB_IMAGE` to the local images to exercise. The script creates a new disposable spec 037 project with synthetic identities, private files, and temporary loopback-only access for the backup client. It verifies the same application image IDs before and after recovery and removes the project and volumes at exit.

| Integrated Compose check | Result |
| --- | --- |
| Runtime | Project `temuriset-backup-drill-5205212342`, PostgreSQL 16.15, spec 037's pinned SeaweedFS, and ClamAV 1.4.6. Local API image `sha256:ae00ebeb883fd7e665ccb26eb7ce94dcb99c2ea0a2037a16ab31186ac4d54899` and web image `sha256:b8eb16b4556e21b263750a6873315f909d81f762e4f3e9ae1b90098955fa7a6e` were built from the local worktree based on `eeab59e15b675d033df5f6072e8808a0116277a6`. |
| Source and target | Fresh Compose volumes and the `temuriset` source DB, separate `temuriset_restore_5205212342` DB, and dedicated source and restore buckets. The source Compose worker scanned the PDF before capture. |
| Capture and recovery | Stopped writers and verified the Compose fence. Missing and corrupted objects caused backup to fail before publishing. After recording the valid encrypted snapshot, dropped `document_versions` with its dependent foreign keys and deleted the source object. Recovered the matching row and object into the fresh target pair. |
| Recovery point and observed loss | Alembic `0009`, snapshot 2026-11-05 18:12:22.185316 UTC. Sentinel written at 18:12:24.084787 UTC was absent after recovery. The 1.899 s difference measures this fixture's post-snapshot write. |
| Recovery time | 1.211 s inside the restore command. 11.082 s from restore start through row verification, restored API and web startup, and HTTPS gateway verification. Provisioning and investigation are outside this measurement. |
| Row fingerprint | `17a171c7d3f57c79b789dd70dcf91aaccb5b5450a76ab9d6c0600ab97f772994` over the storage key, checksum, byte size and file state. |
| Object and access | One recovered PDF with SHA-256 `8da40be05f62ae93cd00aea53618c796fb7bc19d2bbab2e5b09bd0a87428bc7a`. Nginx, Next.js and the API gateway returned HTTP 200 to the grantee and HTTP 404 to an unrelated signed-in user before and after restore. |

### Standalone component check

Without `--compose`, the script also supports a local component check using a native loopback PostgreSQL cluster, the pinned SeaweedFS image, and the current worktree ASGI gateway. This check requires the PostgreSQL server tools and uses the synthetic mailbox and scanner.

| Check | Result |
| --- | --- |
| Recorded snapshot | 2026-11-05 18:06:01.792621 UTC, Alembic `0009`. Local worktree based on `eeab59e15b675d033df5f6072e8808a0116277a6`. |
| Source and target | Disposable PostgreSQL databases and S3 buckets, restore pair ID `be8bb400ce`. No pilot data. |
| Missing or corrupted object | Both capture attempts failed before publishing an encrypted bundle. Restored the original fixture bytes before the successful capture. |
| Irreversible change | Wrote a sentinel, dropped `document_versions` and its dependent foreign keys on the disposable source, then deleted its object. Restored the encrypted pre-change snapshot into the empty target pair. |
| Loss observed | Sentinel written at 2026-11-05 18:06:03.302288 UTC was absent on the restored database, a 1.510 s interval from the recovery point. This measures the fixture's post-snapshot write, not an operating RPO. |
| Recovery time | 1.104 s inside the restore command. 3.543 s from restore start through verified row and gateway access. This excludes provisioning, investigation and cutover. |
| Restored row | One matching document row, fingerprint `f00a525397aa5579a90eaeb256021e5d4114df01b1cdc95ee08586780433a95a` over storage key, checksum, byte size and file state. |
| Restored object | One matching PDF, SHA-256 `8da40be05f62ae93cd00aea53618c796fb7bc19d2bbab2e5b09bd0a87428bc7a`. |
| Gateway | A signed-in user with a grant received HTTP 200 and matching PDF bytes. An unrelated signed-in user received HTTP 404. Both checks passed before and after recovery. |

## Integrated local synthetic rehearsal at Alembic 0014

The Compose drill on 6 November 2026 used a disposable project `temuriset-backup-drill-12eada77c0` from the integrated worktree based on `485028dbf28d9d755c2cf1462e9afb2778ea68bd`. Its source and restore gateways used API image ID `sha256:9caf020485e34b613ed1ac035e995e68f95d593f8d76595cb69f1df3ac4630ae` and web image ID `sha256:f8da088f3bb0fa60c1ecc1447cbc73f6f4aa8e038396a63c80b32fe469c7c0fd`.

| Check | Result |
|---|---|
| Capture and destructive change | Quiescence was verified before capture. Missing and changed objects both blocked backup publication. After the valid encrypted snapshot, the drill inserted a sentinel, dropped `document_versions` and its dependent foreign keys, and removed the source PDF. |
| Recovery point and loss observed | Schema `0014`, snapshot `2026-11-06T02:12:26.189575Z`. The sentinel written at `02:12:40.068501Z` was absent from the restored database. The 13.879 s interval measures the fixture's write after the snapshot. |
| Recovery time | Restore command 7.094 s. Recovery through restored HTTPS gateway verification 42.306 s, including app restarts and the row and access checks. Provisioning and incident investigation are outside the measurement. |
| Verified pair | One restored row with fingerprint `b4e77a72d50cfa3baac4e2d5e4caeaaa3725caadb2e9666924f7dd9cfe55c5a3` over storage key, checksum, byte size and file state. One PDF with SHA-256 `8da40be05f62ae93cd00aea53618c796fb7bc19d2bbab2e5b09bd0a87428bc7a`. The granted request returned 200 and the ungranted request 404 before and after restore. |

## Final integrated local synthetic rehearsal at Alembic 0015

On 6 November 2026, `deployment/temuriset/backup/tests/drill.sh --compose` exercised the disposable project `temuriset-backup-drill-ae0397d7c7` from assembled source `eae3900618b9481dfd6222185ecac006b6acfb2a`. The source and restore gateways used API image ID `sha256:996c2c17f15bd3afced562ece92cb1ac1be5bf9d20c4cf43f751204ba9c0089a` and web image ID `sha256:6ec51021c76acdf882c0187f34fe6f4dc5453a2fefd5ffb92189e14f3ae0a01e`.

| Check | Result |
|---|---|
| Capture and destructive change | Missing and changed objects each blocked bundle publication. After a valid encrypted snapshot, the drill inserted a sentinel, dropped `document_versions` and its dependent foreign keys, and deleted the source PDF. |
| Recovery point and observed loss | Schema `0015`, snapshot `2026-11-06T02:32:13.960395Z`. The sentinel written at `02:32:16.099459Z` was absent after restore. The 2.139 s interval measures this fixture's write after the snapshot. |
| Recovery time | 3.939 s inside the restore command. 20.205 s from restore start through row verification, app restarts and HTTPS gateway checks. Provisioning and investigation were outside the measurement. |
| Verified pair | One restored row with fingerprint `99112d165067bf3e372505d9a65c1a5d10949424ad29393b1cfc927f82f391a2` over storage key, checksum, byte size and file state. One PDF with SHA-256 `8da40be05f62ae93cd00aea53618c796fb7bc19d2bbab2e5b09bd0a87428bc7a`. The grantee received 200 and the ungranted user 404 before and after restore. |

## Migration compatibility evidence

| Comparison | Evidence |
| --- | --- |
| PR-base smoke | Archived M10 base `eeab59e15b675d033df5f6072e8808a0116277a6` against the local candidate worktree, using PostgreSQL 16.11. Alembic `0009 → 0009`. The old API read and wrote after upgrade, the candidate read old writes, the old API read a candidate write, and jobs ran through both worker versions. Same-head smoke only. |
| Synthetic expand | Same base against a disposable copy with a synthetic additive `0010` creating a table. Alembic `0009 → 0010`, with both API versions and both workers passing the same coexistence checks. |
| Synthetic contract | Same base against a disposable copy with a synthetic `0010` dropping an existing table. The check rejected the change to existing schema signatures. Repository migration files were untouched. |
| M7 integration comparison | Archived M7 `d6cb95f3df2cc8c9fd18b5391d03b3b7b856218d` against the local integrated worktree at `485028dbf28d9d755c2cf1462e9afb2778ea68bd`. PostgreSQL 16.11, Alembic `0013 → 0014`. The compatibility guard exited 1 on replacement of `document_versions.file_state`. This is a non-passing development comparison. |
| Stacked PR-base comparison | M10 `49a99fdd9805fa75716e782650db5dcb6a076491` against candidate commit `eae3900618b9481dfd6222185ecac006b6acfb2a`. Alembic `0014 → 0015`. Both APIs read and wrote the tested records and both workers processed the supported job probe. This is PR-base evidence for a changed head. |
| Actual previous release | Open. No trusted `temuriset-vX.Y.Z` release exists. Once available, dispatch **TemuRiset migration compatibility** from protected `main` with the tag and matching commit SHA from the trusted release inventory. Keep the workflow artifact with the change record. AC71 requires a passing actual-release comparison with a new Alembic head. |

The 0013 check allowed `CREATED`, `UPLOADING`, `QUARANTINED`, `AVAILABLE` and `REJECTED`. Revision 0014 adds `ERASURE_PENDING` and `ERASED` to that set. In an independent disposable probe on the upgraded database, the old owner metadata serializer returned both new strings with HTTP 200, rejected non-owner metadata with 404 and refused owner and grantee content with `FILE_NOT_AVAILABLE`. The old scanner left both rows unchanged. A separate real candidate deletion revoked the owner session (the old API returned 401) and the download grant (the old API returned `GRANT_REVOKED`). The old worker claimed the newly enqueued `documents.erase` job as `NEEDS_MANUAL_INPUT:UNKNOWN_JOB_KIND`, leaving the request `PROCESSING` and the version `ERASURE_PENDING`.

Coexistence across 0014 therefore fails. Retire all old workers and API instances before enabling candidate erasure. If an old worker has already stranded a deletion job, keep writers paused while the data steward chooses a verified forward repair or a paired restore from before the change. The migration guard deliberately retains the generic constraint-change rejection.

The release manager and data steward must record approval for a first-release bootstrap with no prior deployed version. Retain the PR-base result as development evidence and keep AC71 open. A same-head previous-release run also leaves the expand scenario open.

## Recovery and migration decisions

1. **Expand.** The release manager records the old and candidate image digests, Git commits and Alembic heads. Take a paired backup and require old/new API and worker coexistence evidence before deploying an additive schema. Keep the old version running until both code versions can read and write supported data. Drain and stop old workers before any producer can enqueue a newly introduced job kind. Apply this ordering even to additive schema changes when old workers can claim jobs without a handler.
2. **Migrate.** Run a bounded, repeatable backfill. Check completeness and values on representative synthetic cases before promoting candidate traffic. The host operator records the checks and live schema.
3. **Contract.** Remove obsolete schema only after the release manager records retirement of all old API and worker instances and dependent jobs. The compatibility workflow deliberately rejects removed or changed existing columns and constraints and new constraints on existing tables. Plan a separate contract change after retirement.
4. **Recover.** The host operator pauses writers, preserves evidence and escalates to the data steward. For a compatible schema, restart the previous pinned code without running old migrations. For an irreversible change, keep traffic paused while the data steward selects a tested forward repair or authorizes a verified paired restore. A forward repair must preserve or reconcile data affected by the change. A restore can discard writes after the recorded snapshot. Record the affected interval and reconcile those writes before cutover. Verify the restored schema, representative rows, object hashes and granted and ungranted gateway access before reopening traffic.

Staging rehearsal remains open. Repeat with approved synthetic data and named owners from the [staging runbook](../RUNBOOK.md). Record the actual RTO and recovery point in the change record before accepting staging readiness.
