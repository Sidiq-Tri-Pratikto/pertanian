import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, type ComponentRef, type ReactNode, type Ref } from 'react';
import { AccessibilityInfo, Platform, ScrollView, StyleSheet, useWindowDimensions, View, type TextInstance } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { HDButton } from '@/components/hd/HDButton';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useLabels } from '@/features/localization/messages';

type HDScreenProps = {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  children: ReactNode;
  supporting?: ReactNode;
  /** The step's primary action, outside the scroll view so the keyboard never hides it. */
  footer?: ReactNode;
  /** For moving a focused target into view, such as an error summary's link. */
  scrollRef?: Ref<ComponentRef<typeof ScrollView>>;
  contentRef?: Ref<ComponentRef<typeof View>>;
};

// Web only: receives programmatic focus without joining the tab order. React Native's types omit `tabIndex`.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

/** Shared screen frame: top bar, title, and optional supporting column. Moves focus to the heading on arrival. */
export function HDScreen({ title, subtitle, onBack, children, supporting, footer, scrollRef, contentRef }: HDScreenProps) {
  const { back } = useLabels();
  const heading = useRef<TextInstance>(null);
  const { width } = useWindowDimensions();
  const wide = width >= size.breakpointWide;
  const split = wide && supporting != null;

  useFocusEffect(
    useCallback(() => {
      if (!heading.current) {
        return;
      }
      if (Platform.OS === 'web') {
        // A return from a stack screen must keep the reader's place, and plain focus() scrolls to the heading.
        (heading.current as unknown as HTMLElement).focus({ preventScroll: true });
      } else {
        AccessibilityInfo.sendAccessibilityEvent(heading.current, 'focus');
      }
    }, []),
  );

  return (
    <SafeAreaView edges={['top', 'left', 'right']} style={styles.root}>
      <View style={styles.top}>
        {onBack ? (
          <HDButton variant="text" icon="chevronLeft" onPress={onBack}>
            {back}
          </HDButton>
        ) : (
          <HDText variant="bodyStrong">HematDaya</HDText>
        )}
      </View>
      <ScrollView ref={scrollRef} contentContainerStyle={[styles.scroll, wide && styles.wideGutters]} keyboardShouldPersistTaps="handled">
        <View ref={contentRef} style={[styles.column, split && styles.wideColumn]}>
          <View style={styles.head}>
            <HDText ref={heading} variant="title" role="heading" aria-level={1} {...FOCUSABLE_BY_SCRIPT}>
              {title}
            </HDText>
            {subtitle ? (
              <HDText variant="label" tone="secondary">
                {subtitle}
              </HDText>
            ) : null}
          </View>
          <View style={[styles.body, split && styles.split]}>
            <View style={[styles.group, split && styles.main]}>{children}</View>
            {supporting != null ? (
              <View style={[styles.group, split && styles.supporting]}>{supporting}</View>
            ) : null}
          </View>
        </View>
      </ScrollView>
      {footer ? (
        <View style={styles.footer}>
          <View style={styles.footerColumn}>{footer}</View>
        </View>
      ) : null}
    </SafeAreaView>
  );
}

const { color, space, size } = tokens;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: color.backgroundCanvas },
  top: {
    minHeight: size.targetMinimum,
    justifyContent: 'center',
    paddingHorizontal: space.pageGutter,
    backgroundColor: color.backgroundSurface,
    borderBottomWidth: size.borderControl,
    borderBottomColor: color.borderDecorative,
  },
  scroll: { flexGrow: 1, alignItems: 'center', padding: space.pageGutter, paddingBottom: space['24'] },
  column: { width: '100%', maxWidth: size.contentReadingWidth, gap: space['24'] },
  wideGutters: { paddingHorizontal: space.pageGutterWide },
  wideColumn: { maxWidth: size.contentMaxWidth },
  body: { gap: space['24'] },
  split: { flexDirection: 'row', alignItems: 'flex-start' },
  group: { gap: space['24'], minWidth: 0 },
  main: { flex: 2 },
  supporting: { flex: 1 },
  head: { gap: space['4'] },
  footer: {
    alignItems: 'center',
    paddingHorizontal: space.pageGutter,
    paddingVertical: space.stackTight,
    backgroundColor: color.backgroundSurface,
    borderTopWidth: size.borderControl,
    borderTopColor: color.borderDecorative,
  },
  footerColumn: { width: '100%', maxWidth: size.contentReadingWidth, gap: space.stackTight },
});
