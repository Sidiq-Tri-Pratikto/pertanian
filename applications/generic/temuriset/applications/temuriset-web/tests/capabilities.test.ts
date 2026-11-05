import type { CapabilityManifest } from '@/api/client';
import { ApiError } from '@/api/errors';

vi.mock('next/headers', () => ({
  cookies: async () => ({ toString: () => 'tr_persona=mitra' }),
}));

const { serverGet } = await import('@/api/server');
const { hasCapability, readCapabilities } = await import('@/features/capabilities');
const { findFeature, isOffered } = await import('@/features/registry');

const manifest = {
  capabilities: [
    { id: 'core', optional: false, status: 'planned' },
    { id: 'company_funding', optional: true, status: 'planned' },
  ],
} as CapabilityManifest;

function respond(status: number, body: unknown) {
  return vi.fn(async () => new Response(JSON.stringify(body), { status }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('server reads', () => {
  it('forward the visitor cookies to the service', async () => {
    const fetch = respond(200, manifest);
    vi.stubGlobal('fetch', fetch);

    expect(await serverGet('/api/v1/capabilities')).toEqual(manifest);
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8020/api/v1/capabilities',
      expect.objectContaining({ headers: { cookie: 'tr_persona=mitra' }, cache: 'no-store' }),
    );
  });

  it('turn the service failure envelope into an ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      respond(403, {
        error: { code: 'CAPABILITY_UNAVAILABLE', message: 'Fitur ini tidak tersedia.', request_id: 'ref_1', recovery: { retryable: false } },
      }),
    );

    await expect(serverGet('/api/v1/x')).rejects.toMatchObject({ code: 'CAPABILITY_UNAVAILABLE', requestId: 'ref_1' });
  });

  it('report an unreachable service', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('fetch failed'))));

    await expect(serverGet('/api/v1/x')).rejects.toEqual(ApiError.unreachable());
  });
});

describe('capabilities', () => {
  it('reads the selected capability ids from the manifest', async () => {
    vi.stubGlobal('fetch', respond(200, manifest));

    expect(await readCapabilities()).toEqual(['core', 'company_funding']);
    expect(hasCapability(manifest, 'company_funding')).toBe(true);
    expect(hasCapability(manifest, 'organization_review')).toBe(false);
  });

  it('reads nothing when the manifest is unavailable', async () => {
    vi.stubGlobal('fetch', respond(503, {}));

    expect(await readCapabilities()).toBeNull();
  });

  it('offers a feature only when its capability is selected', () => {
    const funding = findFeature('pendanaan-perusahaan')!;
    const portfolio = findFeature('inovasi')!;

    expect(isOffered(funding, ['core', 'company_funding'])).toBe(true);
    expect(isOffered(funding, ['core'])).toBe(false);
    expect(isOffered(funding, null)).toBe(false);
    expect(isOffered(portfolio, null)).toBe(true);
  });
});
