import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import type { Period } from '@/features/workspace/workspace-store';

const PRESETS = [
  { preset: 'today', label: 'Hari ini' },
  { preset: 'this_week', label: 'Minggu ini' },
  { preset: 'last_7_days', label: '7 hari lengkap terakhir' },
];
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

type HDPeriodSelectorProps = { value: Period; activeLabel: string; timezone?: string; onCommit: (period: Period) => void };

/** Presets commit when chosen; a range commits on Terapkan. The service resolves every boundary in site time. */
export function HDPeriodSelector({ value, activeLabel, timezone, onCommit }: HDPeriodSelectorProps) {
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [error, setError] = useState<string | null>(null);

  const apply = () => {
    if (!ISO_DATE.test(start) || !ISO_DATE.test(end)) {
      setError('Tanggal belum valid. Gunakan format TTTT-BB-HH, misalnya 2026-10-19.');
    } else if (start > end) {
      setError('Tanggal mulai harus sebelum atau sama dengan tanggal selesai.');
    } else {
      setError(null);
      onCommit({ preset: 'range', start_date: start, end_date: end });
    }
  };

  return (
    <View role="group" aria-label="Periode" style={styles.block}>
      <HDText variant="labelStrong">Periode</HDText>
      <View style={styles.presets}>
        {PRESETS.map((option) => {
          const pressed = value.preset === option.preset;
          return (
            <Pressable
              key={option.preset}
              role="button"
              aria-pressed={pressed}
              aria-label={option.label}
              onPress={() => onCommit({ preset: option.preset, start_date: '', end_date: '' })}
              style={[styles.preset, pressed && styles.pressed]}>
              <HDText variant={pressed ? 'labelStrong' : 'label'}>
                {pressed ? '✓ ' : ''}
                {option.label}
              </HDText>
            </Pressable>
          );
        })}
      </View>
      <View style={styles.range}>
        <TextInput aria-label="Tanggal mulai" placeholder="2026-10-19" value={start} onChangeText={setStart} style={styles.input} />
        <TextInput aria-label="Tanggal selesai" placeholder="2026-10-25" value={end} onChangeText={setEnd} style={styles.input} />
        <HDButton onPress={apply}>Terapkan</HDButton>
      </View>
      {error ? <HDText tone="error">{error}</HDText> : null}
      <HDText variant="label" role="status" accessibilityLiveRegion="polite">
        Periode aktif: {activeLabel}{timezone ? ` · ${timezone}` : ''}
      </HDText>
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  presets: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap },
  preset: {
    minHeight: tokens.size.targetMinimum,
    justifyContent: 'center',
    paddingHorizontal: tokens.space.controlPaddingX,
    borderRadius: tokens.radius.control,
    borderWidth: tokens.size.borderControl,
    borderColor: tokens.color.borderControl,
  },
  pressed: {
    borderWidth: tokens.size.borderSelected,
    borderColor: tokens.color.selectionIndicator,
    backgroundColor: tokens.color.selectionBackground,
  },
  range: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.inlineGap, alignItems: 'center' },
  input: {
    minHeight: tokens.size.targetMinimum,
    minWidth: 140,
    flexGrow: 1,
    paddingHorizontal: tokens.space.controlPaddingX,
    borderRadius: tokens.radius.control,
    borderWidth: tokens.size.borderControl,
    borderColor: tokens.color.borderControl,
    color: tokens.color.textPrimary,
  },
});
