import { focusManager, onlineManager, QueryClientProvider } from '@tanstack/react-query';
import { act, cleanup, render } from '@testing-library/react-native';
import { Text } from 'react-native';

import type { HistoryResponse } from '@/api/client';
import { createQueryClient } from '@/api/query-client';
import { useHistory } from '@/features/assets/useHistory';
import type { Workspace } from '@/features/workspace/workspace-store';

import { hourlyHistory, mondayWindow, weeklyHistory, weekWindow } from './fixtures/history';

const workspace: Workspace = {
  token: 'test-token', siteId: 'site-a', scenarioId: 'h-base', expiresAt: '2099-01-01T00:00:00Z',
  initialPeriod: { preset: 'this_week', start_date: '2026-10-19', end_date: '2026-10-19' },
};

type Props = {
  open?: boolean;
  site?: Workspace | null;
  assetId?: string;
  confirmed?: HistoryResponse['window'] | null;
};

function Read({ open = true, site = workspace, assetId = 'kulkas', confirmed = weekWindow }: Props) {
  const history = useHistory({ open, workspace: site, assetId, confirmed });
  return <Text>{history.error?.code ?? (history.isFetching && history.failureReason ? 'waiting' : history.status)}</Text>;
}

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status });
}

function failed(attempts: number, retryable = true) {
  return json({
    error: {
      code: 'DATABASE_UNAVAILABLE',
      message: 'Layanan sedang sibuk. Tunggu sebentar.',
      request_id: 'ref-retry',
      recovery: { retryable, retry_after_seconds: 2, max_attempts: attempts },
    },
  }, 503);
}

async function tick(ms = 0) {
  await act(async () => jest.advanceTimersByTimeAsync(ms));
}

describe('the lazy asset history query', () => {
  let client: ReturnType<typeof createQueryClient>;

  beforeEach(() => {
    jest.useFakeTimers();
    focusManager.setFocused(true);
    onlineManager.setOnline(true);
    client = createQueryClient();
  });

  afterEach(async () => {
    await cleanup();
    client.clear();
    focusManager.setFocused(undefined);
    onlineManager.setOnline(true);
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  function tree(props: Props = {}) {
    return <QueryClientProvider client={client}><Read {...props} /></QueryClientProvider>;
  }

  it('waits for an open disclosure, workspace, asset and current confirmed window', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async () => json(weeklyHistory()));
    const view = await render(tree({ open: false }));
    await view.rerender(tree({ site: null }));
    await view.rerender(tree({ assetId: '' }));
    await view.rerender(tree({ confirmed: null }));
    await tick();
    expect(fetchMock).not.toHaveBeenCalled();

    await view.rerender(tree());
    await tick();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('isolates site, asset, dates, timezone and granularity and uses hour for both one-day selections', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
      const search = new URL(String(input)).searchParams;
      const data = search.get('bucket') === 'hour' ? hourlyHistory() : weeklyHistory();
      if ((init?.headers as Record<string, string>).Authorization === 'Bearer utc-token') {
        data.window = { ...data.window, timezone: 'UTC' };
      }
      return json(data);
    });
    const view = await render(tree());
    await tick();
    await view.rerender(tree({ assetId: 'oven' }));
    await tick();
    await view.rerender(tree({ site: { ...workspace, siteId: 'site-b', token: 'site-b-token' } }));
    await tick();
    await view.rerender(tree({ confirmed: mondayWindow }));
    await tick();
    const explicitDay = { ...mondayWindow, start_date: '2026-10-20', end_date: '2026-10-20' };
    await view.rerender(tree({ confirmed: explicitDay }));
    await tick();
    await view.rerender(tree({ site: { ...workspace, token: 'utc-token' }, confirmed: { ...weekWindow, timezone: 'UTC' } }));
    await tick();

    const paths = fetchMock.mock.calls.map(([input]) => new URL(String(input)));
    expect(paths.map((url) => url.pathname.split('/').at(-2))).toEqual(['kulkas', 'oven', 'kulkas', 'kulkas', 'kulkas', 'kulkas']);
    expect(paths.map((url) => url.searchParams.get('bucket'))).toEqual(['day', 'day', 'day', 'hour', 'hour', 'day']);
    expect(paths.map((url) => url.searchParams.get('start_date'))).toEqual([
      '2026-10-19', '2026-10-19', '2026-10-19', '2026-10-19', '2026-10-20', '2026-10-19',
    ]);
    expect(paths.map((url) => url.searchParams.get('end_date'))).toEqual([
      '2026-10-25', '2026-10-25', '2026-10-25', '2026-10-19', '2026-10-20', '2026-10-25',
    ]);
    expect(client.getQueryCache().getAll()).toHaveLength(6);
  });

  it.each([1, 3])('stops at %i total requests, through close, remount and lifecycle triggers', async (attempts) => {
    const fetchMock = jest.spyOn(globalThis, 'fetch').mockImplementation(async () => failed(attempts));
    let view = await render(tree());
    await tick();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    for (let expected = 2; expected <= attempts; expected += 1) {
      await tick(1999);
      expect(fetchMock).toHaveBeenCalledTimes(expected - 1);
      await tick(1);
      expect(fetchMock).toHaveBeenCalledTimes(expected);
    }
    await tick(1);
    expect(view.getByText('DATABASE_UNAVAILABLE')).toBeOnTheScreen();

    await view.rerender(tree({ open: false }));
    await view.rerender(tree());
    await act(async () => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
      onlineManager.setOnline(false);
      onlineManager.setOnline(true);
      await client.invalidateQueries();
    });
    await view.unmount();
    await client.invalidateQueries({ refetchType: 'all' });
    view = await render(tree());
    await tick(10_000);
    expect(view.getByText('DATABASE_UNAVAILABLE')).toBeOnTheScreen();
    expect(fetchMock).toHaveBeenCalledTimes(attempts);
  });

  it('does not retry a refusal and makes a fresh attempt for another confirmed selection', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(failed(3, false)).mockResolvedValueOnce(json(hourlyHistory()));
    const view = await render(tree());
    await tick(10_000);
    expect(view.getByText('DATABASE_UNAVAILABLE')).toBeOnTheScreen();
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await view.rerender(tree({ confirmed: mondayWindow }));
    await tick(1);
    expect(view.getByText('success')).toBeOnTheScreen();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('keeps a single wait when a successful cached read is invalidated during refresh, and can recover', async () => {
    const fetchMock = jest.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(json(weeklyHistory())).mockResolvedValueOnce(failed(3)).mockResolvedValueOnce(json(weeklyHistory()));
    const view = await render(tree());
    await tick(1);
    expect(view.getByText('success')).toBeOnTheScreen();
    const refresh = client.invalidateQueries();
    await tick(1);
    expect(view.getByText('waiting')).toBeOnTheScreen();
    const repeated = client.invalidateQueries();
    await tick(1998);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await tick(2);
    await Promise.all([refresh, repeated]);
    expect(view.getByText('success')).toBeOnTheScreen();
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
