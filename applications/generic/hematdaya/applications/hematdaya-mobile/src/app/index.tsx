import { useRouter } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { CONTEXT_OPTIONS, useContextPreset } from '@/features/context-preset';

/** S01: value statement, start, demo, and a skippable context choice. No account, no permission prompt. */
export default function WelcomeScreen() {
  const router = useRouter();
  const { preset, setPreset } = useContextPreset();

  return (
    <HDScreen title="Selamat datang" subtitle="Pemantauan listrik dan saran berbasis data">
      <HDText variant="section">Pahami energi yang dipantau, lalu periksa perubahan berdasarkan data.</HDText>
      <HDText>
        HematDaya hanya membaca dan menjelaskan energi listrik yang tercatat. Aplikasi ini tidak menyalakan atau
        mematikan perangkat apa pun.
      </HDText>
      <HDChoiceGroup
        legend="Konteks penggunaan"
        optional
        help="Hanya mengubah contoh. Tidak mengubah data, izin, perhitungan, atau jadwal."
        options={CONTEXT_OPTIONS}
        value={preset}
        onChange={setPreset}
      />
      <View style={styles.actions}>
        <HDButton variant="primary" fullWidth onPress={() => router.replace('/beranda')}>
          Mulai
        </HDButton>
        <HDButton fullWidth onPress={() => router.push('/segera-hadir/demo', { withAnchor: true })}>
          Coba demo
        </HDButton>
        <HDButton
          variant="text"
          fullWidth
          onPress={() => {
            setPreset('unspecified');
            router.replace('/beranda');
          }}>
          Lewati
        </HDButton>
      </View>
      <HDText variant="label" tone="secondary">
        Tidak perlu akun, alat ukur, AC, tarif, jadwal, data produksi, atau izin notifikasi.
      </HDText>
    </HDScreen>
  );
}

const styles = StyleSheet.create({ actions: { gap: tokens.space.stackTight } });
