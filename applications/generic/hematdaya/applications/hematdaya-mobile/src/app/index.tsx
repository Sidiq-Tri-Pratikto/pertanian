import { Redirect, useRouter } from 'expo-router';
import { useRef, useState, type ComponentRef } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { CONTEXT_OPTIONS, useContextPreset } from '@/features/context-preset';
import { DemoSheet } from '@/features/workspace/DemoSheet';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useDemoSession } from '@/features/workspace/useDemoSession';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

/** S01: value statement, start, demo, and a skippable context choice. No account, no permission prompt. */
export default function WelcomeScreen() {
  const router = useRouter();
  const { status, workspace } = useWorkspace();
  const { preset, setPreset } = useContextPreset();
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);
  const empty = useDemoSession();

  if (status === 'loading') {
    return (
      <HDScreen title="HematDaya">
        <HDProgressStatus state="loading" label="Memuat ruang kerja…" />
      </HDScreen>
    );
  }
  if (workspace && !sheetOpen && empty.state.kind === 'idle') {
    return <Redirect href="/beranda" />;
  }

  const startEmpty = async () => {
    if (await empty.start('empty')) {
      router.replace('/beranda');
    }
  };

  return (
    <HDScreen title="Selamat datang" subtitle="Pemantauan listrik dan saran berbasis data">
      <SessionEndedNotice />
      <HDText variant="section">Pahami energi yang dipantau, lalu periksa perubahan berdasarkan data.</HDText>
      <HDText>
        HematDaya hanya membaca dan menjelaskan energi listrik yang tercatat. Aplikasi ini tidak menyalakan atau
        mematikan perangkat apa pun.
      </HDText>
      <HDChoiceGroup
        legend="Konteks penggunaan"
        optional
        help="Hanya mengubah contoh dan pilihan demo awal. Tidak mengubah data, izin, perhitungan, atau jadwal."
        options={CONTEXT_OPTIONS}
        value={preset}
        onChange={setPreset}
      />
      <View style={styles.actions}>
        <HDButton
          variant="primary"
          fullWidth
          loading={empty.state.kind === 'pending'}
          loadingLabel="Menyiapkan ruang kerja…"
          onPress={startEmpty}>
          Mulai
        </HDButton>
        <View ref={demoButton}>
          <HDButton fullWidth onPress={() => setSheetOpen(true)}>
            Coba demo
          </HDButton>
        </View>
        <HDButton
          variant="text"
          fullWidth
          onPress={() => {
            setPreset('unspecified');
            void startEmpty();
          }}>
          Lewati
        </HDButton>
      </View>
      <HDProgressStatus
        state={empty.state.kind === 'failed' ? 'failure' : empty.state.kind === 'unknown' ? 'unknown' : null}
        detail={empty.state.kind === 'failed' || empty.state.kind === 'unknown' ? empty.state.error.message : null}
        action={
          empty.state.kind === 'failed' && empty.state.canRetry ? (
            <HDButton variant="text" icon="refresh" onPress={async () => (await empty.retry()) && router.replace('/beranda')}>
              Coba lagi
            </HDButton>
          ) : empty.state.kind === 'unknown' ? (
            <HDButton variant="text" onPress={async () => (await empty.startOver('empty')) && router.replace('/beranda')}>
              Mulai ruang kerja baru
            </HDButton>
          ) : null
        }
      />
      <HDText variant="label" tone="secondary">
        Mulai membuka ruang kerja sementara yang berakhir otomatis sampai akun tersedia. Tidak perlu akun, alat ukur,
        AC, tarif, jadwal, data produksi, atau izin notifikasi.
      </HDText>
      <DemoSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onOpened={() => {
          setSheetOpen(false);
          router.replace('/beranda');
        }}
        returnFocusTo={demoButton}
      />
    </HDScreen>
  );
}

const styles = StyleSheet.create({ actions: { gap: tokens.space.stackTight } });
