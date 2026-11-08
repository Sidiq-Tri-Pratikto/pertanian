import AsyncStorage from '@react-native-async-storage/async-storage';

export type StorageSection = 'summaries' | 'asset-drafts' | 'import-draft' | 'scope';
const SECTIONS: StorageSection[] = ['summaries', 'asset-drafts', 'import-draft', 'scope'];
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
