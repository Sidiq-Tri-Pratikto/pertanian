import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { FollowForm } from '@/features/subscriptions/FollowForm';
import { FollowConfirmView } from '@/views/subscriptions/FollowConfirmView';
import { FollowManageView } from '@/views/subscriptions/FollowManageView';

vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }), usePathname: () => '/' }));

const fetchMock = vi.fn<typeof fetch>();
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

const INVENTION = '11111111-1111-4111-8111-111111111111';
const FOLLOW = {
  invention_id: INVENTION,
  invention_title: 'ClearSpring',
  email: 'pe***@example.com',
  status: 'PENDING' as const,
  locale: 'id' as const,
  confirmed_at: null,
};

function sent(index = -1) {
  const [url, init] = fetchMock.mock.calls.at(index) as [string, RequestInit];
  return { url, method: init.method, body: JSON.parse(String(init.body)) as Record<string, unknown> };
}

describe('following an invention (spec 053)', () => {
  it('checks the email, then sends the page language and says to check the inbox', async () => {
    fetchMock.mockResolvedValue(json({ status: 'check_email' }, 202));
    const user = userEvent.setup();
    const { container } = render(
      <LocaleProvider locale="en">
        <FollowForm inventionId={INVENTION} />
      </LocaleProvider>,
    );

    await user.type(screen.getByRole('textbox', { name: /Email address/ }), 'not-an-email');
    await user.click(screen.getByRole('button', { name: 'Send confirmation email' }));
    expect(screen.getByText('Enter an email such as name@example.com.')).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    await user.clear(screen.getByRole('textbox', { name: /Email address/ }));
    await user.type(screen.getByRole('textbox', { name: /Email address/ }), 'pengikut@example.com');
    await user.click(screen.getByRole('button', { name: 'Send confirmation email' }));

    expect(await screen.findByText('Check your email')).toBeInTheDocument();
    expect(sent()).toMatchObject({ url: expect.stringContaining('/api/v1/follows'), body: { invention_id: INVENTION, email: 'pengikut@example.com', locale: 'en' } });
    const result = await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false } } });
    expect(result.violations.map((violation) => violation.id)).toEqual([]);
  });

  it('shows the service message when one address asks too often', async () => {
    fetchMock.mockResolvedValue(json({ error: { code: 'RATE_LIMITED', message: 'Terlalu banyak permintaan. Coba lagi dalam 30 menit.', request_id: 'r-1', recovery: { retryable: true } } }, 429));
    const user = userEvent.setup();
    render(<FollowForm inventionId={INVENTION} />);

    await user.type(screen.getByRole('textbox', { name: /Alamat email/ }), 'pengikut@example.com');
    await user.click(screen.getByRole('button', { name: 'Kirim email konfirmasi' }));

    expect(await screen.findByText('Terlalu banyak permintaan. Coba lagi dalam 30 menit.')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Alamat email/ })).toHaveValue('pengikut@example.com');
  });

  it('opening the confirmation link confirms nothing until the button is pressed', async () => {
    fetchMock.mockResolvedValueOnce(json(FOLLOW)).mockResolvedValueOnce(json({ ...FOLLOW, status: 'ACTIVE', manage_token: 'manage-token-0123456789' }));
    const user = userEvent.setup();
    render(<FollowConfirmView token="confirm-token-0123456789" />);

    expect(await screen.findByText('Inovasi: ClearSpring')).toBeInTheDocument();
    expect(sent().url).toContain('/api/v1/follows/preview');
    await user.click(screen.getByRole('button', { name: 'Konfirmasi langganan' }));

    expect(await screen.findByRole('heading', { name: 'Anda mengikuti inovasi ini' })).toBeInTheDocument();
    expect(sent().url).toContain('/api/v1/follows/confirm');
    expect(screen.getByRole('link', { name: 'Kelola langganan' })).toHaveAttribute('href', '/ikuti/atur?token=manage-token-0123456789');
    expect(screen.getByRole('link', { name: 'Kembali ke inovasi' })).toHaveAttribute('href', `/temuan/${INVENTION}`);
  });

  it('a used link says so instead of a button', async () => {
    fetchMock.mockResolvedValue(json({ error: { code: 'NOT_FOUND', message: 'x', request_id: 'r', recovery: { retryable: false } } }, 404));
    render(<FollowConfirmView token="used-token-0123456789" />);

    expect(await screen.findByRole('heading', { name: 'Tautan ini tidak berlaku' })).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('changes the email language and unfollows from the manage link', async () => {
    const active = { ...FOLLOW, status: 'ACTIVE' as const };
    fetchMock
      .mockResolvedValueOnce(json(active))
      .mockResolvedValueOnce(json({ ...active, locale: 'en' }))
      .mockResolvedValueOnce(json({ ...active, locale: 'en', status: 'UNSUBSCRIBED' }));
    const user = userEvent.setup();
    render(<FollowManageView token="manage-token-0123456789" />);

    expect(await screen.findByText('Mengikuti: ClearSpring')).toBeInTheDocument();
    await user.selectOptions(screen.getByRole('combobox', { name: 'Bahasa email' }), 'en');
    await user.click(screen.getByRole('button', { name: 'Simpan bahasa' }));
    expect(await screen.findByText('Bahasa email tersimpan.')).toBeInTheDocument();
    expect(sent()).toMatchObject({ method: 'PUT', body: { token: 'manage-token-0123456789', locale: 'en' } });

    await user.click(screen.getByRole('button', { name: 'Berhenti mengikuti' }));
    expect(await screen.findByRole('heading', { name: 'Langganan dihentikan' })).toBeInTheDocument();
    await waitFor(() => expect(sent().url).toContain('/api/v1/follows/unfollow'));
  });
});
