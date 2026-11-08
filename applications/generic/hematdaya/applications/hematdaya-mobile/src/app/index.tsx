import AsyncStorage from '@react-native-async-storage/async-storage';
import { Redirect, useRouter } from 'expo-router';
import { useEffect, useRef, useState, type ComponentRef } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { DemoSheet } from '@/features/workspace/DemoSheet';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

const EXPLORED_KEY = 'hematdaya.welcome.explored.v1';

/** S01 offers a demo or empty Home without requiring setup. */
export default function WelcomeScreen() {
  const router = useRouter();
  const { status, workspace, ended } = useWorkspace();
  const [explored, setExplored] = useState<boolean | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const demoButton = useRef<ComponentRef<typeof View>>(null);

  useEffect(() => {
    let active = true;
    const read = async () => {
      const saved = await AsyncStorage.getItem(EXPLORED_KEY).catch(() => null);
      if (active) setExplored(saved === 'true');
    };
    void read();
    return () => { active = false; };
  }, []);

  const openHome = async () => {
    // A preference write can fail without preventing navigation to Home.
    await AsyncStorage.setItem(EXPLORED_KEY, 'true').catch(() => undefined);
    router.replace('/beranda');
  };

  if (status === 'loading' || explored === null) {
    return (
      <HDScreen title="HematDaya">
        <HDProgressStatus state="loading" label="Memuat HematDaya…" />
      </HDScreen>
    );
  }
  if (!sheetOpen && (workspace || explored || ended === 'expired')) {
    return <Redirect href="/beranda" />;
  }

  return (
    <HDScreen title="Selamat datang">
      <HDText variant="section">Lihat pemakaian listrik dan apa yang berubah.</HDText>
      <HDText>Coba dengan data contoh. HematDaya hanya membaca data, tanpa mengendalikan perangkat.</HDText>
      <View style={styles.actions}>
        <View ref={demoButton}>
          <HDButton variant="primary" fullWidth onPress={() => setSheetOpen(true)}>
            Coba demo
          </HDButton>
        </View>
        <HDButton fullWidth onPress={openHome}>Lanjut tanpa data</HDButton>
      </View>
      <DemoSheet
        open={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onOpened={openHome}
        returnFocusTo={demoButton}
      />
    </HDScreen>
  );
}

const styles = StyleSheet.create({ actions: { gap: tokens.space.stackTight } });
