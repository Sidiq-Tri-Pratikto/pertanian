# Implementation plan — Explore-first onboarding

Use the existing Expo route, workspace provider, demo picker, import draft and Settings. Store a device-only boolean in AsyncStorage and wait for hydration when routing Welcome. A storage failure leaves Continue functional for the current process. Use the existing empty Home route and session-end notice. Keep demo confirmation on the existing idempotent session path.

Render **Tambah data** as a secondary link to the first import step. Keep file opening in the existing document picker and retain its explicit temporary workspace start. In the prototype, keep its local empty model as the client-only representation of empty Home. Use browser preference storage for returning users.

Check router regressions before implementing. Exercise both demos, picker intent, return and expiry. Run prototype domain tests, Expo web and standalone browser checks, mobile lint/typecheck/tests/export, and the hosted API-absent Android smoke. Record observed evidence and limitations.
