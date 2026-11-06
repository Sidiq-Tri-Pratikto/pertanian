import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useTabNavigation } from '@/features/navigation';

/** S04 before any source exists: empty state with the two ways data will arrive. */
export default function PerangkatScreen() {
  const { openFeature, openSettings } = useTabNavigation();

  return (
    <HDScreen title="Perangkat" subtitle="Perangkat, grup, sirkuit, dan meter lokasi">
      <View style={styles.section}>
        <HDText variant="section">Belum ada perangkat</HDText>
        <HDText>Perangkat muncul di sini setelah ada data energi. HematDaya tidak mengendalikan perangkat.</HDText>
        <HDButton variant="primary" onPress={() => openFeature('sumber-meter')}>
          Tambah sumber
        </HDButton>
        <HDButton onPress={() => openFeature('impor-data')}>Impor data</HDButton>
        <HDButton variant="text" onPress={() => openFeature('daftar-perangkat')}>
          Lihat rencana fitur ini
        </HDButton>
      </View>
      <HDButton variant="text" onPress={openSettings}>
        Pengaturan
      </HDButton>
    </HDScreen>
  );
}

const styles = StyleSheet.create({ section: { gap: tokens.space.stack } });
