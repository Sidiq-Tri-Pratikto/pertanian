import { LanguageSetting } from '@/features/localization/LanguageSetting';
import { useCopy } from '@/features/localization/messages';
import Constants from 'expo-constants';
import { View } from 'react-native';

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
  const { back, openFeature } = useTabNavigation();
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
