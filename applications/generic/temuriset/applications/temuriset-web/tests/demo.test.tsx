import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ContextBar } from '@/features/ContextBar';
import { DemoPanel, type DemoAccount } from '@/features/demo/DemoPanel';

import { makeMe } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

let replies: { status: number; body?: unknown }[] = [];
const fetchMock = vi.fn(async () => {
  const reply = replies.shift() ?? { status: 500, body: {} };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

beforeEach(() => {
  replies = [];
  fetchMock.mockClear();
  router.push.mockClear();
  vi.stubGlobal('fetch', fetchMock);
  HTMLDialogElement.prototype.showModal ??= function showModal(this: HTMLDialogElement) {
    this.open = true;
  };
  HTMLDialogElement.prototype.close ??= function close(this: HTMLDialogElement) {
    this.open = false;
  };
});

afterEach(() => vi.unstubAllGlobals());

const ACCOUNTS: DemoAccount[] = [
  { key: 'rani', name: 'Rani', persona: 'inovator', fixture: 'F01', label: 'Akun demo · data fiktif' },
  { key: 'mitra-a', name: 'Peserta P', persona: 'mitra', fixture: 'Recipient A', label: 'Akun demo · data fiktif' },
];

describe('demo picker (spec 021)', () => {
  it('lists labelled accounts and signs a partner in to Jelajahi', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: {} }];
    render(<DemoPanel accounts={ACCOUNTS} />);

    expect(screen.getByText('F01 · Akun demo · data fiktif')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Masuk sebagai Peserta P' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/discover'));
    const [path, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect([path, init.body]).toEqual(['/api/v1/demo/sign-in', JSON.stringify({ key: 'mitra-a' })]);
  });

  it('resets only after confirmation and says real accounts are untouched', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: { accounts: 10, inventions: 6 } }];
    render(<DemoPanel accounts={ACCOUNTS} />);

    await user.click(screen.getByRole('button', { name: 'Atur ulang demo' }));
    expect(fetchMock).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: 'Atur ulang' }));

    expect(await screen.findByText('Demo sudah diatur ulang. Akun nyata tidak berubah.')).toBeInTheDocument();
    expect((fetchMock.mock.calls[0] as unknown as [string])[0]).toBe('/api/v1/demo/reset');
  });

  it('keeps the picker and says why when signing in fails', async () => {
    const user = userEvent.setup();
    replies = [{ status: 404, body: { error: { code: 'NOT_FOUND', message: 'Data yang diminta tidak ditemukan.', request_id: 'ref_1', recovery: { retryable: false } } } }];
    render(<DemoPanel accounts={ACCOUNTS} />);

    await user.click(screen.getByRole('button', { name: 'Masuk sebagai Rani' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Data yang diminta tidak ditemukan.');
    expect(router.push).not.toHaveBeenCalled();
  });

  it('labels every screen of a demo account in the bar', () => {
    const me = makeMe();
    render(<ContextBar me={{ ...me, account: { ...me.account, kind: 'demo' } }} />);

    expect(screen.getByText('Demo · Data fiktif')).toBeInTheDocument();
  });
});
