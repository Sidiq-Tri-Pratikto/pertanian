import { useCopy } from '@/features/localization/messages';
import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import type { Period } from '@/features/workspace/workspace-store';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

type HDPeriodSelectorProps = { value: Period; activeLabel: string; timezone?: string; onCommit: (period: Period) => void };

/** Presets commit when chosen; a range commits on Terapkan. The service resolves every boundary in site time. */
export function HDPeriodSelector({ value, activeLabel, timezone, onCommit }: HDPeriodSelectorProps) {
  const say = useCopy();
  const presets = [
    { preset: 'today', label: say('Hari ini', 'Today') },
    { preset: 'this_week', label: say('Minggu ini', 'This week') },
    { preset: 'last_7_days', label: say('7 hari lengkap terakhir', 'Last 7 complete days') },
  ];
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [error, setError] = useState<string | null>(null);

  const apply = () => {
    if (!ISO_DATE.test(start) || !ISO_DATE.test(end)) {
      setError(say("Tanggal belum valid. Gunakan format TTTT-BB-HH, misalnya 2026-10-19.", "Use the date format YYYY-MM-DD, for example 2026-10-19."));
    } else if (start > end) {
      setError(say("Tanggal mulai harus sebelum atau sama dengan tanggal selesai.", "The start date must be on or before the end date."));
    } else {
      setError(null);
      onCommit({ preset: 'range', start_date: start, end_date: end });
    }
  };

  return (
    <View role="group" aria-label={say("Periode", "Period")} style={styles.block}>
      <HDText variant="labelStrong">{say("Periode", "Period")}</HDText>
      <View style={styles.presets}>
        {presets.map((option) => {
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
        <TextInput aria-label={say("Tanggal mulai", "Start date")} placeholder="2026-10-19" value={start} onChangeText={setStart} style={styles.input} />
        <TextInput aria-label={say("Tanggal selesai", "End date")} placeholder="2026-10-25" value={end} onChangeText={setEnd} style={styles.input} />
        <HDButton onPress={apply}>{say("Terapkan", "Apply")}</HDButton>
      </View>
      {error ? <HDText tone="error">{error}</HDText> : null}
      <HDText variant="label" role="status" accessibilityLiveRegion="polite">{say("Periode aktif:", "Active period:")} {activeLabel}{timezone ? ` · ${timezone}` : ''}
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
