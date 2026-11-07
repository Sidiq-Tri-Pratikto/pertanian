import Constants from 'expo-constants';
import { View } from 'react-native';

import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { FeatureRow } from '@/features/FeatureRow';
import { useTabNavigation } from '@/features/navigation';
import { FEATURES } from '@/features/registry';

/** S09 shell: settings are planned, so this lists what is coming and states the version. */
export default function PengaturanScreen() {
  const { back, openFeature } = useTabNavigation();

  return (
    <HDScreen title="Pengaturan" onBack={back}>
      <View>
        <HDText variant="section">Rencana fitur</HDText>
        {FEATURES.filter((feature) => feature.status === 'coming_soon').map((feature) => (
          <FeatureRow key={feature.id} feature={feature} onPress={() => openFeature(feature.id)} />
        ))}
      </View>
      <HDText variant="label" tone="secondary">
        HematDaya {Constants.expoConfig?.version ?? ''} · HematDaya Design System 1.0.0-draft
      </HDText>
    </HDScreen>
  );
}
