import AsyncStorage from '@react-native-async-storage/async-storage';
import { act, renderHook, waitFor } from '@testing-library/react-native';
import { onlineManager } from '@tanstack/react-query';
import * as SecureStore from 'expo-secure-store';

import { getAsset } from '@/api/client';
import { ownerStorageKey } from '@/features/offline/owner-storage';
import { WorkspaceProvider, useWorkspace } from '@/features/workspace/WorkspaceProvider';

import { attestedResponse, seedConfirmedWorkspace } from './fixtures/workspaces';
import {
  attestWorkspace, clearWorkspace, loadWorkspaceRecord, revokeWorkspace, saveWorkspace,
  type Workspace,
} from '@/features/workspace/workspace-store';

const siteId = '00000000-0000-0000-0000-000000000034';
const workspace: Workspace = {
  token: 'demo-test', siteId, scenarioId: 'h-base',
  expiresAt: '2099-01-01T00:00:00Z',
  initialPeriod: { preset: 'today', start_date: '2026-10-25', end_date: '2026-10-25' },
};

it('recognizes legacy credentials without authorizing a cached namespace', async () => {
  await saveWorkspace(workspace);
  await expect(loadWorkspaceRecord()).resolves.toEqual({ workspace, kind: 'legacy' });
});

it('binds the durable epoch to the exact credential even for a replacement on the same site', async () => {
  const record = await attestWorkspace(workspace);
  await saveWorkspace(workspace, record);
  await expect(loadWorkspaceRecord()).resolves.toEqual({ workspace, kind: 'confirmed', attestation: record });
  await saveWorkspace({ ...workspace, token: 'replacement' }, record);
  await expect(loadWorkspaceRecord()).resolves.toBeNull();
});

it.each(['not a timestamp', '2000-01-01T00:00:00Z'])('cannot attest an invalid or expired expiry %s', async (expiresAt) => {
  await expect(attestWorkspace({ ...workspace, expiresAt })).rejects.toMatchObject({ code: 'SESSION_EXPIRED' });
});

it('keeps an ambiguous reset credential fenced after an app restart', async () => {
  const record = await attestWorkspace(workspace);
  await saveWorkspace(workspace, record);
  await revokeWorkspace(workspace);
  await expect(loadWorkspaceRecord()).resolves.toEqual({ workspace, kind: 'revoked' });
  expect(await SecureStore.getItemAsync('hematdaya.workspace.v1')).not.toContain(record.epoch);
  await clearWorkspace();
  await expect(loadWorkspaceRecord()).resolves.toBeNull();
});

it('rejects a rewritten epoch or legacy-migration entitlement', async () => {
  const record = await attestWorkspace(workspace);
  await saveWorkspace(workspace, { ...record, epoch: 'a'.repeat(22) });
  await expect(loadWorkspaceRecord()).resolves.toBeNull();
  await saveWorkspace(workspace, { ...record, legacyImport: true });
  await expect(loadWorkspaceRecord()).resolves.toBeNull();
});

function answer(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

const site = { id: siteId, kind: 'demo', timezone: 'Asia/Jakarta', name: 'Fixture' };

afterEach(() => {
  jest.restoreAllMocks();
  onlineManager.setOnline(true);
});

it('keeps a legacy record out of the read path until an owned site response arrives', async () => {
  await saveWorkspace(workspace);
  onlineManager.setOnline(false);
  let complete!: (response: Response) => void;
  const fetch = jest.spyOn(globalThis, 'fetch').mockImplementation(() =>
    new Promise((resolve) => { complete = resolve; }));
  const hook = await renderHook(useWorkspace, { wrapper: WorkspaceProvider });
  await waitFor(() => expect(hook.result.current.status).toBe('ready'));
  expect(hook.result.current.storage).toBeNull();
  expect(fetch).not.toHaveBeenCalled();
  await act(() => onlineManager.setOnline(true));
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  expect(hook.result.current.workspace).toBeNull();
  await act(() => complete(answer(site)));
  await waitFor(() => expect(hook.result.current.storage).not.toBeNull());
  expect(hook.result.current.legacyImport).toBe(true);
});

it('cannot terminate a same-site replacement when the old request returns a late 401', async () => {
  await seedConfirmedWorkspace(workspace);
  let reject!: (response: Response) => void;
  jest.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise((resolve) => { reject = resolve; }));
  const hook = await renderHook(useWorkspace, { wrapper: WorkspaceProvider });
  await waitFor(() => expect(hook.result.current.credential).not.toBeNull());
  const old = hook.result.current.credential!;
  const pending = getAsset('old-asset', old).catch((error: unknown) => error);
  const replacement = { ...workspace, token: 'replacement-credential' };
  await act(() => hook.result.current.open(replacement, attestedResponse(replacement)));
  expect(old.signal.aborted).toBe(true);
  await act(() => reject(answer({
    error: { code: 'UNAUTHORIZED', message: 'Sesi berakhir. Buka sesi baru.', request_id: 'ref-401',
      recovery: { retryable: false } },
  }, 401)));
  await expect(pending).resolves.toMatchObject({ code: 'WORKSPACE_CHANGED' });
  expect(hook.result.current.workspace?.token).toBe(replacement.token);
  expect(hook.result.current.ended).toBeNull();
});

it('durably revokes the previous epoch before the real reset request and activates a fresh epoch', async () => {
  const prior = await seedConfirmedWorkspace(workspace);
  await AsyncStorage.setItem(ownerStorageKey(prior.epoch, 'asset-drafts'), 'old draft');
  const fetch = jest.spyOn(globalThis, 'fetch').mockImplementation(async () => {
    expect(await loadWorkspaceRecord()).toEqual({ kind: 'revoked', workspace });
    return answer({
      site_id: siteId, scenario_id: workspace.scenarioId, expires_at: workspace.expiresAt,
      initial_period: workspace.initialPeriod,
    });
  });
  const hook = await renderHook(useWorkspace, { wrapper: WorkspaceProvider });
  await waitFor(() => expect(hook.result.current.storage?.epoch).toBe(prior.epoch));
  await act(() => hook.result.current.resetDemo());
  expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/\/demo\/sessions\/current\/reset$/), expect.objectContaining({
    method: 'POST', headers: { Authorization: 'Bearer demo-test' },
  }));
  expect(hook.result.current.workspace?.token).toBe(workspace.token);
  expect(hook.result.current.storage?.epoch).not.toBe(prior.epoch);
  await expect(AsyncStorage.getItem(ownerStorageKey(prior.epoch, 'asset-drafts'))).resolves.toBeNull();
});

it('serializes an old in-flight durable write before owner cleanup', async () => {
  const prior = await seedConfirmedWorkspace(workspace);
  const hook = await renderHook(useWorkspace, { wrapper: WorkspaceProvider });
  await waitFor(() => expect(hook.result.current.storage?.epoch).toBe(prior.epoch));
  const active = hook.result.current.storage!;
  const setItem = AsyncStorage.setItem;
  let finish!: () => void;
  jest.spyOn(AsyncStorage, 'setItem').mockImplementationOnce((key, value) =>
    new Promise((resolve) => { finish = () => { void setItem(key, value).then(resolve); }; }));
  const writing = active.write('asset-drafts', 'old draft');
  await waitFor(() => expect(finish).toBeDefined());
  await act(async () => {
    const logout = hook.result.current.end(null);
    finish();
    await logout;
  });
  await expect(writing).resolves.toBe(false);
  await expect(active.read('asset-drafts')).resolves.toBeNull();
  await expect(AsyncStorage.getItem(ownerStorageKey(prior.epoch, 'asset-drafts'))).resolves.toBeNull();
});

it('keeps a logout terminal even when deleting the credential-control key fails', async () => {
  await seedConfirmedWorkspace(workspace);
  const hook = await renderHook(useWorkspace, { wrapper: WorkspaceProvider });
  await waitFor(() => expect(hook.result.current.credential).not.toBeNull());
  jest.spyOn(SecureStore, 'deleteItemAsync').mockRejectedValueOnce(new Error('write protected'));
  await act(() => hook.result.current.end(null));
  expect(hook.result.current.workspace).toBeNull();
  expect(hook.result.current.storageError).toBe(true);
  await expect(loadWorkspaceRecord()).resolves.toBeNull();
  expect(await SecureStore.getItemAsync('hematdaya.workspace.v1')).not.toContain(workspace.token);
});
