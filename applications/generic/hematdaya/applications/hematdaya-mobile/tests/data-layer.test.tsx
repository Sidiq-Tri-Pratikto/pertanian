import { fireEvent, render, screen } from '@testing-library/react-native';
import * as SecureStore from 'expo-secure-store';
import { useRef, type ComponentRef } from 'react';
import { AccessibilityInfo, Platform, View } from 'react-native';

import { getSummary } from '@/api/client';
import { ApiError } from '@/api/errors';
import { endsSession, retryDelay, shouldRetry } from '@/api/query-client';
import { HDSheetDialog } from '@/components/hd/HDSheetDialog';
import { clearWorkspace, loadWorkspace, saveWorkspace, type Workspace } from '@/features/workspace/workspace-store';

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
