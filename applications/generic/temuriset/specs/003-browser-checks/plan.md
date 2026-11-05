# Implementation Plan: Browser checks in CI

**Branch**: `003-browser-checks` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Summary

Add `@playwright/test` and `@axe-core/playwright` to the web app, a `make e2e` target that builds, starts the web app against a live API and runs the suite, and a CI job with Postgres and the API.

## Project Structure

```text
applications/temuriset-web/
├── playwright.config.ts           # chromium; projects per viewport; webServer: next start on 3020
├── e2e/
│   ├── fixtures.ts                # persona cookie helper; later: signed-in account helper (008)
│   ├── routes.ts                  # every route and its persona, one list shared by all checks
│   ├── overflow.spec.ts           # 320/360/768/1280 and 200% text at 320
│   ├── axe.spec.ts                # @axe-core/playwright, all rules
│   └── keyboard.spec.ts           # skip link, focus visible, not under the tab bar
└── Makefile                       # e2e: build, start API_URL=..., playwright test
.github/workflows/temuriset-web.yml  # new job: postgres service, API via uv, make e2e, upload report
```

## Prototype Reference

`docs/generic/temuriset/app-prototype/tools/journeys.browser.js`: `audit()` for overflow, `scan()` for names, duplicate ids, one h1 and targets. Port the logic, not the walker.

## Test Plan

The suite itself is the test. Add one deliberate-failure check per category in a throwaway branch to prove each assertion can fail, and record that in the PR description.

## Out of Scope

Journey tests (024, 026, 029, 032), screen-reader runs (040), visual regression snapshots.

## Task Outline

1. Install Playwright and axe; `playwright.config.ts` with webServer.
2. Shared route list with personas.
3. Overflow, axe and keyboard specs.
4. `make e2e` and the CI job with API and Postgres.
5. Prove each check fails on a broken page.
