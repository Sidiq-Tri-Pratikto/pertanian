# Implementation Plan: Source catalog

**Branch**: `035-source-catalog-s05` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add the read-only catalog at `GET /api/v1/device-catalog` and a shared S05 entry from Welcome, Beranda and Perangkat. List model, availability and known measurement capabilities. Keep the Shelly setup unavailable unless the isolated lab path from 046 is enabled. Mark other models as planned or unsupported. Use the existing manifest and registry to decide whether to show the secondary CSV action.

The browser prototype mirrors the catalog and unavailable states. Its demo fixtures remain separate from meter setup.

## Test Plan

- Open the catalog from Welcome and both tabs, read capability and availability, and return to the originating screen.
- Confirm that a catalog-only build creates no workspace, enrollment or reading. Confirm import is available only when the existing CSV route is enabled.
- Check both locales and verify that the catalog creates no connection success.

## Task Outline

1. Define the catalog response and source status copy.
2. Add the meter entry and read-only catalog screen.
3. Advertise the catalog after both routes work.
