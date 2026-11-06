import { useLocalSearchParams } from 'expo-router';

import { EvidenceScreen } from '@/features/insights/EvidenceScreen';

export default function EvidenceRoute() {
  const { id, revision } = useLocalSearchParams<{ id: string; revision?: string }>();
  const parsed = revision !== undefined && /^[1-9]\d*$/.test(revision) ? Number(revision) : undefined;
  return <EvidenceScreen insightId={id} revision={parsed} />;
}
