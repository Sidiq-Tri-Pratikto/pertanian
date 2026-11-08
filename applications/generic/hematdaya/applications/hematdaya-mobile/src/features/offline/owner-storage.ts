import AsyncStorage from '@react-native-async-storage/async-storage';

import type { ScopePair } from '@/api/client';
import { ApiError } from '@/api/errors';

export type StorageSection = 'summaries' | 'asset-drafts' | 'import-draft' | 'scope' | 'scope-attempt';
const SECTIONS: StorageSection[] = ['summaries', 'asset-drafts', 'import-draft', 'scope', 'scope-attempt'];
export type OwnerStorage = {
  epoch: string;
  read: (section: StorageSection) => Promise<string | null>;
  write: (section: StorageSection, value: string) => Promise<boolean>;
  update: (section: StorageSection, change: (before: string | null) => string) => Promise<boolean>;
};

export function ownerStorageKey(epoch: string, section: StorageSection | 'import-recovery') {
  return `hematdaya.offline.v1.${epoch}.${section}`;
}

/** Deletion follows credential-epoch revocation, so failures leave unreachable records. */
export async function removeOwnerData(epoch: string): Promise<void> {
  await AsyncStorage.multiRemove(SECTIONS.map((section) => ownerStorageKey(epoch, section)));
}

export type ScopeFence = { epoch: number; pair: ScopePair | null };
export type ScopeAttempt = { id: string; base: ScopePair };

function revision(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}

function pair(value: unknown): value is ScopePair {
  const candidate = value as Partial<ScopePair> | null;
  return revision(candidate?.binding) && revision(candidate?.selection);
}

export function readScopeFence(raw: string | null): ScopeFence {
  const value: unknown = raw === null ? 0 : JSON.parse(raw);
  if (revision(value)) return { epoch: value, pair: null };
  const fence = value as Partial<ScopeFence> | null;
  if (revision(fence?.epoch) && (fence.pair === null || pair(fence.pair))) {
    return { epoch: fence.epoch, pair: fence.pair };
  }
  throw ApiError.storage();
}

/** A reload can observe these fences only. There is no proposal to resend. */
export function readScopeAttempt(raw: string | null): ScopeAttempt | null {
  const value = (raw === null ? null : JSON.parse(raw)) as Partial<ScopeAttempt> | null;
  if (value === null) return null;
  if (typeof value?.id === 'string' && value.id.length > 0 && pair(value.base)) return { id: value.id, base: value.base };
  throw ApiError.storage();
}
