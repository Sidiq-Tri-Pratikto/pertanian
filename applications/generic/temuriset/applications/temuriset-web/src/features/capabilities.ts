import { cache } from 'react';

import type { CapabilityManifest } from '@/api/client';
import { serverGet } from '@/api/server';
import type { Capabilities } from '@/features/registry';

export function hasCapability(manifest: CapabilityManifest, id: string): boolean {
  return manifest.capabilities.some((capability) => capability.id === id);
}

// Share one manifest read per server render. If it fails, optional features stay hidden.
export const readCapabilityManifest = cache(async (): Promise<CapabilityManifest | null> => {
  try {
    return await serverGet<CapabilityManifest>('/api/v1/capabilities');
  } catch {
    return null;
  }
});

export async function readCapabilities(): Promise<Capabilities> {
  const manifest = await readCapabilityManifest();
  if (!Array.isArray(manifest?.capabilities)) return null;
  return manifest.capabilities.map((capability) => capability?.id).filter((id) => typeof id === 'string');
}

export async function readAdapterAvailability(id: string): Promise<boolean> {
  const manifest = await readCapabilityManifest();
  return Array.isArray(manifest?.adapters) && manifest.adapters.some((adapter) => adapter?.id === id && adapter.status === 'available');
}
