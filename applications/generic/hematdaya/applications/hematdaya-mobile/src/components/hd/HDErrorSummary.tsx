import { useCopy } from '@/features/localization/messages';
import { useEffect, useRef, type ComponentRef } from 'react';
import { Platform, Pressable, StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { moveFocus } from '@/lib/focus';

export type SummaryError = {
  key: string;
  text: string;
  /** The field or row to focus; called when the link is pressed, so it may also scroll the target into view. */
  target: () => unknown;
};

type HDErrorSummaryProps = {
  errors: SummaryError[];
  /** How many submits produced these errors. Focus moves here on each increase, and never at zero. */
  submitCount: number;
  convention?: string;
  title?: string;
};

// Web only: receives programmatic focus without joining the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

/**
 * Web only: react-native-web leaves Enter on a `role="link"` element to the browser, which follows only real
 * anchors, so a summary link would ignore the keyboard. React Native's types omit `onKeyDown`.
 */
function enterFollows(follow: () => void): object {
  if (Platform.OS !== 'web') {
    return {};
  }
  return {
    onKeyDown: (event: { key: string; preventDefault: () => void }) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        follow();
      }
    },
  };
}

/** After a submit, lists every error as a link to its field or row, and takes focus. Hidden when empty. */
export function HDErrorSummary({ errors, submitCount, convention, title }: HDErrorSummaryProps) {
  const say = useCopy();
  const container = useRef<ComponentRef<typeof View>>(null);
  const shown = errors.length > 0;

  useEffect(() => {
    if (!shown || submitCount <= 0) {
      return;
    }
    // The screen focuses its heading on arrival after child effects run; a zero-delay timeout lands after it.
    const timer = setTimeout(() => moveFocus(container.current), 0);
    return () => clearTimeout(timer);
  }, [shown, submitCount]);

  if (!shown) {
    return null;
  }
  const heading = title ?? say(`Periksa ${errors.length} hal berikut`, `Check these ${errors.length} items`);
  return (
    <View ref={container} role="alert" aria-label={heading} style={styles.summary} {...FOCUSABLE_BY_SCRIPT}>
      <View style={styles.head}>
        <HDIcon name="error" size="small" color={tokens.color.statusErrorForeground} />
        <HDText variant="bodyStrong" role="heading" aria-level={2} style={styles.title}>
          {heading}
        </HDText>
      </View>
      {convention ? <HDText variant="label">{convention}</HDText> : null}
      {errors.map((error) => (
        <Pressable
          key={error.key}
          role="link"
          aria-label={error.text}
          onPress={() => moveFocus(error.target())}
          {...enterFollows(() => moveFocus(error.target()))}
          style={styles.link}>
          <HDText tone="link" style={styles.linkText}>
            {error.text}
          </HDText>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  summary: {
    gap: tokens.space.stackTight,
    padding: tokens.space['16'],
    borderRadius: tokens.radius.surface,
    borderWidth: tokens.size.borderSelected,
    borderColor: tokens.color.statusErrorForeground,
    backgroundColor: tokens.color.statusErrorBackground,
  },
  head: { flexDirection: 'row', alignItems: 'center', gap: tokens.space.stackTight },
  title: { flexShrink: 1 },
  link: { minHeight: tokens.size.targetMinimum, justifyContent: 'center' },
  linkText: { textDecorationLine: 'underline' },
});
