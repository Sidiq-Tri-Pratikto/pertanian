# Tasks: API base

All tasks are complete on branch `001-api-base`.

- [x] T001 Add `app/capabilities/` schema, service and router
- [x] T002 Validate the composition in `create_app`; add `COMPOSITION` to settings and `.env.example`
- [x] T003 Mount `/api/v1`, set the API version from `SOURCE_RELEASE`
- [x] T004 Move health to `/health/live` and `/health/ready`, including the Dockerfile `HEALTHCHECK`
- [x] T005 Translate public messages and add `field_message`; update the error catalog and deviation note
- [x] T006 Add capability and read-only contract tests
- [x] T007 Regenerate `contracts/openapi.json` and the mobile schema
- [x] T008 `make check`, live `curl` of all routes, `docker build`
