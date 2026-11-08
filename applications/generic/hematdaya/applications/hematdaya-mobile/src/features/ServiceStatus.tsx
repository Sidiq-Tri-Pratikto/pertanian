import { useCopy } from '@/features/localization/messages';
import { errorMessage } from '@/features/localization/error-copy';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useCapabilities } from '@/features/use-capabilities';

/** States whether the service answers, and keeps the app usable when it does not. */
export function ServiceStatus() {
  const say = useCopy();
  const { state, retry } = useCapabilities();

  if (state.kind === 'loading') {
    return (
      <View role="status" style={styles.loading}>
        <ActivityIndicator color={tokens.color.actionPrimaryBackground} />
        <HDText variant="label" tone="secondary">{say("Memeriksa layanan…", "Checking service…")}</HDText>
      </View>
    );
  }

  if (state.kind === 'failed') {
    const { error, retryStatus } = state;
    return (
      <HDNotice
        tone="attention"
        title={say("Layanan belum tersedia", "Service unavailable")}
        live
        action={
          retryStatus !== 'unavailable' ? (
            <HDButton
              variant="text"
              icon="refresh"
              onPress={retry}
              disabledReason={retryStatus === 'waiting' ? say("Tunggu sebentar sebelum mencoba lagi.", "Wait a moment before trying again.") : null}>{say("Coba lagi", "Try again")}</HDButton>
          ) : null
        }>
        <HDText>{errorMessage(error)}</HDText>
        {error.requestId ? (
          <HDText variant="label" tone="secondary">{say("ID referensi:", "Reference ID:")} {error.requestId}
          </HDText>
        ) : null}
      </HDNotice>
    );
  }

  return (
    <HDNotice tone="neutral" title={say("Layanan tersedia", "Service available")}>
      {say(`Versi ${state.manifest.source_release}. Fitur pemantauan segera hadir.`, `Release ${state.manifest.source_release}.`)}
    </HDNotice>
  );
}

const styles = StyleSheet.create({
  loading: { flexDirection: 'row', alignItems: 'center', gap: tokens.space.stackTight, minHeight: tokens.size.targetMinimum },
});
