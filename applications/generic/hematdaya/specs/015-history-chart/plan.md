# Implementation plan — History chart

**Branch**: `015-history-chart` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

Add the read-only History disclosure to S06 after 014. Port 022's shared `HDHistoryChart` to the installed `react-native-svg` and give the existing chart data disclosure a semantic web table.

## Project Structure

Paths below are relative to `applications/hematdaya-mobile/`.

```text
src/api/client.ts
src/features/assets/{AssetDetailScreen.tsx,AssetHistorySection.tsx,history-model.ts,useHistory.ts}
src/components/hd/{HDHistoryChart.tsx,HDChartDataAlternative.tsx,HDChartDataTable.tsx,HDChartDataTable.web.tsx,HDChartDataTable.css}
```

The shared Expo Router asset route continues to compose `AssetDetailScreen`. Place **Lihat riwayat** before **Sumber data** and use the existing tab and back behavior.

## Read contract and recovery

- Use the current confirmed asset summary's inclusive local dates to send `GET /api/v1/assets/{asset_id}/measurements` with the workspace bearer and explicit `start_date`, `end_date` and `bucket`. A single local date selects `hour`, including Monday **Minggu ini**. Other ranges select `day`. Key the lazy TanStack Query by workspace/site, asset, dates, timezone and granularity. A previous or placeholder summary cannot start a read for a new selection.
- Use the generated 010 response and the shared request and error boundary. Check echoed dates, granularity and timezone against the request. Validate ordered UTC bounds, including `window.start ≤ effective_end ≤ window.end`, and fields used for display. Measured and partial buckets carry a nonnegative recorded decimal. Measured coverage is complete through the cutoff and partial coverage is below one, including values that round down to zero. Missing has null energy and zero coverage. Future and unavailable have null energy and coverage. Only unavailable carries a reason. A non-null highest pointer must resolve by UTC instant to exactly one measured bucket. Consume a null pointer as supplied. An unexpected 204 or malformed or mismatched response becomes `UNEXPECTED_RESPONSE`. S06 uses the recorded series even when 020 comparison fields are present.
- Use one automatic retry sequence for a History operation. Honor `retryable`, `retry_after_seconds` and `max_attempts` from the normalized error, counting the initial request. Reuse the shared fallback delay and attempt limit when those values are absent. Keep terminal failures terminal for the active or cached request identity, including on toggle, remount, focus, reconnect and invalidation. A newly confirmed workspace, asset or date/timezone request can start its own operation. Successful requests remain eligible for ordinary refresh. The status announces the wait while retry is pending. At terminal failure, keep the service message and reference where available, explain that retry has stopped and provide a safe next step. Give the automatic sequence sole control of retries and keep its terminal UI free of a retry action.
- Use the last confirmed History only within its workspace and asset. While a selection is pending or failed, identify retained data as such and display its own original period, timezone and elapsed cutoff. Ignore a late response for an older selection in the active view. A confirmed all-missing, all-future or all-unavailable series replaces retained data. A successful response with an empty bucket array has an explicit empty state. Keep the current session-expiry behavior.

## Chart and data alternative

- Share one display model for S06 plot, visible summary and data rows. Use the full selected `energy_kwh`, service order, supplied provenance, response resolution when known and exact decimal strings. Use energy arithmetic only for visual scale. Resolve `highest_bucket.start` by UTC instant and trust the service's unrounded ranking and earliest-UTC tie rule.
- Use the History response's `window.effective_end` and UTC bounds for elapsed qualification. When `bucket.start < effective_end < bucket.end`, label the recorded value and returned coverage as measured through that cutoff, even when the service state is `measured` and coverage is `1.000`. A highest bucket crossing that cutoff gets the same qualification. For a current window show the elapsed endpoint with the local time and applicable offset. A window with `effective_end == start` can state that the period has yet to begin. Retained data keeps its own cutoff.
- Use returned UTC starts and ends for bucket identity and interval labels. Use local dates, times and offsets from the response. On 23- and 25-hour days preserve server order and every table row. Use sparse hourly axis labels, including offset-distinct labels for a repeated hour. Give missing-period and highest-bucket text the same unambiguous date/time/offset. Keep the labels readable as text scales.
- Use `Rect`, chart tokens, a zero baseline and 20% headroom. Use a hatched SVG `Pattern` with the missing-marker token and label **Tidak ada data**. Measured energy reported as `0.000` uses the measured baseline tick. Partial energy shows a separate mark and coverage at any reported value, including `0.000` and small positive values. Use an empty slot for future and a nonnumeric marker for unavailable. Label `source_conflict` and `insufficient_resolution` separately. Use safe generic copy for an unfamiliar reason. Keep one accessible image label for the plot with no exposed per-bar targets. Put exact values in the data alternative and make the summary visible.
- Keep S08's frozen version and aligned solid/dashed series. Preserve the existing dotted mask gap and matching note for a frozen null. Keep S06's hatch and unavailable states specific to asset history. Use real web table markup with a caption and associated headers, stacked below 768 CSS px. Keep the disclosure and exact values in the existing S03 and S08 consumers and retain stacked, labeled native rows.

## Prototype Reference

`Asset` history block in `hematdaya-app.js`, `HistoryChart` in `docs/design/components/`.

## Test Plan

Test malformed or mismatched responses, retries at limits one and three, wait timing and lifecycle triggers, stale request races, replacement by all-unavailable/missing/future data, elapsed-only completeness, every bucket state, highest ties and no eligible highest. Cover the 23- and 25-hour display in fixtures and S08's frozen null and reference in regression tests. Use a multi-day learning-partial demo range to see an actual missing daily bucket and a partial daily total.

Use real web keyboard and screen reader checks for the S06 task and shared S03/S08 tables above and below the stacking breakpoint. Measure 320 CSS px reflow and 200% text separately. Record focus visibility and order, disclosure state, live status, relevant hit areas, contrast and header associations. Verify native assistive technology at 043.

## Handoff

016 owns edit/archive and the final `detail-perangkat` registry flip. Its handoff includes S07's existing **Tentang riwayat perangkat** link, which currently opens the generic feature-information placeholder. S06 reads the current asset history while S08 continues reading frozen evidence. Both use the shared chart and data alternative.
