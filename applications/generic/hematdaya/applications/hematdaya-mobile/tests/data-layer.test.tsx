import { fireEvent, render, screen } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { useRef, type ComponentRef } from 'react';
import { AccessibilityInfo, Platform, View } from 'react-native';

import {
  commitImport,
  getAsset,
  getAssets,
  getAssetSummary,
  getImport,
  getImportErrors,
  getSummary,
  IMPORT_COMMIT_TIMEOUT_MS,
  IMPORT_PREVIEW_TIMEOUT_MS,
  previewImport,
} from '@/api/client';
import { ApiError } from '@/api/errors';
import { endsSession, retryDelay, shouldRetry } from '@/api/query-client';
import { HDSheetDialog } from '@/components/hd/HDSheetDialog';
import { clearImportDraft, loadImportDraft, saveImportDraft } from '@/features/imports/draft-store';
import { clearWorkspace, loadWorkspace, saveWorkspace, type Workspace } from '@/features/workspace/workspace-store';

import recordedImports from './fixtures/imports.json';

const workspace: Workspace = {
  token: 'hdd_v1_fake',
  siteId: 'site-1',
  scenarioId: 'h-base',
  expiresAt: '2099-01-01T00:00:00Z',
  initialPeriod: { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' },
};

describe('query retry policy', () => {
  it('retries only retryable failures, counting the first attempt', () => {
    const retryable = new ApiError('DATABASE_UNAVAILABLE', 'x', { retryable: true, retry_after_seconds: 30, max_attempts: 3 });
    const final = new ApiError('INTERNAL_ERROR', 'x', { retryable: false });

    expect(shouldRetry(1, retryable)).toBe(true);
    expect(shouldRetry(2, retryable)).toBe(true);
    expect(shouldRetry(3, retryable)).toBe(false);
    expect(shouldRetry(1, final)).toBe(false);
    expect(retryDelay(1, retryable)).toBe(30_000);
    expect(retryDelay(1, ApiError.unreachable())).toBe(1000);
  });

  it('treats expired or rejected credentials as the end of the workspace', () => {
    expect(endsSession(new ApiError('SESSION_EXPIRED', 'x', { retryable: false }))).toBe(true);
    expect(endsSession(new ApiError('UNAUTHORIZED', 'x', { retryable: false }))).toBe(true);
    expect(endsSession(new ApiError('NOT_FOUND', 'x', { retryable: false }))).toBe(false);
  });
});

describe('workspace store', () => {
  const realOS = Platform.OS;

  afterEach(() => {
    Platform.OS = realOS;
    globalThis.sessionStorage?.clear();
  });

  it('keeps the token in secure storage on native', async () => {
    await saveWorkspace(workspace);

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('hematdaya.workspace.v1', JSON.stringify(workspace));
    await expect(loadWorkspace()).resolves.toEqual(workspace);
    await clearWorkspace();
    await expect(loadWorkspace()).resolves.toBeNull();
  });

  it('uses sessionStorage on the web, where no secure store exists', async () => {
    Platform.OS = 'web';
    const storage = new Map<string, string>();
    Object.defineProperty(globalThis, 'sessionStorage', {
      configurable: true,
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
        clear: () => storage.clear(),
      },
    });

    await saveWorkspace(workspace);

    expect(storage.get('hematdaya.workspace.v1')).toBe(JSON.stringify(workspace));
    await expect(loadWorkspace()).resolves.toEqual(workspace);
  });

  it('ignores a damaged entry instead of crashing', async () => {
    await SecureStore.setItemAsync('hematdaya.workspace.v1', '{not json');

    await expect(loadWorkspace()).resolves.toBeNull();
  });
});

describe('api client', () => {
  afterEach(() => jest.restoreAllMocks());

  it('sends the bearer token and period, and refuses an unexpected body', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ secret: 'x' })));

    await expect(getSummary('site 1', { preset: 'today' }, 'hdd_v1_fake')).rejects.toMatchObject({
      code: 'UNEXPECTED_RESPONSE',
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain('/api/v1/sites/site%201/summary?preset=today');
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer hdd_v1_fake');
  });
});

describe('asset reads', () => {
  afterEach(() => jest.restoreAllMocks());

  const asset = (id: string) => ({ id, name: id, category: null, location: null, scope_kind: 'device', parent_asset_id: null, expected_use: 'unknown', archived: false });
  const notFound = {
    error: { code: 'NOT_FOUND', message: 'Data tidak ditemukan. Periksa kembali pilihan Anda.', request_id: 'ref_404', recovery: { retryable: false } },
  };

  it('follows every page of assets, in order, with the bearer token', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async (input) =>
      new URL(String(input)).searchParams.get('cursor')
        ? new Response(JSON.stringify({ items: [asset('b')], next_cursor: null }))
        : new Response(JSON.stringify({ items: [asset('a')], next_cursor: 'page 2' })),
    );

    await expect(getAssets('site 1', 'tok')).resolves.toMatchObject([{ id: 'a' }, { id: 'b' }]);

    const [firstUrl, firstInit] = fetchMock.mock.calls[0];
    expect(String(firstUrl)).toContain('/api/v1/sites/site%201/assets?limit=100');
    expect((firstInit?.headers as Record<string, string>).Authorization).toBe('Bearer tok');
    expect(new URL(String(fetchMock.mock.calls[1][0])).searchParams.get('cursor')).toBe('page 2');
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('stops after 20 pages when a cursor never ends', async () => {
    const fetchMock = jest
      .spyOn(globalThis, 'fetch')
      .mockImplementation(async () => new Response(JSON.stringify({ items: [asset('a')], next_cursor: 'again' })));

    await expect(getAssets('site-1', 'tok')).resolves.toHaveLength(20);

    expect(fetchMock).toHaveBeenCalledTimes(20);
  });

  it('encodes the asset ID and reads one asset', async () => {
    const fetchMock = jest
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue(new Response(JSON.stringify({ ...asset('a/b'), bindings: [], sources: [] })));

    await expect(getAsset('a/b', 'tok')).resolves.toMatchObject({ id: 'a/b' });

    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/assets/a%2Fb');
  });

  it('reads one asset summary for the period', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ window: {}, scope: {}, coverage: {}, assets: [], energy_kwh: null })),
    );

    await getAssetSummary('a 1', { preset: 'today' }, 'tok');

    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/assets/a%201/summary?preset=today');
  });

  it.each([
    ['getAssets', () => getAssets('s', 'tok')],
    ['getAsset', () => getAsset('a', 'tok')],
    ['getAssetSummary', () => getAssetSummary('a', { preset: 'today' }, 'tok')],
  ])('%s refuses an unexpected body and passes on a not-found failure', async (_name, read) => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async () => new Response(JSON.stringify({ secret: 'x' })));
    await expect(read()).rejects.toMatchObject({ code: 'UNEXPECTED_RESPONSE' });

    fetchMock.mockImplementation(async () => new Response(JSON.stringify(notFound), { status: 404 }));
    await expect(read()).rejects.toMatchObject({ name: 'ApiError', code: 'NOT_FOUND', requestId: 'ref_404' });
  });
});

describe('import client', () => {
  const realOS = Platform.OS;
  const Recorded = recordedImports as unknown as Record<string, Record<string, unknown>>;
  const reply = (body: unknown, status = 200) => async () => new Response(JSON.stringify(body), { status });

  afterEach(() => {
    Platform.OS = realOS;
    jest.restoreAllMocks();
  });

  function call(fetchMock: jest.SpyInstance, index = 0) {
    const [url, init] = fetchMock.mock.calls[index] as [string, RequestInit];
    return { url: String(url), init, headers: (init.headers ?? {}) as Record<string, string> };
  }

  it('posts a paste as form text with the answers as JSON text, the bearer token and the long preview timeout', async () => {
    const timeout = jest.spyOn(AbortSignal, 'timeout');
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(reply(Recorded.valid.first, 201));

    await expect(previewImport('site 1', { kind: 'paste', text: 'a' }, { timezone_confirmed: true }, 'tok')).resolves.toMatchObject({
      id: (Recorded.valid.first as { id: string }).id,
    });

    const { url, init, headers } = call(fetchMock);
    expect(url).toContain('/api/v1/sites/site%201/imports/preview');
    expect(init.method).toBe('POST');
    expect(headers.Authorization).toBe('Bearer tok');
    expect(Object.keys(headers).map((name) => name.toLowerCase())).not.toContain('content-type');
    const body = init.body as FormData;
    expect(body).toBeInstanceOf(FormData);
    expect(body.get('text')).toBe('a');
    expect(body.get('mapping')).toBe(JSON.stringify({ timezone_confirmed: true }));
    expect(body.get('file')).toBeNull();
    expect(IMPORT_PREVIEW_TIMEOUT_MS).toBe(120_000);
    expect(timeout).toHaveBeenCalledWith(120_000);
  });

  it('uploads a web File as it is, with no text', async () => {
    Platform.OS = 'web';
    const append = jest.spyOn(FormData.prototype, 'append');
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(reply(Recorded.valid.first, 201));
    const file = new File(['x'], 'a.csv');

    await previewImport('s', { kind: 'file', file }, {}, 'tok');

    expect(append).toHaveBeenCalledWith('file', file);
    expect(append.mock.calls.map(([name]) => name)).not.toContain('text');
    expect((call(fetchMock).init.body as FormData).get('mapping')).toBe('{}');
  });

  it('uploads a native file by its URI, name and type, falling back to text/csv', async () => {
    const append = jest.spyOn(FormData.prototype, 'append');
    jest.spyOn(globalThis, 'fetch').mockImplementation(reply(Recorded.valid.first, 201));

    await previewImport('s', { kind: 'file', uri: 'file:///c/a.csv', name: 'a.csv', mimeType: 'text/csv' }, {}, 'tok');
    expect(append).toHaveBeenCalledWith('file', { uri: 'file:///c/a.csv', name: 'a.csv', type: 'text/csv' });

    append.mockClear();
    await previewImport('s', { kind: 'file', uri: 'file:///c/b.csv', name: 'b.csv' }, {}, 'tok');
    expect(append).toHaveBeenCalledWith('file', { uri: 'file:///c/b.csv', name: 'b.csv', type: 'text/csv' });
    expect(append.mock.calls.map(([name]) => name)).not.toContain('text');
  });

  it('reads one import with the default timeout, encoding its ID', async () => {
    const timeout = jest.spyOn(AbortSignal, 'timeout');
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(reply(Recorded.valid.get));

    await expect(getImport('i/1', 'tok')).resolves.toMatchObject({ status: 'committed' });

    expect(call(fetchMock).url).toContain('/api/v1/imports/i%2F1');
    expect(call(fetchMock).headers.Authorization).toBe('Bearer tok');
    expect(timeout).toHaveBeenCalledWith(10_000);
  });

  it('reads the next page of row errors by cursor', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(reply((Recorded.pages as Record<string, unknown>).page));

    await expect(getImportErrors('i', 'c1', 'tok')).resolves.toMatchObject({ next_cursor: null });

    expect(call(fetchMock).url).toContain('/api/v1/imports/i/errors?limit=50&cursor=c1');
  });

  it('commits with the operation key, the acknowledgment as JSON and the commit timeout', async () => {
    const timeout = jest.spyOn(AbortSignal, 'timeout');
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(reply(Recorded.valid.commit));
    const key = 'k'.repeat(22);

    await expect(commitImport('i', true, key, 'tok')).resolves.toMatchObject({ rows_added: 12, replayed: false });

    const { url, init, headers } = call(fetchMock);
    expect(url).toContain('/api/v1/imports/i/commit');
    expect(init.method).toBe('POST');
    expect(init.body).toBe('{"acknowledge_skipped":true}');
    expect(headers['Idempotency-Key']).toBe(key);
    expect(headers['Content-Type']).toBe('application/json');
    expect(IMPORT_COMMIT_TIMEOUT_MS).toBe(60_000);
    expect(timeout).toHaveBeenCalledWith(60_000);
  });

  it.each([
    ['previewImport', () => previewImport('s', { kind: 'paste', text: 'a' }, {}, 'tok')],
    ['getImport', () => getImport('i', 'tok')],
    ['getImportErrors', () => getImportErrors('i', 'c', 'tok')],
    ['commitImport', () => commitImport('i', false, 'k'.repeat(22), 'tok')],
  ])('%s refuses an unexpected body and reports a lost connection', async (_name, send) => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(reply({ secret: 'x' }));
    await expect(send()).rejects.toMatchObject({ code: 'UNEXPECTED_RESPONSE' });

    fetchMock.mockRejectedValue(new TypeError('Network request failed'));
    await expect(send()).rejects.toMatchObject({ code: 'NETWORK_UNREACHABLE' });
  });
});

describe('import draft store', () => {
  const realOS = Platform.OS;
  let storage: Map<string, string>;
  const KEY = 'hematdaya.import-draft.v1';
  const answers = { timezone_confirmed: true, scope: 'disjoint' as const };
  const base = { siteId: 'site-1', answers, intervalText: {}, importId: 'imp-1', intent: { importId: 'imp-1', key: 'k'.repeat(22), acknowledge: false } };

  function useWebStorage(setItem?: (key: string, value: string) => void) {
    Platform.OS = 'web';
    storage = new Map();
    Object.defineProperty(globalThis, 'sessionStorage', {
      configurable: true,
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: setItem ?? ((key: string, value: string) => storage.set(key, value)),
        removeItem: (key: string) => storage.delete(key),
        clear: () => storage.clear(),
      },
    });
  }

  afterEach(() => {
    Platform.OS = realOS;
  });

  it('brings a paste back with its text on the web', () => {
    useWebStorage();

    saveImportDraft({ ...base, source: { kind: 'paste', text: 'timestamp,perangkat,energi_wh\n' } });

    expect(loadImportDraft()).toEqual({
      ...base,
      source: { kind: 'paste', text: 'timestamp,perangkat,energi_wh\n' },
      needsReselect: false,
      textDropped: false,
    });
  });

  it('brings a file back by its name only, to be picked again', () => {
    useWebStorage();

    saveImportDraft({ ...base, source: { kind: 'file', file: new File(['x'], 'contoh-valid.csv') } });

    expect(storage.get(KEY)).not.toContain('"x"');
    expect(loadImportDraft()).toMatchObject({ source: { kind: 'file', name: 'contoh-valid.csv' }, needsReselect: true, textDropped: false });
  });

  it('stores a paste too large for the quota without its text, and says so', () => {
    let calls = 0;
    useWebStorage((key, value) => {
      calls += 1;
      if (calls === 1) {
        throw Object.assign(new Error('full'), { name: 'QuotaExceededError' });
      }
      storage.set(key, value);
    });

    saveImportDraft({ ...base, source: { kind: 'paste', text: 'besar' } });

    expect(storage.get(KEY)).not.toContain('besar');
    expect(loadImportDraft()).toMatchObject({ source: null, textDropped: true, answers, importId: 'imp-1' });
  });

  it('ignores a damaged entry, and clears', () => {
    useWebStorage();
    storage.set(KEY, '{not json');
    expect(loadImportDraft()).toBeNull();

    storage.set(KEY, JSON.stringify({ siteId: 1 }));
    expect(loadImportDraft()).toBeNull();

    saveImportDraft({ ...base, source: null });
    clearImportDraft();
    expect(loadImportDraft()).toBeNull();
  });

  it('keeps nothing on native, and never touches the secure store', () => {
    (SecureStore.setItemAsync as jest.Mock).mockClear();
    (SecureStore.getItemAsync as jest.Mock).mockClear();
    saveImportDraft({ ...base, source: { kind: 'paste', text: 'a' } });

    expect(loadImportDraft()).toBeNull();
    clearImportDraft();
    expect(SecureStore.setItemAsync).not.toHaveBeenCalled();
    expect(SecureStore.getItemAsync).not.toHaveBeenCalled();
  });
});

function SheetHarness({ open, onClose }: { open: boolean; onClose: (reason: string) => void }) {
  const opener = useRef<ComponentRef<typeof View>>(null);
  return (
    <>
      <View ref={opener} testID="opener" />
      <HDSheetDialog open={open} title="Pilih data demo" onClose={onClose} returnFocusTo={opener}>
        <View />
      </HDSheetDialog>
    </>
  );
}

describe('sheet dialog', () => {
  it('closes from its Tutup control and returns focus to the opener', async () => {
    const focusSpy = jest.spyOn(AccessibilityInfo, 'sendAccessibilityEvent').mockImplementation(() => undefined);
    const onClose = jest.fn();
    const view = await render(<SheetHarness open onClose={onClose} />);

    expect(screen.getByRole('heading', { name: 'Pilih data demo' })).toBeOnTheScreen();
    await fireEvent.press(screen.getByRole('button', { name: 'Tutup' }));
    expect(onClose).toHaveBeenCalledWith('close');

    await view.rerender(<SheetHarness open={false} onClose={onClose} />);

    expect(focusSpy).toHaveBeenCalled();
    focusSpy.mockRestore();
  });
});
