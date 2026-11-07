import { useLocalSearchParams } from 'expo-router';

import { AssetDetailScreen } from '@/features/assets/AssetDetailScreen';

export default function AssetRoute() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <AssetDetailScreen assetId={id} />;
}
