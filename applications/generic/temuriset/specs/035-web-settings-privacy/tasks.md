# Tasks: Profile, privacy and reports screens

**Input**: `specs/035-web-settings-privacy/spec.md`, `plan.md`, reconciled with spec 034 and the M7 main baseline at `d6cb95f`. Checked boxes describe the carried implementation
**Integration**: M10
**Tests**: Write behavior tests first and observe the relevant failure before implementing the behavior. Record a blocked dependency separately from a failing test.

**Paths** start at `applications/generic/temuriset/applications/temuriset-web/`.

## Decisions resolved against the code

| ID | Decision | Why |
|---|---|---|
| D1 | `/settings?lapor=<type>&objek=<id>#laporkan` prefills a validated subject type and opaque ID. The form may show the generic subject kind in Indonesian. Titles, labels, and reasons stay out of URLs. An invalid pair leaves a usable blank report form. Add a link for other parties' profiles on S08. Add the same opaque prefill to the authorized S13 workspace from spec 026. | US1 scenario 3 requires entry from the room itself. The partner-profile link and direct prefill test cover separate paths. |
| D2 | Before submission, the deletion dialog explains what requesting deletion does and that some data may be kept under policy. After submission, render the server's categories as "Akan dihapus", "Sudah dihapus" and "Tetap disimpan", with the retention reasons and periods it returns. | 034 generates the answer from policy and fulfils requests separately. The client has no retention policy of its own and shows removal only when the API confirms it. |
| D3 | Download through a fresh, same-origin, authorized `GET /api/v1/privacy-requests/{id}/export`. Save the file only after a successful response. Handle denial, session expiry and fetch failures in S18 through the shared failure envelope and recovery behavior. | 034 builds an export under current permissions on each read. The requester needs an actionable error in the screen if access or network conditions change. |
| D4 | Map the report categories from the generated 034 contract to Indonesian labels and default to `OTHER` ("Lainnya"). The label is editable free text and the reason is required. | FR22 and the API contract define the reporting vocabulary. |
| D5 | The operator queue has no screen in this spec. | 035 lists only the three user actions. Operators use the API. |
| D6 | Use the request and response types generated from 034. Send the current `acting_party_id`, the create-version value required by 034, and one `Idempotency-Key` per intent. Retry the same intent with the same body and key. Keep the draft and last confirmed result on failure. | Constitution principles 11 and 12. The generated contract defines `expected_version` for creation and the server owns authorization and state. |

---

## Phase 1: Setup and contract

- [X] T001 Confirm the signed-in S18 and acting-party context from 008. Wait for 034 to publish its report and privacy creation, status and export routes, including the agreed first-create `expected_version` semantics and failure envelope. Confirm its `make openapi` output in `../../contracts/openapi.json` and refresh `src/api/schema.generated.ts` with `make generate-api` if needed. Use the generated types and resolve any missing contract in 034 before proceeding.

## Phase 2: User Story 1 - Report, export and delete with honest explanations (Priority: P1) 🎯 MVP

**Independent Test**: Open S18, correct an empty report, follow its case status, request and download an export, and confirm a deletion request that returns retained categories. Repeat with an expired session or denied access. Exercise the pitch-room entry in Phase 3.

- [X] T002 [US1] Write failing contract and boundary tests in `tests/privacy.test.tsx`. Cover valid, malformed and absent subject prefill, including a `PITCH` ID and a URL with an ignored label. Assert the three creation actions send the agreed 034 body and version, active party, and a stable key on retry. Cover a changed intent using a new key, and status and download failures carrying the actionable message, reference ID and recovery behavior.
- [X] T003 [US1] Write generated-type mappings, labels, safe subject-prefill parsing and link construction in `src/features/privacy/model.ts`. Add status reads, mutations and the authorized download in `src/features/privacy/api.ts`. Reuse the same-origin API helpers and failure parsing, with a bounded request timeout and recovery limits.
- [X] T004 [US1] Add failing view tests in `tests/privacy.test.tsx` and route tests in `tests/pages.test.tsx`. Cover an empty reason focusing the linked summary and sending nothing, report case number and status, a deletion dialog that sends only on confirmation, pending versus fulfilled deletion and server-provided retention reasons, export success and denial, and status on revisit. Cover loading, empty, success, failure, permission denial, retries retaining the draft, the two FR-001 statements, and axe on each new view. In `tests/intake.test.tsx`, cover the S08 prefill link for other parties and the `SUSPENDED` label.
- [X] T005 [US1] Implement `src/views/settings/ReportForm.tsx`. Use D1 and D4, show the acting party before sending, and display the private case number and status. Preserve the reason on failure, focus the linked error summary for invalid input, and announce status without stealing focus. Include the FR-001 explanation about reputation.
- [X] T006 [US1] Implement `src/views/settings/PrivacyRequests.tsx` with export, deletion confirmation, status, and the two distinct download outcomes from D3. Reuse `TR.Dialog`, preserve confirmed content on failure, show the acting party before confirmation, and render the authoritative response and copy about already-downloaded copies from FR-001.
- [X] T007 [US1] Integrate both sections in `src/views/SettingsView.tsx` and `src/app/settings/page.tsx`. Use 034's authorized status reads with the active session. Render denied and failed states without revealing restricted objects or replacing the rest of S18. Use the existing loading, status and failure patterns.
- [X] T008 [US1] Add "Laporkan" for other parties in `src/views/intake/PartnerView.tsx` using D1, and map the generated `SUSPENDED` reason in `src/features/intake/model.ts`.

## Phase 3: Browser acceptance and pitch-room entry

- [X] T009 [US1] Add `e2e/privacy.spec.ts` cases for a private report from S08 with prefill, validation and status after reload, deletion with retained reasons, and a downloaded export containing the requester's data. Cover expiry or denied download without leaving S18 or creating a file. Keep the existing `/settings` entries in `e2e/routes.ts`. In the privacy suite, check the new controls at 320 CSS px and 200% text, keyboard open, focus, Escape and return focus for the confirmation dialog, error-summary focus, and announcement of completion.
- [X] T010 [US1] Reuse the real pitch setup from 026's J03 browser case through `e2e/fixtures.ts`. In `e2e/privacy.spec.ts`, open that pitch room, click "Laporkan", reach S18 with that pitch's `PITCH` subject ID, and submit a report that shows the case number. Assert the URL omits the pitch title and private form text. Verify an unrelated account sees the no-access view with no reporting link or title.
- [X] T011 [US1] After T010 establishes the missing behavior, wire "Laporkan" in `src/views/pitches/WorkspaceView.tsx` for the authorized room using D1, or reuse the matching link if 026 already provides it. Run the room case against the real route and confirm US1 scenario 3 passes.

## Phase 4: Availability and closure

- [X] T012 After T001–T011, run the focused view and axe tests in `tests/privacy.test.tsx` and the browser tests in `e2e/privacy.spec.ts`. Confirm each US1 scenario, including the room case. Until the room case passes, keep `privasi-laporan` at `coming_soon` in `src/features/registry.ts` and 035 open.
- [X] T013 After T012 passes, update `tests/registry.test.ts` and `tests/pages.test.tsx` for the new availability and flip `privasi-laporan` to `available` with `home: '/settings#laporkan'` in `src/features/registry.ts`.
- [X] T014 Update the `/settings` row in `README.md`.
- [ ] T015 From the project folder, run `python3 docs/roadmap/check_traceability.py`, `make check` and `make e2e`. Read the output and record which checks ran, including the required room case. Resolve any failures before closure.
- [ ] T016 After T015 passes, set **Status** to `Built, awaiting review` in `../../specs/035-web-settings-privacy/spec.md`.

## Requirement coverage

| Requirement | Tests | Implementation |
|---|---|---|
| US1 scenario 1 (report validation, case and status) | T002, T004, T009 | T003, T005, T007 |
| US1 scenario 2 (deletion and retention) | T004, T009 | T003, T006, T007 |
| US1 scenario 3 (pitch-room entry) | T010, T011 | T003, T005, T007, T011 |
| US1 (request export, download and status) | T002, T004, T009 | T003, T006, T007 |
| FR-001 (downloaded copies and reputation) | T004 | T005, T006 |
| SC-001 (views, axe and browser report flow) | T004, T009–T012, T015 | T003, T005–T008, T011 |
| Registry availability | T012, T013, T015 | T013, gated on all acceptance scenarios |

## Dependencies & Execution Order

- 008 and the generated contract from 034 gate T001. Contract and boundary tests precede T003. View tests precede T005–T008.
- T009 can run when the S18 and S08 work is ready. T010 and T011 use the authorized workspace from 026. The remaining availability and closure tasks wait for the room case to pass.

## Implementation Strategy

Preserve the carried S18 and S08 behavior. Finish the real pitch-room case before changing the registry and recording integrated validation.

## Carried validation before integrating 026

- Web lint, typecheck and the production build passed. Vitest passed 203 tests at 89.06% line coverage with two workers and a 20-second per-test timeout on this host.
- Chromium passed the three implemented privacy scenarios and the narrow Settings axe and reflow checks. The 026 workspace entry case remains required for closure.


## Integrated validation on M7

- The new Chromium case reached an authorized pitch room and failed while waiting for the missing report link before implementation. After wiring the link, all four privacy journeys passed against the production web build, including the private report and unrelated-account cases. Twelve runs were skipped as expected because each journey names its target viewport.
- The six focused Vitest cases passed, including the privacy view axe checks.
