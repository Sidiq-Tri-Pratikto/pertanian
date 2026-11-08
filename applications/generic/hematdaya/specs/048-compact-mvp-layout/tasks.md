# Tasks — Compact MVP layout

- [x] T008 Check Spec 047 merge and analyze the spec, plan and tasks.
- [x] T009 [US1] Add the compact frame and responsive supporting column in `applications/hematdaya-mobile/src/components/hd/HDScreen.tsx`.
- [x] T010 [US1] Group summary content on Home, Devices and Insights. Keep the single-column scope and import routes.
- [x] T011 [US1] Update the standalone prototype and sync `docs/reference/prototype/hematdaya-app.js`.
- [x] T012 [US2] Check both builds at the supported widths and enlarged text. Run applicable checks and capture evidence.

## Analysis

FR-001 and FR-002 map to T009 and T010. FR-003 maps to T011. FR-004 constrains the frame in T009 and use in T010. T012 verifies FR-001 through FR-005. Use CSS or native responsive styles to keep a stable reading order. Keep forms in the default frame and retain all confirmed state and status behavior.

## Verification evidence

- Captured five screens per runtime at 320, 390, 768 and 1280 px, before and after the change. Both builds stayed within the viewport.
- In Chrome, keyboard activation reached the household demo and chart data table at each width. Home retained the data table at 200% text. The measured heading contrast was 15.21:1. Demo entry targets measured at least 48 px in both builds.
- Mobile lint, type checking and all 576 tests passed. The serial Jest run used an extended timeout for the local host. Expo exported Android, iOS and web bundles. Prototype domain tests and traceability passed.
