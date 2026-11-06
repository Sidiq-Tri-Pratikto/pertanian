import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, type ReactNode } from 'react';
import { AccessibilityInfo, Platform, ScrollView, StyleSheet, View, type TextInstance } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { HDButton } from '@/components/hd/HDButton';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDScreenProps = {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  children: ReactNode;
};

// Web only: receives programmatic focus without joining the tab order. React Native's types omit `tabIndex`.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

/** Shared screen frame: top bar, title, one reading column. Moves focus to the heading on arrival. */
export function HDScreen({ title, subtitle, onBack, children }: HDScreenProps) {
  const heading = useRef<TextInstance>(null);

  useFocusEffect(
    useCallback(() => {
      if (!heading.current) {
        return;
      }
      if (Platform.OS === 'web') {
        (heading.current as unknown as HTMLElement).focus();
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
            Kembali
          </HDButton>
        ) : (
          <HDText variant="bodyStrong">HematDaya</HDText>
        )}
      </View>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.column}>
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
          {children}
        </View>
      </ScrollView>
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
  scroll: { flexGrow: 1, alignItems: 'center', padding: space.pageGutter, paddingBottom: space['32'] },
  column: { width: '100%', maxWidth: size.contentReadingWidth, gap: space.sectionGap },
  head: { gap: space['4'] },
});
