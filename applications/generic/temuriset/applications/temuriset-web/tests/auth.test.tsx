import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ContextSwitcher } from '@/components/tr/ContextSwitcher';
import { SummaryList } from '@/components/tr/SummaryList';
import { AcceptInvitationButton, AccountForm, CreateOrganizationForm, InviteForm, RevokeButton, SignOutButton } from '@/features/AccountForms';
import { ContextBar } from '@/features/ContextBar';
import { savePending } from '@/features/signIn';
import { CodeView } from '@/views/CodeView';
import { StartView } from '@/views/StartView';

import { makeMe, ORGANIZATION, ORGANIZATION_PARTY, PERSONAL } from './fixtures';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));
const forgetPersona = vi.fn(async () => {});
vi.mock('@/features/actions', () => ({ forgetPersona: () => forgetPersona() }));

type Reply = { status: number; body?: unknown };
let replies: Reply[] = [];
const fetchMock = vi.fn(async () => {
  const reply = replies.shift() ?? { status: 204 };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

function failure(code: string, message: string, extra: Record<string, unknown> = {}, recovery: Record<string, unknown> = { retryable: false }) {
  return { error: { code, message, request_id: 'ref_1', recovery, ...extra } };
}

function sent(index = 0) {
  const [path, init] = fetchMock.mock.calls[index] as unknown as [string, RequestInit];
  return { path, method: init.method, headers: init.headers as Record<string, string>, body: init.body ? JSON.parse(String(init.body)) : undefined };
}

beforeEach(() => {
  replies = [];
  fetchMock.mockClear();
  Object.values(router).forEach((mock) => mock.mockClear());
  forgetPersona.mockClear();
  sessionStorage.clear();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('sign-up (S01)', () => {
  it('lists every missing field in a focused summary and sends nothing', async () => {
    const user = userEvent.setup();
    render(<StartView persona={null} mode="sign_up" returnTo={null} />);

    await user.click(screen.getByRole('button', { name: 'Kirim kode' }));

    const summary = screen.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    expect(summary).toHaveFocus();
    expect(summary).toHaveTextContent('Pilih cara Anda memakai TemuRiset.');
    expect(summary).toHaveTextContent('Isi nama tampilan.');
    expect(summary).toHaveTextContent('Isi email dengan format nama@contoh.com.');
    expect(screen.getByRole('textbox', { name: /Email/ })).toHaveAttribute('aria-invalid', 'true');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('sends the code request with the profile and opens the code screen, keeping the email out of the address', async () => {
    const user = userEvent.setup();
    replies = [{ status: 202, body: { sent: true } }];
    render(<StartView persona="inovator" mode="sign_up" returnTo="/settings" />);

    await user.type(screen.getByRole('textbox', { name: /Nama tampilan/ }), 'Rani');
    await user.type(screen.getByRole('textbox', { name: /Email/ }), 'rani@example.com');
    await user.selectOptions(screen.getByRole('combobox', { name: /Zona waktu/ }), 'Asia/Makassar');
    await user.click(screen.getByRole('button', { name: 'Kirim kode' }));

    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/start/kode'));
    expect(sent().body).toEqual({
      email: 'rani@example.com',
      purpose: 'sign_up',
      display_name: 'Rani',
      locale: 'id',
      time_zone: 'Asia/Makassar',
      persona: 'inovator',
    });
    expect(JSON.parse(sessionStorage.getItem('tr_masuk') ?? '{}')).toMatchObject({ email: 'rani@example.com', returnTo: '/settings' });
  });

  it('explains a rate limit with the wait and keeps what was typed', async () => {
    const user = userEvent.setup();
    replies = [{ status: 429, body: failure('RATE_LIMITED', 'Terlalu banyak permintaan kode. Tunggu sebentar lalu coba lagi.', {}, { retryable: true, retry_after_seconds: 600 }) }];
    render(<StartView persona={null} mode="sign_in" returnTo={null} />);

    await user.type(screen.getByRole('textbox', { name: /Email/ }), 'rani@example.com');
    await user.click(screen.getByRole('button', { name: 'Kirim kode' }));

    expect(await screen.findByText(/Coba lagi dalam 10 menit\./)).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Email/ })).toHaveValue('rani@example.com');
    expect(sent().body).toMatchObject({ email: 'rani@example.com', purpose: 'sign_in' });
  });
});

describe('the code screen', () => {
  beforeEach(() => {
    savePending({ email: 'rani@example.com', purpose: 'sign_up', display_name: 'Rani', locale: 'id', time_zone: 'Asia/Jakarta', persona: 'mitra', returnTo: null });
  });

  it('says where the code went', () => {
    render(<CodeView />);

    expect(screen.getByText(/Kami mengirim kode enam angka ke rani@example.com/)).toBeInTheDocument();
  });

  it('focuses the summary on a wrong code, states the attempts left and keeps the code typed (UX-09)', async () => {
    const user = userEvent.setup();
    replies = [{ status: 422, body: failure('CODE_INVALID', 'Kode verifikasi tidak cocok.', { attempts_left: 3 }) }];
    render(<CodeView />);

    await user.type(screen.getByRole('textbox', { name: /Kode verifikasi/ }), '123456');
    await user.click(screen.getByRole('button', { name: 'Masuk' }));

    const summary = await screen.findByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    expect(summary).toHaveFocus();
    expect(screen.getByRole('link', { name: 'Kode tidak cocok. Sisa percobaan: 3.' })).toHaveAttribute('href', '#kode');
    expect(screen.getByRole('textbox', { name: /Kode verifikasi/ })).toHaveValue('123456');
  });

  it('offers a new code when the code is used up, and resends it', async () => {
    const user = userEvent.setup();
    replies = [
      { status: 422, body: failure('CODE_EXPIRED', 'Kode verifikasi sudah tidak berlaku. Minta kode baru lalu masukkan kode tersebut.') },
      { status: 202, body: { sent: true } },
    ];
    render(<CodeView />);

    await user.type(screen.getByRole('textbox', { name: /Kode verifikasi/ }), '123456');
    await user.click(screen.getByRole('button', { name: 'Masuk' }));
    const summary = await screen.findByRole('group', { name: 'Masih ada yang perlu diperbaiki' });
    expect(summary).toHaveTextContent('Minta kode baru');
    await user.click(within(summary).getByRole('button', { name: 'Kirim ulang kode' }));

    expect(await screen.findByText('Kode baru sudah dikirim')).toBeInTheDocument();
    expect(sent(1)).toMatchObject({ path: '/api/v1/auth/code', body: { email: 'rani@example.com', purpose: 'sign_up', persona: 'mitra' } });
  });

  it('rejects anything but six digits before asking the service', async () => {
    const user = userEvent.setup();
    render(<CodeView />);

    await user.type(screen.getByRole('textbox', { name: /Kode verifikasi/ }), '12ab');
    await user.click(screen.getByRole('button', { name: 'Masuk' }));

    expect(screen.getByRole('link', { name: 'Isi kode verifikasi enam angka dari email Anda.' })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('signs in, forgets the old persona cookie and opens the persona home', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: makeMe({ persona: 'mitra' }) }];
    render(<CodeView />);

    await user.type(screen.getByRole('textbox', { name: /Kode verifikasi/ }), '123456');
    await user.click(screen.getByRole('button', { name: 'Masuk' }));

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/discover'));
    expect(forgetPersona).toHaveBeenCalled();
    expect(sessionStorage.getItem('tr_masuk')).toBeNull();
  });

  it('sends a visitor with nothing pending back to the start', async () => {
    sessionStorage.clear();
    render(<CodeView />);

    await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/start'));
  });
});

describe('acting context (UX-02)', () => {
  it('switches context, reloads and announces it without moving focus', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: makeMe({ organization: true, actingAsOrganization: true }) }];
    render(<ContextBar me={makeMe({ organization: true })} />);

    await user.selectOptions(screen.getByRole('combobox', { name: 'Bertindak sebagai' }), ORGANIZATION_PARTY);

    expect(await screen.findByText('Sekarang bertindak sebagai Demo Circular Materials Ltd')).toBeInTheDocument();
    expect(sent()).toMatchObject({ path: '/api/v1/me/context', method: 'PUT', body: { party_id: ORGANIZATION_PARTY } });
    expect(router.refresh).toHaveBeenCalled();
    expect(screen.getByRole('combobox', { name: 'Bertindak sebagai' })).toHaveFocus();
  });

  it('keeps the old context and explains a refused switch', async () => {
    const user = userEvent.setup();
    replies = [{ status: 404, body: failure('NOT_FOUND', 'Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi.') }];
    render(<ContextBar me={makeMe({ organization: true })} />);

    await user.selectOptions(screen.getByRole('combobox', { name: 'Bertindak sebagai' }), ORGANIZATION_PARTY);

    expect(await screen.findByText('Konteks tidak berubah')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Bertindak sebagai' })).toHaveValue(PERSONAL);
  });

  it('shows the acting party read-only beside a consequential action', () => {
    render(<ContextSwitcher readOnly value={ORGANIZATION_PARTY} options={[{ id: ORGANIZATION_PARTY, kind: 'organization', name: 'Demo' }]} actionLabel="Mengundang sebagai" />);

    expect(screen.getByText(/Mengundang sebagai:/)).toHaveTextContent('Mengundang sebagai: Demo · Organisasi');
    expect(screen.queryByRole('combobox')).toBeNull();
  });
});

describe('account and organizations (S18)', () => {
  it('saves account changes against the version shown', async () => {
    const user = userEvent.setup();
    replies = [{ status: 200, body: makeMe() }];
    render(<AccountForm me={makeMe()} />);

    await user.selectOptions(screen.getByRole('combobox', { name: 'Menu yang ditampilkan' }), 'mitra');
    await user.click(screen.getByRole('button', { name: 'Simpan akun' }));

    expect(await screen.findByText('Akun tersimpan')).toBeInTheDocument();
    expect(sent()).toMatchObject({ method: 'PATCH', body: { persona: 'mitra', expected_version: 1 } });
  });

  it('explains a stale account change and keeps the edits', async () => {
    const user = userEvent.setup();
    replies = [{ status: 409, body: failure('STALE_VERSION', 'Data ini sudah diubah sejak Anda membukanya.', { current_version: 2 }) }];
    render(<AccountForm me={makeMe()} />);

    await user.clear(screen.getByRole('textbox', { name: /Nama tampilan/ }));
    await user.type(screen.getByRole('textbox', { name: /Nama tampilan/ }), 'Rani S.');
    await user.click(screen.getByRole('button', { name: 'Simpan akun' }));

    expect(await screen.findByText('Data ini sudah diubah sejak Anda membukanya.')).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Nama tampilan/ })).toHaveValue('Rani S.');
  });

  it('creates an organization with an idempotency key, reused when the same request is retried', async () => {
    const user = userEvent.setup();
    replies = [
      { status: 503, body: failure('DATABASE_UNAVAILABLE', 'Layanan data sedang tidak tersedia.', {}, { retryable: true }) },
      { status: 201, body: { id: ORGANIZATION } },
    ];
    render(<CreateOrganizationForm />);

    await user.type(screen.getByRole('textbox', { name: /Nama organisasi/ }), 'Demo');
    await user.selectOptions(screen.getByRole('combobox', { name: /Jenis organisasi/ }), 'company');
    await user.click(screen.getByRole('button', { name: 'Buat organisasi' }));
    await screen.findByText('Layanan data sedang tidak tersedia.');
    await user.click(screen.getByRole('button', { name: 'Buat organisasi' }));

    expect(await screen.findByText(/Organisasi dibuat/)).toBeInTheDocument();
    expect(sent(0).headers['Idempotency-Key']).toBeTruthy();
    expect(sent(1).headers['Idempotency-Key']).toBe(sent(0).headers['Idempotency-Key']);
    expect(sent(1).body).toEqual({ name: 'Demo', kind: 'company' });
  });

  it('requires a name and kind before creating an organization', async () => {
    const user = userEvent.setup();
    render(<CreateOrganizationForm />);

    await user.click(screen.getByRole('button', { name: 'Buat organisasi' }));

    expect(screen.getByRole('link', { name: 'Isi nama organisasi.' })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('invites with chosen capabilities acting as the organization', async () => {
    const user = userEvent.setup();
    const me = makeMe({ organization: true, actingAsOrganization: true });
    replies = [{ status: 201, body: {} }];
    render(<InviteForm me={me} organizationId={ORGANIZATION} />);

    await user.type(screen.getByRole('textbox', { name: /Email anggota/ }), 'eve@example.com');
    await user.click(screen.getByRole('button', { name: 'Kirim undangan' }));
    expect(screen.getByRole('link', { name: 'Pilih setidaknya satu kewenangan.' })).toBeInTheDocument();
    await user.click(screen.getByRole('checkbox', { name: 'Mengubah portofolio' }));
    await user.click(screen.getByRole('button', { name: 'Kirim undangan' }));

    expect(await screen.findByText('Undangan dikirim. Berlaku 7 hari.')).toBeInTheDocument();
    expect(sent()).toMatchObject({
      path: `/api/v1/organizations/${ORGANIZATION}/invitations`,
      body: { acting_party_id: ORGANIZATION_PARTY, email: 'eve@example.com', capabilities: ['edit_portfolio'] },
    });
  });

  it('revokes, accepts and signs out through the service', async () => {
    const user = userEvent.setup();
    const me = makeMe({ organization: true, actingAsOrganization: true });
    replies = [{ status: 200, body: {} }, { status: 200, body: {} }, { status: 204 }];
    render(
      <>
        <RevokeButton me={me} invitationId="i1" email="eve@example.com" />
        <AcceptInvitationButton token="tok" />
        <SignOutButton />
      </>,
    );

    await user.click(screen.getByRole('button', { name: /Cabut undangan/ }));
    await screen.findByText('Undangan dicabut');
    await user.click(screen.getByRole('button', { name: 'Terima undangan' }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/settings?bergabung=1'));
    await user.click(screen.getByRole('button', { name: 'Keluar' }));
    await waitFor(() => expect(router.push).toHaveBeenCalledWith('/start?masuk=1'));

    expect([sent(0).path, sent(1).path, sent(2).path]).toEqual(['/api/v1/invitations/i1/revoke', '/api/v1/invitations/tok/accept', '/api/v1/auth/sign-out']);
    expect(sent(0).body).toEqual({ acting_party_id: ORGANIZATION_PARTY });
  });

  it('lists summary rows with a contextual change link', () => {
    render(<SummaryList rows={[{ id: 'nama', label: 'Nama tampilan', value: 'Rani', changeHref: '#ubah' }]} />);

    expect(screen.getByRole('link', { name: /Ubah\s*nama tampilan/ })).toHaveAttribute('href', '#ubah');
  });
});
