import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

/** Expandable detail. Limitations that change a number never go inside one. */
export function HDDisclosure({
  summary, children, onToggle, status,
}: { summary: string; children: ReactNode; onToggle?: (open: boolean) => void; status?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(false);
  return (
    <View style={styles.block}>
      <Pressable
        role="button"
        aria-expanded={open}
        aria-label={summary}
        onPress={() => {
          setOpen(!open);
          onToggle?.(!open);
        }}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={[styles.summary, focused && styles.focused]}>
        <HDIcon name={open ? 'chevronLeft' : 'chevronRight'} size="small" color={tokens.color.actionSecondaryForeground} />
        <HDText variant="labelStrong" tone="link" style={styles.label}>
          {summary}
        </HDText>
      </Pressable>
      {status}
      {open ? <View style={styles.block}>{children}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  summary: { flexDirection: 'row', alignItems: 'center', gap: tokens.space.inlineGap, minHeight: tokens.size.targetMinimum, minWidth: tokens.size.targetMinimum },
  focused: {
    outlineColor: tokens.color.focusRing,
    outlineStyle: 'solid',
    outlineWidth: tokens.size.focusRingWidth,
    outlineOffset: tokens.size.focusGapWidth,
  },
  label: { flexShrink: 1 },
});
