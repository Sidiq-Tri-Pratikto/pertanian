import { useLocale } from '@/features/localization/locale';
import { useCopy } from '@/features/localization/messages';
import { Redirect, useLocalSearchParams } from 'expo-router';

import { HDComingSoon } from '@/components/hd/HDComingSoon';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDScreen } from '@/components/hd/HDScreen';
import { useTabNavigation } from '@/features/navigation';
import { findFeature, localizedFeature } from '@/features/registry';

/** One screen for every planned feature, so no route pretends to work before its pull request ships. */
export default function SegeraHadirScreen() {
  const say = useCopy();
  const locale = useLocale();
  const { feature: featureId } = useLocalSearchParams<{ feature: string }>();
  const { back, scopeHref } = useTabNavigation();
  if (featureId === 'cakupan-sumber') return <Redirect href={scopeHref} />;
  const feature = findFeature(featureId);

  if (!feature) {
    return (
      <HDScreen title={say("Fitur tidak ditemukan", "Feature not found")} onBack={back}>
        <HDNotice tone="neutral" title={say("Halaman ini tidak tersedia", "This page is unavailable")}>{say("Kembali ke halaman sebelumnya untuk melanjutkan.", "Go back to continue.")}</HDNotice>
      </HDScreen>
    );
  }

  return (
    <HDScreen title={localizedFeature(feature, locale).title} onBack={back}>
      <HDComingSoon feature={feature} />
    </HDScreen>
  );
}
