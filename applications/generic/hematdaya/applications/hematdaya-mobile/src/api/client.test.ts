import { getAsset, getArchivedAssets, getAssets, getCapabilities, getSummary, isAssetPatchRefusal, patchAsset, type Asset, type CapabilityManifest } from '@/api/client';
import { ApiError } from '@/api/errors';

import summaryFixtures from '../../tests/fixtures/assets.json';

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

const asset = {
  id: 'df5eb61e-f5ea-43a6-93b2-07dc913394df',
  name: 'Kulkas dapur',
  category: null,
  location: '',
  scope_kind: 'device',
  parent_asset_id: null,
  expected_use: 'unknown',
  archived: false,
} satisfies Asset;
const detail = { ...asset, sources: [], bindings: [] };
const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

describe('asset write and reconciliation contract', () => {
  afterEach(() => jest.restoreAllMocks());

  it('sends the captured fields and bearer and accepts an exact 200 acknowledgment', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(response(asset));

    await expect(patchAsset(asset.id, { name: asset.name, location: '' }, 'bearer')).resolves.toEqual(asset);
    expect(fetchMock).toHaveBeenCalledWith(expect.stringMatching(new RegExp(`/assets/${asset.id}$`)), expect.objectContaining({
      method: 'PATCH',
      body: JSON.stringify({ name: asset.name, location: '' }),
      headers: { Authorization: 'Bearer bearer', 'Content-Type': 'application/json' },
      signal: expect.anything(),
    }));
  });

  it.each([
    response({ ...asset, id: 'other' }),
    response({ ...asset, name: 'Unrelated' }),
    response({ ...asset, archived: null }),
    response(asset, 201),
    new Response(null, { status: 204 }),
  ])('rejects a nonmatching or unexpected acknowledgment', async (invalid) => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(invalid);
    await expect(patchAsset(asset.id, { name: asset.name }, 'bearer')).rejects.toMatchObject({ code: 'UNEXPECTED_RESPONSE' });
  });

  it.each([[401, 'UNAUTHORIZED'], [401, 'SESSION_EXPIRED'], [404, 'NOT_FOUND'], [422, 'VALIDATION_FAILED']] as const)(
    'keeps a valid %i %s refusal with its status and reference', async (status, code) => {
      jest.spyOn(globalThis, 'fetch').mockResolvedValue(response({
        error: { code, message: 'Isian ditolak. Periksa kembali.', request_id: 'ref-save', recovery: { retryable: false } },
      }, status));
      const failure = await patchAsset(asset.id, { name: asset.name }, 'bearer').then(() => { throw new Error('Expected PATCH to fail'); }, ApiError.from);
      expect(failure).toMatchObject({ code, status, requestId: 'ref-save' });
      expect(isAssetPatchRefusal(failure)).toBe(true);
    },
  );

  it.each([[500, 'VALIDATION_FAILED', { retryable: false }], [404, 'VALIDATION_FAILED', { retryable: false }], [422, 'VALIDATION_FAILED', {}]] as const)(
    'cannot confirm a rejection with status %i and code %s without the documented pair and envelope', async (status, code, recovery) => {
      jest.spyOn(globalThis, 'fetch').mockResolvedValue(response({
        error: { code, message: 'Isian ditolak. Periksa kembali.', request_id: 'ref-unknown', recovery },
      }, status));
      const failure = await patchAsset(asset.id, { name: asset.name }, 'bearer').then(() => { throw new Error('Expected PATCH to fail'); }, ApiError.from);
      expect(isAssetPatchRefusal(failure)).toBe(false);
    },
  );

  it('classifies a fetch timeout as unknown', async () => {
    jest.spyOn(globalThis, 'fetch').mockRejectedValue(new DOMException('timeout', 'TimeoutError'));
    const failure = await patchAsset(asset.id, { name: asset.name }, 'bearer').then(() => { throw new Error('Expected PATCH to fail'); }, ApiError.from);
    expect(failure).toMatchObject({ code: 'NETWORK_UNREACHABLE' });
    expect(isAssetPatchRefusal(failure)).toBe(false);
  });

  it.each([detail, { ...detail, id: 'other' }, { ...detail, bindings: [{}] }])('requires valid owned detail from a fresh GET', async (payload) => {
    jest.spyOn(globalThis, 'fetch').mockResolvedValue(response(payload));
    const read = getAsset(asset.id, 'bearer');
    if (payload === detail) await expect(read).resolves.toEqual(detail);
    else await expect(read).rejects.toMatchObject({ code: 'UNEXPECTED_RESPONSE' });
  });
});

describe('asset cursor reads', () => {
  afterEach(() => jest.restoreAllMocks());

  it('forwards include_archived on every page and deduplicates asset IDs', async () => {
    const another = { ...asset, id: '92ed0b7f-26da-46de-bc5a-f57cb3008dc3', archived: true };
    const fetchMock = jest.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({ items: [asset], next_cursor: 'next' }))
      .mockResolvedValueOnce(response({ items: [asset, another], next_cursor: null }));

    await expect(getArchivedAssets('site', 'bearer')).resolves.toEqual({ items: [asset, another], next_cursor: null });
    expect(fetchMock.mock.calls.map(([url]) => new URL(String(url)).searchParams.get('include_archived'))).toEqual(['true', 'true']);
    expect(String(fetchMock.mock.calls[1][0])).toContain('cursor=next');
  });

  it('rejects an invalid archived flag and keeps the legacy active-only request shape', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(response({ items: [{ ...asset, archived: 'false' }], next_cursor: null }))
      .mockResolvedValueOnce(response({ items: [asset], next_cursor: null }));
    await expect(getArchivedAssets('site', 'bearer')).rejects.toMatchObject({ code: 'UNEXPECTED_RESPONSE' });
    await expect(getAssets('site', 'bearer')).resolves.toEqual([asset]);
    expect(String(fetchMock.mock.calls[1][0])).not.toContain('include_archived');
  });

  it('reports incompleteness if a cursor survives the page bound', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      response({ items: [asset], next_cursor: 'keeps-going' }));
    await expect(getArchivedAssets('site', 'bearer')).resolves.toEqual({ items: [asset], next_cursor: 'keeps-going' });
    expect(fetchMock).toHaveBeenCalledTimes(20);
  });
});

describe('summary freshness boundary', () => {
  const { summary } = summaryFixtures['h-base'];
  const router = summary.assets.find((row) => row.name === 'Router')!;
  const source = {
    source_id: 'source-router', asset_id: router.asset_id, label: 'Router', origin: 'simulated',
    state: 'stale', last_capture_at: '2026-10-25T11:00:00Z', cadence_seconds: 3600, policy_version: 1,
    historical_range: null,
  };
  afterEach(() => jest.restoreAllMocks());

  it('accepts legacy absence and one typed source capture without adding other requests', async () => {
    const fetch = jest.spyOn(globalThis, 'fetch').mockResolvedValueOnce(response(summary))
      .mockResolvedValueOnce(response({ ...summary, source_freshness: [source] }));
    await expect(getSummary('site', { preset: 'last_7_days' }, 'token')).resolves.not.toHaveProperty('source_freshness');
    await expect(getSummary('site', { preset: 'last_7_days' }, 'token')).resolves.toMatchObject({ source_freshness: [source] });
    expect(fetch.mock.calls.map(([url, init]) => [new URL(String(url)).pathname, init?.method])).toEqual([
      ['/api/v1/sites/site/summary', 'GET'], ['/api/v1/sites/site/summary', 'GET'],
    ]);
  });

  it.each([{ cadence_seconds: 0 }, { last_capture_at: null }, { state: 'historical' }, { asset_id: 'other' }])(
    'rejects malformed freshness %# without retaining an untrusted field', async (changes) => {
      jest.spyOn(globalThis, 'fetch').mockResolvedValue(response({
        ...summary, source_freshness: [{ ...source, ...changes, token: 'fake-summary-token' }],
      }));
      await expect(getSummary('site', { preset: 'last_7_days' }, 'token'))
        .rejects.toMatchObject({ code: 'UNEXPECTED_RESPONSE', recovery: { retryable: false } });
    },
  );
});
