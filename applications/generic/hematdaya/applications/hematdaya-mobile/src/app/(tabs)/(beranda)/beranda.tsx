import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { CONTEXT_EXAMPLES, useContextPreset } from '@/features/context-preset';
import { useTabNavigation } from '@/features/navigation';
import { ServiceStatus } from '@/features/ServiceStatus';

/** S02: empty Beranda. No axes, no Rp0, no giant zero: there is simply no data yet. */
export default function BerandaScreen() {
  const { preset } = useContextPreset();
  const { openFeature, openSettings } = useTabNavigation();

  return (
    <HDScreen title="Beranda">
      <View style={styles.section}>
        <HDText variant="section">Belum ada data energi</HDText>
        <HDText>HematDaya membaca energi dari berkas CSV atau dari sumber pengukuran yang didukung.</HDText>
        <HDText tone="secondary">{CONTEXT_EXAMPLES[preset]}</HDText>
        <HDButton variant="primary" icon="chevronRight" onPress={() => openFeature('impor-data')}>
          Impor data
        </HDButton>
        <HDButton onPress={() => openFeature('demo')}>Coba demo</HDButton>
        <HDButton variant="text" onPress={() => openFeature('sumber-meter')}>
          Lihat meter yang didukung
        </HDButton>
      </View>
      <ServiceStatus />
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
    </HDScreen>
  );
}

const styles = StyleSheet.create({ section: { gap: tokens.space.stack } });
