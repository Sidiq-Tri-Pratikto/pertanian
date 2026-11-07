import { AccessibilityInfo, Platform } from 'react-native';

/**
 * Moves keyboard and screen-reader focus to an element: `focus()` on the web, a focus event for TalkBack and
 * VoiceOver on native. A missing target does nothing.
 */
export function moveFocus(target: unknown): void {
  if (!target) {
    return;
  }
  if (Platform.OS === 'web') {
    (target as HTMLElement).focus?.();
  } else {
    AccessibilityInfo.sendAccessibilityEvent(target as Parameters<typeof AccessibilityInfo.sendAccessibilityEvent>[0], 'focus');
  }
}
