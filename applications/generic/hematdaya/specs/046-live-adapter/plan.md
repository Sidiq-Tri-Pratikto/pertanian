# Implementation Plan: Live meter adapter

**Branch**: `046-live-adapter` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Lab boundary

Enable `METER_PILOT_ENABLED` only on the isolated lab deployment. Operator provisioning assigns a standard site and meter UUID to the owner code. The device publishes cumulative Wh and capture time once per minute over TLS MQTT. Its broker credential grants only its assigned readings topic. The worker reads measurement topics and resolves the meter assignment from the ACL-bound topic. Validate model, firmware, measurement semantics, scoped credentials and collection transport against the actual unit. The lab is limited to one plug-in appliance and creates one new asset.

## API contract

| Route | Behaviour |
| --- | --- |
| `GET /api/v1/device-catalog` | Reports the Shelly model, deployment availability, counter measurement, cadence and device scope |
| `GET /api/v1/pilot/session` | Verifies the operator-issued bearer code and returns its site and expiry |
| `POST /api/v1/sites/{site_id}/enrollments` | Starts or replays setup for the assigned meter with an idempotency key |
| `GET /api/v1/enrollments/{id}` | Returns waiting, ready, connected or expired state and the appropriate reading or result |
| `POST /api/v1/enrollments/{id}/confirm` | Confirms the named new asset with an idempotency key after the first valid reading |

Reuse the source/binding model and `IngestService`. Lock the owned site before the enrollment when confirming. Commit the source, asset, binding, first reading and replay result together. Keep the operator-issued access code in client memory and retain only non-secret draft fields. Reuse the existing readings and history path after confirmation.

## Test Plan

- Disabled flag, unauthorized or revoked access, cross-site and cross-meter refusal, first reading and state changes.
- Invalid and duplicate readings, lost response and concurrent confirmation replay, expiry, stale source, no control path.
- Real device and reference comparison on the compatible installation. Verify credential separation and record actual bench evidence before advertising verified model support.

## Release

Develop and exercise the isolated lab alongside 036/037. Opening the pilot to users requires 038/039/040, platform and usability evidence, and G5 physical validation.
