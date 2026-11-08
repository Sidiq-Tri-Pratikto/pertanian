# Implementation plan — Localization foundation

Negotiate locale in ASGI before the error boundary. Use the same safety and retry envelope. For CSV, use question kind, reason, field and line information in the response mapper. Retain original persisted input and legacy Indonesian copy. Add optional display variants for observations and notices, render both from the same result, and preserve current fields and Insights cache keys. Do not duplicate evaluation or add a write path.

Add a device-local client preference and formatter context without remounting workspace providers. Set the request locale at dispatch. Use stable locale-neutral operation identities and localize status independently of response text. Keep English access behind the 050 selector. Test concurrent requests and legacy data, then run API, mobile and contract checks.
