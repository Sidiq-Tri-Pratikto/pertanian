import { LanguageSetting } from '@/features/localization/LanguageSetting';
import { useCopy, useLabels } from '@/features/localization/messages';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Redirect, useRouter, type Href } from 'expo-router';
import { useEffect, useRef, useState, type ComponentRef } from 'react';
import { StyleSheet, View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { HOME_METER_SETUP } from '@/features/navigation';
import { DemoSheet } from '@/features/workspace/DemoSheet';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';

const EXPLORED_KEY = 'hematdaya.welcome.explored.v1';

/** S01 leads to meter setup and also allows exploring without data. */
export default function WelcomeScreen() {
  const say = useCopy();
  const labels = useLabels();
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

  const openDestination = async (destination: Href) => {
    // A preference write can fail without preventing navigation to Home.
    await AsyncStorage.setItem(EXPLORED_KEY, 'true').catch(() => undefined);
    router.replace(destination);
  };
  const openHome = () => openDestination('/beranda');

  if (status === 'loading' || explored === null) {
    return (
      <HDScreen title="HematDaya">
        <HDProgressStatus state="loading" label={say("Memuat HematDaya…", "Loading HematDaya…")} />
      </HDScreen>
    );
  }
  if (!sheetOpen && (workspace || explored || ended === 'expired')) {
    return <Redirect href="/beranda" />;
  }

  return (
    <HDScreen title={say("Selamat datang", "Welcome")}>
      <HDText variant="section">{say("Lihat pemakaian listrik dan apa yang berubah.", "See how much electricity you use and what changed.")}</HDText>
      <HDText>{say("Hubungkan alat ukur yang didukung untuk memantau pemakaian listrik. Anda juga bisa mencoba data demo.", "Connect a supported meter to track electricity use. You can also try the demo.")}</HDText>
      <View style={styles.actions}>
        <HDButton variant="primary" fullWidth onPress={() => openDestination(HOME_METER_SETUP)}>{labels.connectMeter}</HDButton>
        <View ref={demoButton}>
          <HDButton fullWidth onPress={() => setSheetOpen(true)}>{say("Coba demo", "Try demo")}</HDButton>
        </View>
        <HDButton variant="text" fullWidth onPress={openHome}>{say("Lanjut tanpa data", "Continue without data")}</HDButton>
      </View>
      <LanguageSetting />
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
