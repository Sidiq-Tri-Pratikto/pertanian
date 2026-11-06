import { getCapabilities, type CapabilityManifest } from '@/api/client';
import { ApiError } from '@/api/errors';

const manifest = {
  schema_version: 1,
  source_release: '0.1.0',
  composition: { id: 'core-plus-optional', version: 1 },
  capabilities: [{ id: 'core', optional: false, status: 'planned' }],
  adapters: [{ id: 'csv', status: 'planned' }],
  policies: [{ id: 'baseline', version: 1 }],
} satisfies CapabilityManifest;

const fakeSecret = 'fake-manifest-secret';

describe('getCapabilities', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('returns a valid manifest from the service', async () => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(manifest)));

    await expect(getCapabilities()).resolves.toEqual(manifest);
  });

  it.each([
    ['invalid JSON', `<html>${fakeSecret}</html>`],
    ['null', 'null'],
    ['a missing manifest', JSON.stringify({ detail: fakeSecret })],
    ['a blank release', JSON.stringify({ ...manifest, source_release: ' ' })],
    ['an invalid version', JSON.stringify({ ...manifest, schema_version: 1.5 })],
    ['an invalid composition', JSON.stringify({ ...manifest, composition: { id: 'core' } })],
    ['an invalid capability', JSON.stringify({ ...manifest, capabilities: [{ id: 'core', status: 'planned' }] })],
    ['an invalid adapter status', JSON.stringify({ ...manifest, adapters: [{ id: 'csv', status: fakeSecret }] })],
    ['an invalid policy version', JSON.stringify({ ...manifest, policies: [{ id: 'baseline', version: '1' }] })],
  ])('rejects a success response containing %s', async (_, body) => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(body));

    const request = getCapabilities();

    await expect(request).rejects.toBeInstanceOf(ApiError);
    await expect(request).rejects.toMatchObject({
      code: 'UNEXPECTED_RESPONSE',
      message: 'Layanan mengirim jawaban yang tidak dikenali. Coba lagi nanti.',
      requestId: null,
      recovery: { retryable: false },
    });
  });
});
