import { useCopy } from '@/features/localization/messages';
import type { ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { HDIcon } from '@/components/hd/HDIcon';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';

type HDProgressStatusProps = {
  state: 'loading' | 'saving' | 'unknown' | 'failure' | null;
  label?: string;
  detail?: string | null;
  action?: ReactNode;
};

/** Always-mounted polite status region: loading, failure with retry, or unknown result. Never early success. */
export function HDProgressStatus({ state, label, detail, action }: HDProgressStatusProps) {
  const say = useCopy();
  const defaultLabel = {
    loading: say('Memuat…', 'Loading…'),
    saving: say('Menyimpan…', 'Saving…'),
    unknown: say('Status permintaan belum diketahui', 'Request status unknown'),
    failure: say('Belum berhasil', 'Unsuccessful'),
  };
  return (
    <View role="status" accessibilityLiveRegion="polite" style={state ? styles.status : undefined}>
      {state ? (
        <>
          <View style={styles.row}>
            {state === 'loading' || state === 'saving' ? (
              <ActivityIndicator color={tokens.color.actionPrimaryBackground} />
            ) : (
              <HDIcon
                name={state === 'failure' ? 'error' : 'attention'}
                size="small"
                color={state === 'failure' ? tokens.color.statusErrorForeground : tokens.color.statusAttentionForeground}
              />
            )}
            <HDText variant="bodyStrong" style={styles.label}>
              {label ?? defaultLabel[state]}
            </HDText>
          </View>
          {detail ? <HDText>{detail}</HDText> : null}
          {action}
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  status: { gap: tokens.space.stackTight },
  row: { flexDirection: 'row', alignItems: 'center', gap: tokens.space.stackTight, minHeight: tokens.size.targetMinimum },
  label: { flexShrink: 1 },
});
