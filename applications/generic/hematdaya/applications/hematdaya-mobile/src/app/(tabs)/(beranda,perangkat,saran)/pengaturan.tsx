import { LanguageSetting } from '@/features/localization/LanguageSetting';
import { useCopy, useLabels } from '@/features/localization/messages';
import Constants from 'expo-constants';
import { View } from 'react-native';

import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { contextOptions, useContextPreset } from '@/features/context-preset';
import { FeatureRow } from '@/features/FeatureRow';
import { useTabNavigation } from '@/features/navigation';
import { FEATURES } from '@/features/registry';

/** S09 shell: settings are planned, so this lists what is coming and states the version. */
export default function PengaturanScreen() {
  const say = useCopy();
  const labels = useLabels();
  const { back, openFeature, openMeterSetup } = useTabNavigation();
  const { preset, setPreset } = useContextPreset();

  return (
    <HDScreen title={say("Pengaturan", "Settings")} onBack={back}>
      <LanguageSetting />
      <HDChoiceGroup
        legend={say("Konteks penggunaan", "Usage context")}
        optional
        help={say("Hanya mengubah contoh yang ditampilkan.", "This changes only the examples shown.")}
        options={contextOptions()}
        value={preset}
        onChange={setPreset}
      />
      <HDButton variant="text" onPress={openMeterSetup}>{labels.connectMeter}</HDButton>
      <View>
        <HDText variant="section">{say("Rencana fitur", "Planned features")}</HDText>
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
