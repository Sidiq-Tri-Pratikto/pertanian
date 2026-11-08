import { focusManager, onlineManager, useQueryClient } from '@tanstack/react-query';
import { act, renderHook, waitFor } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { attestedResponse, seedConfirmedWorkspace } from './fixtures/workspaces';

import type { AssetDetail } from '@/api/client';
import { useAssetMutations } from '@/features/assets/useAssetMutations';
import { useAsset } from '@/features/assets/useAssets';
import { WorkspaceProvider, useWorkspace } from '@/features/workspace/WorkspaceProvider';

const original: AssetDetail = {
  id: 'df5eb61e-f5ea-43a6-93b2-07dc913394df', name: 'Kulkas', category: null, location: 'Dapur',
  scope_kind: 'device', parent_asset_id: null, expected_use: 'unknown', archived: false, bindings: [], sources: [],
};
const renamed = { ...original, name: 'Kulkas baru' };
const workspace = {
  siteId: 'site', token: 'first-token', scenarioId: 'h-base', expiresAt: '2099-01-01T00:00:00Z',
  initialPeriod: { preset: 'last_7_days', start_date: '2026-10-19', end_date: '2026-10-25' },
};

function response(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

function failure(status: number, code: string, recovery = {}) {
  return response({ error: {
    code, message: 'Permintaan belum selesai. Periksa kembali.', request_id: 'ref-test',
    recovery: { retryable: false, ...recovery },
  } }, status);
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((accept, refuse) => { resolve = accept; reject = refuse; });
  return { resolve, reject, promise };
}

function fetchAssets(patch: () => Promise<Response>, get = () => Promise.resolve(response(original))) {
  const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) =>
    init?.method === 'PATCH' ? patch() : get());
  return {
    fetchMock,
    patches: () => fetchMock.mock.calls.filter(([, init]) => init?.method === 'PATCH'),
    reads: () => fetchMock.mock.calls.filter(([url, init]) => init?.method === 'GET' && /\/assets\//.test(String(url))),
  };
}

async function open() {
  await seedConfirmedWorkspace(workspace);
  const hook = await renderHook(({ assetId }: { assetId: string }) => ({
    editor: useAssetMutations(assetId), detail: useAsset(assetId),
    session: useWorkspace(), client: useQueryClient(),
  }), { wrapper: WorkspaceProvider, initialProps: { assetId: original.id } });
  await waitFor(() => expect(hook.result.current.detail.data).toEqual(original));
  return hook;
}

afterEach(() => {
  jest.restoreAllMocks();
  jest.useRealTimers();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

it('guards duplicate sends and publishes acknowledged metadata over older in-flight detail', async () => {
  const patch = deferred<Response>();
  const oldRead = deferred<Response>();
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original)).mockImplementation(() => oldRead.promise);
  const api = fetchAssets(() => patch.promise, get);
  const { result } = await open();
  await act(() => {
    void result.current.detail.refetch();
    void result.current.editor.submit({ name: renamed.name });
    void result.current.editor.submit({ name: 'Tertimpa' });
  });
  expect(result.current.detail.data?.name).toBe(original.name);
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('saving'));
  expect(api.patches()).toHaveLength(1);
  expect(api.patches()[0][1]?.body).toBe(JSON.stringify({ name: renamed.name }));
  await act(() => patch.resolve(response(renamed)));
  await waitFor(() => expect(result.current.detail.data?.name).toBe(renamed.name));
  await act(() => oldRead.resolve(response(original)));
  expect(result.current.detail.data?.name).toBe(renamed.name);
  expect(result.current.editor.state?.kind).toBe('acknowledged');
});

it('does not read or change confirmed data after a known pre-write refusal', async () => {
  const api = fetchAssets(async () => failure(422, 'VALIDATION_FAILED'));
  const { result } = await open();
  await act(async () => { await result.current.editor.submit({ name: renamed.name }); });
  expect(result.current.detail.data?.name).toBe(original.name);
  await waitFor(() => expect(result.current.editor.state).toMatchObject({ kind: 'refused', error: { requestId: 'ref-test' } }));
  expect(api.reads()).toHaveLength(1);
  expect(api.patches()).toHaveLength(1);
});

it.each([
  { returned: renamed, expected: 'observed' },
  { returned: { ...original, name: 'Ubah bersamaan', location: 'Garasi' }, expected: 'diverged' },
  { returned: original, expected: 'diverged' },
])('reconciles a lost response as $expected without a second write', async ({ returned, expected }) => {
  const patch = deferred<Response>();
  const read = deferred<Response>();
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original)).mockImplementation(() => read.promise);
  const api = fetchAssets(() => patch.promise, get);
  const { result } = await open();
  await act(() => { void result.current.editor.submit({ name: renamed.name }); });
  await act(() => patch.reject(new Error('response lost')));
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('checking'));
  expect(result.current.detail.data?.name).toBe(original.name);
  await act(() => read.resolve(response(returned)));
  await waitFor(() => expect(result.current.editor.state?.kind).toBe(expected));
  expect(result.current.detail.data?.name).toBe(returned.name);
  if (expected === 'diverged') await act(async () => { await result.current.editor.submit({ name: renamed.name }); });
  expect(api.patches()).toHaveLength(1);
  expect(api.reads()).toHaveLength(2);
});

it.each([1, 3])('spends at most %i reconciliation attempts including the first across lifecycle triggers', async (maxAttempts) => {
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original)).mockImplementation(async () =>
    failure(503, 'DATABASE_UNAVAILABLE', { retryable: true, retry_after_seconds: 2, max_attempts: maxAttempts }));
  const api = fetchAssets(async () => new Response(null, { status: 204 }), get);
  const { result } = await open();
  jest.useFakeTimers();
  await act(() => { void result.current.editor.submit({ name: renamed.name }); });
  expect(api.reads()).toHaveLength(2);
  for (let attempt = 1; attempt < maxAttempts; attempt += 1) {
    await act(async () => { await jest.advanceTimersByTimeAsync(1999); });
    expect(api.reads()).toHaveLength(attempt + 1);
    await act(async () => { await jest.advanceTimersByTimeAsync(1); });
    expect(api.reads()).toHaveLength(attempt + 2);
  }
  await waitFor(() => expect(result.current.editor.state).toMatchObject({ kind: 'unresolved', readError: { requestId: 'ref-test' } }));
  await act(async () => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
    onlineManager.setOnline(false);
    onlineManager.setOnline(true);
    await result.current.editor.submit({ name: renamed.name });
    await jest.advanceTimersByTimeAsync(6000);
  });
  expect(api.reads()).toHaveLength(maxAttempts + 1);
  expect(api.patches()).toHaveLength(1);
  expect(result.current.detail.data?.name).toBe(original.name);
});

it('never dispatches a paused write when already offline or on reconnect', async () => {
  const api = fetchAssets(async () => response(renamed));
  const { result } = await open();
  await act(async () => {
    onlineManager.setOnline(false);
    await result.current.editor.submit({ name: renamed.name });
  });
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('offline'));
  await act(() => onlineManager.setOnline(true));
  expect(api.patches()).toHaveLength(0);
});

it('ignores a failed acknowledgment and session effect from a replaced credential of the same site', async () => {
  const patch = deferred<Response>();
  const api = fetchAssets(() => patch.promise);
  const { result } = await open();
  await act(() => { void result.current.editor.submit({ name: renamed.name }); });
  const replacement = { ...workspace, token: 'replacement-token' };
  await act(async () => { await result.current.session.open(replacement, attestedResponse(replacement)); });
  await act(() => patch.resolve(failure(401, 'SESSION_EXPIRED')));
  expect(result.current.session.workspace?.token).toBe('replacement-token');
  expect(result.current.editor.state).toBeUndefined();
  expect(result.current.detail.data?.name).not.toBe(renamed.name);
  expect(api.patches()).toHaveLength(1);
});

it('keeps an invalid reconciliation response unresolved without treating it as the asset', async () => {
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original))
    .mockImplementation(async () => response({ ...renamed, id: 'unexpected-id' }));
  const api = fetchAssets(async () => response({ ...original, name: 'not-the-submitted-name' }), get);
  const { result } = await open();
  await act(async () => { await result.current.editor.submit({ name: renamed.name }); });
  await waitFor(() => expect(result.current.editor.state).toMatchObject({
    kind: 'unresolved', readError: { code: 'UNEXPECTED_RESPONSE' },
  }));
  expect(result.current.detail.data?.name).toBe(original.name);
  expect(api.patches()).toHaveLength(1);
  expect(api.reads()).toHaveLength(2);
});

it('does not apply a finished write to another active asset route', async () => {
  const patch = deferred<Response>();
  const other = { ...original, id: '8a2fea00-bb2e-4b7d-b5e8-1ebaf9ded841', name: 'Router' };
  jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    if (init?.method === 'PATCH') return patch.promise;
    return response(String(input).endsWith(other.id) ? other : original);
  });
  const { result, rerender } = await open();
  await act(() => { void result.current.editor.submit({ name: renamed.name }); });
  await rerender({ assetId: other.id });
  await act(() => patch.resolve(response(renamed)));
  await waitFor(() => expect(result.current.detail.data?.name).toBe(other.name));
  expect(result.current.editor.state).toBeUndefined();
});

it('blocks replacement and old dispatch when durable revocation fails', async () => {
  const api = fetchAssets(async () => response(renamed));
  const { result } = await open();
  const oldSubmit = result.current.editor.submit;
  jest.spyOn(SecureStore, 'setItemAsync').mockRejectedValueOnce(new Error('storage unavailable'));
  await act(async () => {
    await expect(result.current.session.open({ ...workspace, token: 'replacement-token' })).rejects.toMatchObject({ code: 'LOCAL_STORAGE' });
  });
  await act(async () => { await oldSubmit({ name: renamed.name }); });
  expect(result.current.session.workspace).toBeNull();
  expect(result.current.session.storageError).toBe(true);
  expect(api.patches()).toHaveLength(0);
});

it.each([true, false])('observes a lost archive acknowledgment with archived=%s without replaying the change', async (archived) => {
  const observed = { ...original, archived };
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original)).mockResolvedValueOnce(response(observed));
  const api = fetchAssets(async () => { throw new Error('lost response'); }, get);
  const { result } = await open();
  await act(async () => { await result.current.editor.submit({ archived: true }); });
  await waitFor(() => expect(result.current.editor.state?.kind).toBe(archived ? 'observed' : 'diverged'));
  expect(result.current.detail.data?.archived).toBe(archived);
  expect(api.patches().map(([, init]) => init?.body)).toEqual([JSON.stringify({ archived: true })]);
  expect(api.reads()).toHaveLength(2);
});

it('requires an owned read for a restored draft and sends no PATCH when the edits are already present', async () => {
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original)).mockResolvedValueOnce(response(renamed));
  const api = fetchAssets(async () => response(renamed), get);
  const { result } = await open();
  await act(() => result.current.editor.reconcileDraft({ name: renamed.name }, {
    name: original.name, category: original.category ?? '', location: original.location ?? '',
  }));
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('observed'));
  expect(api.reads()).toHaveLength(2);
  expect(api.patches()).toHaveLength(0);
});

it('requires review of a divergent restored draft before a separate explicit write', async () => {
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original))
    .mockResolvedValueOnce(response({ ...original, name: 'Latest service name' }));
  const api = fetchAssets(async () => response(renamed), get);
  const { result } = await open();
  const changes = { name: renamed.name };
  await act(() => result.current.editor.reconcileDraft(changes, {
    name: original.name, category: original.category ?? '', location: original.location ?? '',
  }));
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('draft-review'));
  await act(() => result.current.editor.submit(changes));
  expect(api.patches()).toHaveLength(0);
  await act(() => result.current.editor.review());
  expect(api.patches()).toHaveLength(0);
  await act(() => result.current.editor.submit(changes));
  expect(api.patches()).toHaveLength(1);
});

it('manually observes an unresolved dispatched write without replaying PATCH', async () => {
  const get = jest.fn<Promise<Response>, []>().mockResolvedValueOnce(response(original))
    .mockResolvedValueOnce(failure(500, 'INTERNAL_ERROR'))
    .mockResolvedValueOnce(response(renamed));
  const api = fetchAssets(async () => { throw new TypeError('Response was lost'); }, get);
  const { result } = await open();
  await act(() => result.current.editor.submit({ name: renamed.name }));
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('unresolved'));
  await act(() => result.current.editor.checkOutcome());
  await waitFor(() => expect(result.current.editor.state?.kind).toBe('observed'));
  expect(api.patches()).toHaveLength(1);
});
