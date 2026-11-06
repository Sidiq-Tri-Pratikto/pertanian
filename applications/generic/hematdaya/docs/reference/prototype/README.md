# Prototype reference

The browser prototype built in Claude Design. It is a **behaviour reference and oracle source, never production code**: it is untyped, calculates in the client, and runs on an in-browser mock backend.

| File | Use it for |
|---|---|
| `hematdaya-domain.js` | How each rule behaves: fixtures, summaries, coverage, comparison, CSV parsing, schedules, metrics |
| `hematdaya-app.js` | Screen behaviour, copy, pending and recovery states for S01–S12 |
| `domain.test.js` | 36 assertions to port to `pytest` with the same numbers |
| `ACCEPTANCE.md` | What was and was not verified in the browser. It says nothing about native or service behaviour |
| `NATIVE-HANDOFF.md` | Earlier mapping notes; `docs/roadmap/architecture.md` wins where they differ |
| `design-system-binding.json` | How the prototype bound to the design system, with deviations |

Numbers in the prototype are JavaScript; the service uses integer milli-watt-hours and decimal strings on the wire.
