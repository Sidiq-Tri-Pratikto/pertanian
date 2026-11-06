import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import axe from 'axe-core';

import { ApiError } from '@/api/errors';
import type { Me } from '@/api/client';

import { makeMe } from './fixtures';

const { send, refresh } = vi.hoisted(() => ({ send: vi.fn(), refresh: vi.fn() }));
let status: 'available' | 'planned' | null = null;

vi.mock('@/api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/client')>()),
  send,
}));
vi.mock('next/navigation', () => ({ useRouter: () => ({ refresh }) }));
vi.mock('@/features/session', () => ({ requireMe: async () => makeMe() }));
vi.mock('@/api/server', () => ({
  serverGet: async (path: string) => {
    if (path === '/api/v1/capabilities') {
      if (status === null) throw ApiError.unreachable();
      return { capabilities: [{ id: 'core' }], adapters: [{ id: 'email', status }] };
    }
    if (path === '/api/v1/profiles/me') return null;
    return [];
  },
}));

const SettingsPage = (await import('@/app/settings/page')).default;
const label = 'Pemberitahuan lewat email';

async function openSettings() {
  const rendered = render(await SettingsPage({ searchParams: Promise.resolve({}) }));
  fireEvent.click(screen.getByText('Ubah akun'));
  return rendered;
}

beforeEach(() => {
  status = null;
  send.mockReset();
  refresh.mockReset();
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
});

afterEach(() => vi.unstubAllGlobals());

it.each(['planned', null] as const)('hides optional email when the manifest is %s', async (adapterStatus) => {
  status = adapterStatus;
  await openSettings();
  expect(screen.queryByRole('checkbox', { name: label })).not.toBeInTheDocument();
  const account = makeMe();
  send.mockResolvedValue({ ...account, account: { ...account.account, version: 2 } });
  fireEvent.click(screen.getByRole('button', { name: 'Simpan akun' }));
  await screen.findByText('Akun tersimpan');
  expect(send).toHaveBeenCalledWith('PATCH', '/api/v1/me', expect.not.objectContaining({ email_notifications: expect.anything() }));
});

it('renders an accessible, unchecked preference and saves subsequent changes against the returned version', async () => {
  status = 'available';
  const { container } = await openSettings();
  const checkbox = screen.getByRole('checkbox', { name: label });
  expect(checkbox).not.toBeChecked();
  expect(checkbox).toHaveAccessibleDescription('Dapatkan pemberitahuan umum tentang aktivitas pitching. Kode masuk dan undangan tetap dikirim terpisah.');
  let violations: axe.Result[] = [];
  await act(async () => {
    const result = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } },
    });
    violations = result.violations;
  });
  expect(violations).toEqual([]);

  const me = makeMe();
  let finish: (me: Me) => void = () => {};
  send.mockReturnValueOnce(new Promise<Me>((resolve) => { finish = resolve; }));
  fireEvent.click(checkbox);
  fireEvent.click(screen.getByRole('button', { name: 'Simpan akun' }));
  expect(screen.getByRole('button', { name: 'Menyimpan…' })).toHaveAttribute('aria-busy', 'true');
  expect(checkbox).toBeDisabled();
  expect(send).toHaveBeenLastCalledWith('PATCH', '/api/v1/me', expect.objectContaining({ email_notifications: true, expected_version: 1 }));

  await act(async () => finish({ ...me, account: { ...me.account, email_notifications: true, version: 2 } }));
  expect(screen.getByText('Akun tersimpan')).toBeInTheDocument();
  expect(refresh).toHaveBeenCalledOnce();

  send.mockResolvedValueOnce({ ...me, account: { ...me.account, email_notifications: false, version: 3 } });
  fireEvent.click(checkbox);
  fireEvent.click(screen.getByRole('button', { name: 'Simpan akun' }));
  await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2));
  expect(send).toHaveBeenLastCalledWith('PATCH', '/api/v1/me', expect.objectContaining({ email_notifications: false, expected_version: 2 }));
});

it('focuses the stale-save error, retains the edit, and does not retry automatically', async () => {
  status = 'available';
  await openSettings();
  send.mockRejectedValueOnce(new ApiError('STALE_VERSION', 'Muat ulang versi akun lalu ulangi perubahan.', { retryable: false }, 'ref_fixture'));
  const checkbox = screen.getByRole('checkbox', { name: label });
  fireEvent.click(checkbox);
  fireEvent.click(screen.getByRole('button', { name: 'Simpan akun' }));
  const error = await screen.findByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
  expect(error).toHaveFocus();
  expect(error).toHaveTextContent('Muat ulang versi akun lalu ulangi perubahan.');
  expect(error).toHaveTextContent('ref_fixture');
  expect(checkbox).toBeChecked();
  expect(send).toHaveBeenCalledOnce();
  expect(refresh).not.toHaveBeenCalled();
});
