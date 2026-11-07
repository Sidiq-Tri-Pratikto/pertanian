import { useLocalSearchParams } from 'expo-router';

import { ImportScreen } from '@/features/imports/ImportScreen';

export default function ImportRoute() {
  const { step } = useLocalSearchParams<{ step: string }>();
  return <ImportScreen step={step} />;
}
