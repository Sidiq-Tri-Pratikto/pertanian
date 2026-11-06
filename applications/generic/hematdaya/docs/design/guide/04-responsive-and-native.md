# Responsive and native mapping

## Web layout

- Mobile first. One reading column below 768 CSS px (`size-breakpoint-wide`; CSS repeats 768px in media queries because they cannot read custom properties). From 768 px, `HD.Screen` `aside` becomes a supporting column beside a main column up to `size-content-readingWidth` (720 px), centred within `size-content-maxWidth` (1200 px). Reading order in the DOM is main first, then aside, then navigation.
- Gutters `space-page-gutter` 16 px, `space-page-gutterWide` 24 px from 768 px.
- 320 CSS px is a separate reflow check from 360/390/430 phones; 768, 1280 and 1440 are inspected too. Tables become stacked label/value rows below 768 px (`hd-table--stack`) instead of forcing page scroll.
- Text sizes are rem, so a larger default font or a 200% root size scales every style; containers wrap instead of shrinking.
- `HD.TabNavigation` stays sticky at the bottom at every width; it adds `env(safe-area-inset-bottom)`. `HD.SheetDialog` is a bottom sheet below 768 px and a 560 px centred dialog above, with safe-area padding in its footer.

## Native mapping (documentation only — no native code in this release)

| HD component | Android (Compose / Views) | iOS (SwiftUI / UIKit) | React Native |
|---|---|---|---|
| `HD.Button` | `Button`/`OutlinedButton`/`TextButton`; `enabled=false` + visible reason text, or keep enabled and explain on press | `Button` with `.borderedProminent` / `.bordered` / `.plain`; `.disabled` + reason `Text` | `Pressable` `accessibilityRole="button"`, `accessibilityState={{disabled, busy}}` |
| `HD.IconButton` | `IconButton` with `contentDescription` | `Button { Image }` + `.accessibilityLabel` | `Pressable` + `accessibilityLabel`, `hitSlop` to 48 |
| `HD.TextField` / `HD.NumericField` | `OutlinedTextField` with `supportingText`, `isError`; `KeyboardType.Decimal` | `TextField` + `.keyboardType(.decimalPad)`; error `Text` | `TextInput` `keyboardType="decimal-pad"`; parse with `HD.format.parseDecimal` logic |
| `HD.ChoiceGroup` | `RadioButton`/`Checkbox` rows with `Modifier.selectable`/`toggleable`, `Role.RadioButton` | `Picker(.inline)` / `Toggle` styled as checkbox rows | `accessibilityRole="radio"`/`"checkbox"` rows |
| `HD.PeriodSelector` | `FilterChip` group + `DateRangePicker` | segmented `Picker` + `DatePicker` | chips + platform date picker |
| `HD.TabNavigation` | `NavigationBar` with three `NavigationBarItem`s | `TabView` with three tabs | bottom tab navigator, three routes |
| `HD.SheetDialog` | `ModalBottomSheet`; back gesture = `onDismissRequest` | `.sheet` with `presentationDetents`; swipe/Escape = dismiss | `Modal`/bottom sheet with `onRequestClose`, focus to title |
| `HD.Disclosure` | `AnimatedVisibility` header row, `Role.Button`, expanded state description | `DisclosureGroup` | `Pressable` + `accessibilityState={{expanded}}` |
| `HD.Notice` / `HD.ProgressStatus` | inline surfaces; status changes via `LiveRegionMode.Polite` | inline views; `UIAccessibility.post(.announcement)` for status | `accessibilityLiveRegion="polite"` (Android) / `AccessibilityInfo.announceForAccessibility` |
| `HD.ErrorSummary` | list of clickable rows that `requestFocus()` their field | list of buttons using `@AccessibilityFocusState` | list of `Pressable`s calling `ref.focus()` |
| Charts | Canvas/Compose drawing + `semantics { contentDescription }`; data table screen | Swift Charts with `accessibilityChartDescriptor` or custom; table | `react-native-svg` + summary text + table |

Tokens map one to one: `color-*` to theme colours, `space-*`/`radius-*`/`size-*` px to dp (Android) and pt (iOS), type styles rem × 16 to sp/pt with font scaling on. Keyboard avoidance, visible back behaviour, safe areas, dynamic type/font scale and TalkBack/VoiceOver names must be checked separately on devices. CSS viewport resizing does not prove any native behaviour. None of these mappings has been implemented or tested in this release.
