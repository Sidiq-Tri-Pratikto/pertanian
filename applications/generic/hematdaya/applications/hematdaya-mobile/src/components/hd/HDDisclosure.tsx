import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

/** Expandable detail. Limitations that change a number never go inside one. */
export function HDDisclosure({ summary, children }: { summary: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <View style={styles.block}>
      <Pressable
        role="button"
        aria-expanded={open}
        aria-label={summary}
        onPress={() => setOpen(!open)}
        style={styles.summary}>
        <HDIcon name={open ? 'chevronLeft' : 'chevronRight'} size="small" color={tokens.color.actionSecondaryForeground} />
        <HDText variant="labelStrong" tone="link">
          {summary}
        </HDText>
      </Pressable>
      {open ? <View style={styles.block}>{children}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  summary: { flexDirection: 'row', alignItems: 'center', gap: tokens.space.inlineGap, minHeight: tokens.size.targetMinimum },
});
