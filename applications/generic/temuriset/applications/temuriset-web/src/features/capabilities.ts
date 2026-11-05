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
export const readCapabilities = cache(async (): Promise<Capabilities> => {
  try {
    const manifest = await serverGet<CapabilityManifest>('/api/v1/capabilities');
    return manifest.capabilities.map((capability) => capability.id);
  } catch {
    return null;
  }
});
