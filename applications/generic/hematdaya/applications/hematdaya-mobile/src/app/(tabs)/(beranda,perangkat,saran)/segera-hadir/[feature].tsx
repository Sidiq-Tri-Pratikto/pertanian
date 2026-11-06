import { useLocalSearchParams } from 'expo-router';

import { HDComingSoon } from '@/components/hd/HDComingSoon';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDScreen } from '@/components/hd/HDScreen';
import { useTabNavigation } from '@/features/navigation';
import { findFeature } from '@/features/registry';

/** One screen for every planned feature, so no route pretends to work before its pull request ships. */
export default function SegeraHadirScreen() {
  const { feature: featureId } = useLocalSearchParams<{ feature: string }>();
  const { back } = useTabNavigation();
  const feature = findFeature(featureId);

  if (!feature) {
    return (
      <HDScreen title="Fitur tidak ditemukan" onBack={back}>
        <HDNotice tone="neutral" title="Halaman ini tidak tersedia">
          Kembali ke halaman sebelumnya untuk melanjutkan.
        </HDNotice>
      </HDScreen>
    );
  }

  return (
    <HDScreen title={feature.title} onBack={back}>
      <HDComingSoon feature={feature} />
    </HDScreen>
  );
}
