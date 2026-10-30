import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { useTabNavigation } from '@/features/navigation';

/** S07 before any data exists. No invented alarms: an empty list stays empty. */
export default function SaranScreen() {
  const { openFeature, openSettings } = useTabNavigation();

  return (
    <HDScreen title="Saran" subtitle="Pengamatan berbasis bukti, bukan diagnosis">
      <View style={styles.section}>
        <HDText variant="section">Belum ada saran</HDText>
        <HDText>Saran hanya muncul dari data yang tercatat. Ini bukan penilaian efisiensi atau keamanan.</HDText>
        <HDButton variant="text" onPress={() => openFeature('saran')}>
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
