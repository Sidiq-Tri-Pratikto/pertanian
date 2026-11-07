import NetInfo from '@react-native-community/netinfo';
import { focusManager, onlineManager } from '@tanstack/react-query';
import { AppState } from 'react-native';

import { patchAsset } from '@/api/client';
import { ApiError } from '@/api/errors';
import { shouldRetry } from '@/api/query-client';
import { connectivityFromNative, installConnectivity, isKnownOffline } from '@/features/offline/useConnectivity';

afterEach(() => {
  onlineManager.setOnline(true);
  jest.restoreAllMocks();
});

it.each([
  [null, null, 'unknown'],
  [true, null, 'online'],
  [false, null, 'offline'],
  [true, false, 'unknown'],
  [true, true, 'online'],
] as const)('interprets radio %s and reachability %s as %s', (isConnected, isInternetReachable, expected) => {
  expect(connectivityFromNative({ isConnected, isInternetReachable })).toBe(expected);
});

it('guards the actual dispatch when the device disconnects after an earlier UI check', async () => {
  const fetch = jest.spyOn(globalThis, 'fetch');
  expect(isKnownOffline()).toBe(false);
  onlineManager.setOnline(false);
  await expect(patchAsset('asset', { name: 'Draft' }, 'token')).rejects.toMatchObject({ code: 'OFFLINE_UNSENT' });
  expect(fetch).not.toHaveBeenCalled();
});

it('counts the original query attempt and does not retry a terminal error', () => {
  expect(shouldRetry(0, ApiError.unreachable())).toBe(true);
  expect(shouldRetry(1, ApiError.unreachable())).toBe(true);
  expect(shouldRetry(2, ApiError.unreachable())).toBe(false);
  expect(shouldRetry(0, ApiError.unexpected())).toBe(false);
});

it('feeds native reachability into query online state and native foreground into focus', () => {
  const listener = jest.spyOn(AppState, 'addEventListener');
  const stop = installConnectivity();
  const changeLink = jest.mocked(NetInfo.addEventListener).mock.calls.at(-1)![0];
  const changeApp = listener.mock.calls.at(-1)![1];
  changeLink({ isConnected: false, isInternetReachable: false } as Parameters<typeof changeLink>[0]);
  expect(onlineManager.isOnline()).toBe(false);
  changeLink({ isConnected: true, isInternetReachable: false } as Parameters<typeof changeLink>[0]);
  expect(onlineManager.isOnline()).toBe(true);
  changeApp('background');
  expect(focusManager.isFocused()).toBe(false);
  changeApp('active');
  expect(focusManager.isFocused()).toBe(true);
  expect(NetInfo.refresh).toHaveBeenCalled();
  stop();
});
