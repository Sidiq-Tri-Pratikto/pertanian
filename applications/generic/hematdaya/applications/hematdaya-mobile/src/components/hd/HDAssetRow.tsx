import { useCopy } from '@/features/localization/messages';
import { useState } from 'react';
import { Platform, Pressable, StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatAssetMeta, assetKindLabel, type AssetKind } from '@/lib/format';

type HDAssetRowProps = {
  name: string;
  kind: AssetKind;
  location: string | null;
  category: string | null;
  /** Formatted by the caller. Null means no value, and never a zero. */
  kwh: string | null;
  quality: 'complete' | 'partial' | 'unavailable';
  qualityLabel: string;
  /** One line per unresolved source. */
  sources: string[];
  stale: boolean;
  onOpen: () => void;
};

// A React Native Web pressable with link semantics has no native anchor to handle Enter.
function enterOpens(onOpen: () => void): object {
  if (Platform.OS !== 'web') return {};
  return {
    onKeyDown: (event: { key: string; repeat: boolean; preventDefault: () => void }) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      if (!event.repeat) onOpen();
    },
  };
}

/** One measured thing as one link. No nested control: HematDaya reads energy and never operates a device. */
export function HDAssetRow({ name, kind, location, category, kwh, quality, qualityLabel, sources, stale, onOpen }: HDAssetRowProps) {
  const say = useCopy();
  const staleLabel = say('Data belum diperbarui', 'Data is out of date');
  const [focused, setFocused] = useState(false);
  const label = [
    name,
    assetKindLabel(kind),
    location,
    category,
    kwh ?? say("nilai belum tersedia", "value unavailable"),
    qualityLabel,
    ...sources,
    stale ? staleLabel : null,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <Pressable
      role="link"
      aria-label={label}
      onPress={onOpen}
      {...enterOpens(onOpen)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={[styles.row, focused && styles.focused]}>
      <View style={styles.text}>
        <HDText variant="bodyStrong">{name}</HDText>
        <HDText variant="label" tone="secondary">
          {formatAssetMeta(kind, location, category)}
        </HDText>
        <HDText variant="label" tone={quality === 'complete' ? 'primary' : 'attention'}>
          {qualityLabel}
        </HDText>
        {sources.map((source, index) => (
          <HDText key={`${index}-${source}`} variant="label">
            {source}
          </HDText>
        ))}
        {stale ? (
          <HDText variant="label" tone="attention">
            {staleLabel}
          </HDText>
        ) : null}
      </View>
      <View style={styles.value}>
        <HDText variant="bodyStrong">{kwh ?? '— kWh'}</HDText>
        <HDIcon name="chevronRight" size="small" color={tokens.color.textSecondary} />
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: tokens.size.targetMinimum,
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'flex-start',
    gap: tokens.space.stackTight,
    padding: tokens.space['12'],
    borderBottomWidth: tokens.size.borderControl,
    borderBottomColor: tokens.color.borderDecorative,
  },
  // The basis lets the value drop below the name at large text instead of squeezing it.
  text: { flexGrow: 1, flexShrink: 1, flexBasis: 180, minWidth: 0, gap: tokens.space['4'] },
  value: { marginLeft: 'auto', flexDirection: 'row', alignItems: 'center', gap: tokens.space['4'] },
  focused: {
    outlineColor: tokens.color.focusRing,
    outlineStyle: 'solid',
    outlineWidth: tokens.size.focusRingWidth,
    outlineOffset: tokens.size.focusGapWidth,
  },
});
