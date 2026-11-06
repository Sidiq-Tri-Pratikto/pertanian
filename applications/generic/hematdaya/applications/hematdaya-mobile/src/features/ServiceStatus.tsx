import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useCapabilities } from '@/features/use-capabilities';

/** States whether the service answers, and keeps the app usable when it does not. */
export function ServiceStatus() {
  const { state, retry } = useCapabilities();

  if (state.kind === 'loading') {
    return (
      <View role="status" style={styles.loading}>
        <ActivityIndicator color={tokens.color.actionPrimaryBackground} />
        <HDText variant="label" tone="secondary">
          Memeriksa layanan…
        </HDText>
      </View>
    );
  }

  if (state.kind === 'failed') {
    const { error, retryStatus } = state;
    return (
      <HDNotice
        tone="attention"
        title="Layanan belum tersedia"
        live
        action={
          retryStatus !== 'unavailable' ? (
            <HDButton
              variant="text"
              icon="refresh"
              onPress={retry}
              disabledReason={retryStatus === 'waiting' ? 'Tunggu sebentar sebelum mencoba lagi.' : null}>
              Coba lagi
            </HDButton>
          ) : null
        }>
        <HDText>{error.message}</HDText>
        {error.requestId ? (
          <HDText variant="label" tone="secondary">
            ID referensi: {error.requestId}
          </HDText>
        ) : null}
      </HDNotice>
    );
  }

  return (
    <HDNotice tone="neutral" title="Layanan tersedia">
      {`Versi ${state.manifest.source_release}. Fitur pemantauan segera hadir.`}
    </HDNotice>
  );
}

const styles = StyleSheet.create({
  loading: { flexDirection: 'row', alignItems: 'center', gap: tokens.space.stackTight, minHeight: tokens.size.targetMinimum },
});
