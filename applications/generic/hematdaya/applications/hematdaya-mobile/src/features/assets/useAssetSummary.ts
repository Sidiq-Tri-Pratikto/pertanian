import { useScopedSummary } from '@/features/energy/useSummary';

/** One asset's summary for the shared period. */
export function useAssetSummary(assetId: string | undefined) {
  return useScopedSummary({ kind: 'asset', assetId: assetId ?? '' }, assetId !== undefined);
}
