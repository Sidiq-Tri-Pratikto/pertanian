# HematDaya — Expo / React Native engineering handoff

Target from the PRD: one Expo + React Native + TypeScript app (Expo Router) for Android, iOS and web, backed by the modular FastAPI server. This prototype is a browser simulation; nothing here has run natively.

## 1. Routes → Expo Router

```
app/
  _layout.tsx                 root stack; demo/local workspace provider; capability manifest
  index.tsx                   S01 welcome (redirects to (tabs) when a workspace exists)
  (tabs)/_layout.tsx          Tabs: beranda, perangkat, saran — exactly three, labelled
  (tabs)/beranda/index.tsx    S02/S03
  (tabs)/perangkat/index.tsx  S04
  (tabs)/saran/index.tsx      S07
  (tabs)/saran/tersembunyi.tsx
  asset/[id].tsx              S06 (pushed on the current tab's stack)
  insight/[id].tsx            S08
  source/[step].tsx           S05 (catalog | capability | connect | review | planned)
  import/[step].tsx           S10 (input | mapping | preview | result)
  scope.tsx                   S11
  metric.tsx                  S12
  settings/index.tsx          S09
  settings/demo.tsx           Tentang demo (scenarios, failure injection only in demo builds)
```

Keep period (`{preset,start,end}`), selected site, timezone, aggregation selection and data revision in a shared navigation context, as `hematdaya-app.js` does in `st.period` / `ws.selection`. Restore list scroll on return (`FlatList` `initialScrollIndex` or saved offset). Android hardware back and iOS swipe-back must call the same `pop` as the header back.

## 2. Calculation authority

`hematdaya-domain.js` is a **reference implementation and parity oracle**, not the production engine. The server owns summaries and evidence; the client renders `GET /sites/{id}/summary`, `/insights`, `/assets/{id}/measurements`. Port `tests/domain.test.js` to `pytest` against the FastAPI use cases and keep a small TS parity test on fixture outputs so the two never diverge. Do not ship a second live calculation engine in the app.

Numeric contract: energy integer mWh (or decimal strings), tariff milli-rupiah/kWh, money decimal, `null` + reason for unavailable values (`missing_tariff`, `scope_conflict`, `insufficient_history`, `partial_coverage`, `no_schedule`, `no_output`, `capability_disabled`).

## 3. Components and browser primitives to replace

| Browser piece | Native replacement |
|---|---|
| `HD.*` React DOM components | Native HD component set with the same names, props and states (EnergyMetric, CostEstimate, DataQuality, ContributionRanking, HistoryChart + ChartDataAlternative, InsightSummary, EvidencePanel, ImportPreview, ScopeSummary, ProgressStatus, ErrorSummary…) |
| `<dialog>` SheetDialog | `@gorhom/bottom-sheet` or `Modal` with focus moved to title (`AccessibilityInfo.setAccessibilityFocus`) and back handler |
| `<details>` Disclosure | Pressable with `accessibilityState={{ expanded }}` |
| `<table>` data alternative | Stacked rows (`View` + labelled `Text`), never horizontal scroll on phones |
| `input type=file` + FileReader | `expo-document-picker` + `expo-file-system` read as UTF-8; paste via multiline `TextInput` |
| `input type=time/date` | Native time/date pickers; decimal fields `keyboardType="decimal-pad"` accepting comma |
| CSS tokens (`--space-16`…) | Token module in logical units (dp/pt); 48 target, 16/24 gutter; `allowFontScaling` kept on |
| `history.pushState` | Expo Router stack |
| `prefers-reduced-motion` | `AccessibilityInfo.isReduceMotionEnabled` |
| `env(safe-area-inset-*)` | `react-native-safe-area-context`; `KeyboardAvoidingView` so the active field, error and primary action stay visible |
| In-memory workspace | Demo: isolated local store (e.g. SQLite namespace `demo`) reset only by explicit action; saved data: server only |
| Mock `api.*` | Typed API client; idempotency key header on import commit, source enrollment and feedback; on timeout query operation status before retry |

## 4. Platform requirements not covered by the prototype

Secure session storage (`expo-secure-store`), refresh-token rotation, expiry boundary that keeps non-secret drafts; network state (`@react-native-community/netinfo`) kept separate from source staleness; optional push only after explicit consent (no prompt in demo); TalkBack/VoiceOver labels and focus order; OS font scale up to 200%; Android 48 dp and iOS 48 pt targets measured per platform; hardware back; deep links; no vendor secrets in the app.

## 5. Acceptance carried forward

All rows in `ACCEPTANCE.md` marked pass apply to the browser simulation only. Every native, service, security, restore and participant row starts as **not run** for the Expo build.
