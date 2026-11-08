# Feature specification — Explore-first onboarding

**Status**: Implemented and verified locally
**Depends on**: 002, 012, 013, 027, 034
**Covers**: UX-02, UX-12, UX-20, AT-01, AT-02, AT-03, P01, S01, S02, S10

## US1 — Explore without setup

- FR-001. Welcome leads with **Coba demo** and offers **Lanjut tanpa data**. Neither Welcome nor Continue opens a file picker or creates a workspace.
- FR-002. The demo picker offers Household and Industrial. Confirming a choice uses the existing bounded and replay-safe demo creation.
- FR-003. Continue remains remembered on the device. Returning users resume an active workspace or see empty Home. Expiry is explained on empty Home. Settings offers optional example context.

## US2 — Add data intentionally

- FR-004. Home and Devices offer secondary **Tambah data** entry to the existing CSV screen. File selection, pasting, and workspace creation remain explicit.
- FR-005. The standalone prototype mirrors this flow. The Android smoke reaches all three tabs through Continue while its API is unavailable.

## Success criteria

- SC-001. Continue makes zero workspace requests and each successful demo confirmation makes one.
- SC-002. No file chooser opens before the file control is activated. The CSV draft and existing save behavior are retained.
