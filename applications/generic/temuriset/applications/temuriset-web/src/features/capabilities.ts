import { cache } from 'react';

import type { CapabilityManifest } from '@/api/client';
import { serverGet } from '@/api/server';
import type { Capabilities } from '@/features/registry';

export function hasCapability(manifest: CapabilityManifest, id: string): boolean {
  return manifest.capabilities.some((capability) => capability.id === id);
}

/**
 * Reads the manifest once per server render. When it cannot be read, optional features stay hidden: the page never
 * advertises what the deployment may not run, and the service refuses it anyway.
 */
export const readCapabilityManifest = cache(async (): Promise<CapabilityManifest | null> => {
  try {
    return await serverGet<CapabilityManifest>('/api/v1/capabilities');
  } catch {
    return null;
  }
});


export async function readCapabilities(): Promise<Capabilities> {
  const manifest = await readCapabilityManifest();
  return manifest?.capabilities.map((capability) => capability.id) ?? null;
}
