import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';

import { ApiError } from '@/api/errors';

import { makeMe, ORGANIZATION } from './fixtures';

// What the service answers to server reads; each test sets who is signed in.
let me: ReturnType<typeof makeMe> | null = null;
let deployed: string[] | null = ['core', 'company_funding'];
let supportRequests: unknown[] = [];
const cookieJar = new Map<string, string>();

vi.mock('next/headers', () => ({
  cookies: async () => ({ get: (name: string) => (cookieJar.has(name) ? { value: cookieJar.get(name) } : undefined), delete: vi.fn() }),
}));

vi.mock('@/features/capabilities', () => ({ readCapabilities: async () => deployed }));

vi.mock('@/api/server', () => ({
  serverGet: async (path: string) => {
    if (path === '/api/v1/me') {
      if (!me) throw new ApiError('UNAUTHENTICATED', 'Anda perlu masuk terlebih dahulu.', { retryable: false });
      return me;
    }
    if (path === '/api/v1/profiles/me') return { party_id: me?.active_party_id, bio: '', published: false, version: 1 };
    if (path === '/api/v1/inventions') return [];
    if (path === '/api/v1/support-requests') return supportRequests;
    if (path === '/api/v1/opportunities') return [];
    if (path === '/api/v1/funding-requests') return [];
    if (path.startsWith('/api/v1/pitches?')) return [];
    if (path === '/api/v1/me/queue') return [];
    if (path.startsWith('/api/v1/notifications')) return [];
    if (path.startsWith('/api/v1/discovery?')) {
      const sections = ['relevant', 'new', 'curated'].map((id) => ({ id, title: id, items: [] }));
      return { type: 'partners', sections, filters: {}, next_cursor: null, total_estimate: 0, relaxation: null };
    }
    if (path === `/api/v1/organizations/${ORGANIZATION}/members`) {
      return [{ account_id: 'a', display_name: 'Bima', capabilities: ['manage_members'], version: 1 }];
    }
    if (path === `/api/v1/organizations/${ORGANIZATION}/invitations`) {
      return [{ id: 'i1', email: 'eve@example.com', capabilities: ['schedule'], expires_at: '2026-11-12T02:00:00Z', status: 'pending' }];
    }
    if (path === '/api/v1/invitations/good') {
      return { organization_name: 'Demo Circular Materials Ltd', capabilities: ['edit_portfolio'], expires_at: '2026-11-12T02:00:00Z', status: 'pending' };
    }
    if (path === '/api/v1/invitations/old') {
      return { organization_name: 'Demo Circular Materials Ltd', capabilities: ['edit_portfolio'], expires_at: '2026-11-01T02:00:00Z', status: 'expired' };
    }
    if (path === '/api/v1/invitations/down') throw ApiError.unreachable();
    throw new ApiError('NOT_FOUND', 'Data yang diminta tidak ditemukan.', { retryable: false });
  },
}));

class Redirect extends Error {
  constructor(readonly url: string) {
    super(url);
  }
}

vi.mock('next/navigation', () => ({
  redirect: (url: string) => {
    throw new Redirect(url);
  },
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
}));

const RootPage = (await import('@/app/page')).default;
const StartPage = (await import('@/app/start/page')).default;
const CodePage = (await import('@/app/start/kode/page')).default;
const HomePage = (await import('@/app/home/page')).default;
const InventionsPage = (await import('@/app/inventions/page')).default;
const DiscoverPage = (await import('@/app/discover/page')).default;
const OpportunitiesPage = (await import('@/app/opportunities/page')).default;
const PitchesPage = (await import('@/app/pitches/page')).default;
const SettingsPage = (await import('@/app/settings/page')).default;
const InvitationPage = (await import('@/app/undangan/[token]/page')).default;
const ComingSoon = await import('@/app/segera-hadir/[feature]/page');
const NotFound = (await import('@/app/not-found')).default;
const { safeReturn } = await import('@/features/session');

async function redirectOf(run: () => Promise<unknown>): Promise<string> {
  try {
    await run();
  } catch (error) {
    if (error instanceof Redirect) return error.url;
    throw error;
  }
  throw new Error('expected a redirect');
}

beforeEach(() => {
  me = null;
  deployed = ['core', 'company_funding'];
  supportRequests = [];
  cookieJar.clear();
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('a visitor who is not signed in', () => {
  it('starts at the start screen, and every page returns there after sign-in', async () => {
    expect(await redirectOf(() => RootPage())).toBe('/start');
    expect(await redirectOf(() => HomePage())).toBe('/start?kembali=%2Fhome');
    expect(await redirectOf(() => SettingsPage({ searchParams: Promise.resolve({}) }))).toBe('/start?kembali=%2Fsettings');
    expect(await redirectOf(() => InvitationPage({ params: Promise.resolve({ token: 'good' }) }))).toBe('/start?kembali=%2Fundangan%2Fgood');
  });

  it('signs up with persona, name, email, language and time zone, and never an organization', async () => {
    render((await StartPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Selamat datang di TemuRiset' })).toBeInTheDocument();
    expect(screen.getAllByRole('radio')).toHaveLength(2);
    expect(screen.getByRole('textbox', { name: /Nama tampilan/ })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /Email/ })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Bahasa' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /Zona waktu/ })).toBeInTheDocument();
    expect(screen.queryByText(/organisasi|institusi/i, { selector: 'label' })).toBeNull();
  });

  it('pre-selects the persona chosen before accounts existed', async () => {
    cookieJar.set('tr_persona', 'mitra');

    render((await StartPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('radio', { name: /Saya berinvestasi/ })).toBeChecked();
  });

  it('signs in with only an email', async () => {
    render((await StartPage({ searchParams: Promise.resolve({ masuk: '1' }) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Masuk ke TemuRiset' })).toBeInTheDocument();
    expect(screen.queryByRole('radio')).toBeNull();
    expect(screen.getByRole('link', { name: 'Daftar' })).toHaveAttribute('href', '/start');
  });

  it('keeps the return address when switching between sign-up and sign-in', async () => {
    render((await StartPage({ searchParams: Promise.resolve({ kembali: '/settings' }) })) as ReactElement);

    expect(screen.getByRole('link', { name: 'Masuk' })).toHaveAttribute('href', '/start?masuk=1&kembali=%2Fsettings');
  });

  it('only follows a return address on this site', () => {
    expect(safeReturn('/settings')).toBe('/settings');
    expect(safeReturn('//evil.example')).toBeNull();
    expect(safeReturn('/\\evil.example')).toBeNull();
    expect(safeReturn('https://evil.example')).toBeNull();
    expect(safeReturn(undefined)).toBeNull();
  });
});

describe('a signed-in inventor', () => {
  beforeEach(() => {
    me = makeMe();
  });

  it('opens Beranda, and the start and code screens send it home or back where it was going', async () => {
    expect(await redirectOf(() => RootPage())).toBe('/home');
    expect(await redirectOf(() => StartPage({ searchParams: Promise.resolve({}) }))).toBe('/home');
    expect(await redirectOf(() => StartPage({ searchParams: Promise.resolve({ kembali: '/settings' }) }))).toBe('/settings');
    expect(await redirectOf(() => CodePage())).toBe('/home');
  });

  it('shows an honest empty Beranda with the context in the bar and planned features', async () => {
    render((await HomePage()) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Beranda' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Bertindak sebagai' })).toHaveDisplayValue('Rani · Pribadi');
    expect(screen.getByText('Memeriksa layanan…')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Lihat rencana Kerja Sama/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Lihat rencana Akun dan konteks kerja/ })).toBeNull();
    expect(screen.queryByRole('link', { name: /Lihat rencana Portofolio inovasi/ })).toBeNull();
  });

  it.each([
    [InventionsPage, 'Inovasi Saya'],
    [DiscoverPage, 'Temukan Investor/Mitra'],
    [OpportunitiesPage, 'Kebutuhan/Mandat'],
  ])('renders %#: %s', async (Page, title) => {
    render((await Page({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: title })).toBeInTheDocument();
  });

  it('lists outgoing pitches', async () => {
    render((await PitchesPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Pitching dan Diskusi' })).toBeInTheDocument();
  });

  it('describes a planned feature without creating anything', async () => {
    render((await ComingSoon.default({ params: Promise.resolve({ feature: 'privasi-laporan' }) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Privasi dan laporan' })).toBeInTheDocument();
    expect(screen.getByText(/Tidak ada data yang dibuat atau disimpan/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Kembali' })).toHaveAttribute('href', '/home');
    expect(await ComingSoon.generateMetadata({ params: Promise.resolve({ feature: 'privasi-laporan' }) })).toEqual({ title: 'Privasi dan laporan' });
  });

  it('sends a shipped feature to its screen and says so for an unknown one', async () => {
    expect(await redirectOf(() => ComingSoon.default({ params: Promise.resolve({ feature: 'akun' }) }))).toBe('/settings');

    render((await ComingSoon.default({ params: Promise.resolve({ feature: 'escrow' }) })) as ReactElement);
    expect(screen.getByRole('heading', { level: 1, name: 'Fitur tidak dikenal' })).toBeInTheDocument();
  });

  it('shows the account, no organization requirement, and every planned feature in settings', async () => {
    render((await SettingsPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByText('rani@example.com · Email terverifikasi')).toBeInTheDocument();
    expect(screen.getByText('Asia/Jakarta')).toBeInTheDocument();
    expect(screen.getByText(/Organisasi tidak wajib/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Rencana fitur' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /Anggota/ })).toBeNull();
    expect(screen.getByRole('button', { name: 'Keluar' })).toBeInTheDocument();
  });

  it('confirms joining an organization', async () => {
    render((await SettingsPage({ searchParams: Promise.resolve({ bergabung: '1' }) })) as ReactElement);

    expect(screen.getByText('Anda sudah bergabung dengan organisasi')).toBeInTheDocument();
  });
});

describe('an account acting as its organization', () => {
  beforeEach(() => {
    me = makeMe({ organization: true, actingAsOrganization: true });
  });

  it('lists members and invitations with expiry, and offers to invite and revoke', async () => {
    render((await SettingsPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('combobox', { name: 'Bertindak sebagai' })).toHaveDisplayValue('Demo Circular Materials Ltd · Organisasi');
    expect(screen.getByRole('heading', { name: 'Anggota Demo Circular Materials Ltd' })).toBeInTheDocument();
    expect(screen.getByText('Bima')).toBeInTheDocument();
    expect(screen.getByText('eve@example.com', { selector: 'strong' }).parentElement).toHaveTextContent('Menunggu · berlaku sampai 12 Nov 2026');
    expect(screen.getByRole('button', { name: /Cabut undangan\s*untuk eve@example.com/ })).toBeInTheDocument();
    expect(screen.getByText('Mengundang sebagai:', { exact: false })).toHaveTextContent('Demo Circular Materials Ltd · Organisasi');
  });
});

describe('an invitation link', () => {
  beforeEach(() => {
    me = makeMe();
  });

  it('shows the organization, capabilities and expiry before accepting', async () => {
    render((await InvitationPage({ params: Promise.resolve({ token: 'good' }) })) as ReactElement);

    expect(screen.getByText('Demo Circular Materials Ltd')).toBeInTheDocument();
    expect(screen.getByText('Mengubah portofolio')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Terima undangan' })).toBeInTheDocument();
  });

  it('cannot be accepted once expired', async () => {
    render((await InvitationPage({ params: Promise.resolve({ token: 'old' }) })) as ReactElement);

    expect(screen.queryByRole('button', { name: 'Terima undangan' })).toBeNull();
    expect(screen.getByText('Undangan ini tidak dapat diterima')).toBeInTheDocument();
  });

  it('reveals nothing for another email or an unknown token', async () => {
    render((await InvitationPage({ params: Promise.resolve({ token: 'other' }) })) as ReactElement);

    expect(screen.getByText('Undangan tidak ditemukan')).toBeInTheDocument();
  });

  it('lets an outage reach the error page instead of claiming the invitation is gone', async () => {
    await expect(InvitationPage({ params: Promise.resolve({ token: 'down' }) })).rejects.toMatchObject({ code: 'NETWORK_UNREACHABLE' });
  });
});

describe('a partner', () => {
  beforeEach(() => {
    me = makeMe({ persona: 'mitra' });
  });

  it('starts at Jelajahi', async () => {
    expect(await redirectOf(() => RootPage())).toBe('/discover');
    render((await DiscoverPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Jelajahi' })).toBeInTheDocument();
  });

  it('reads incoming and discussion boxes', async () => {
    render((await PitchesPage({ searchParams: Promise.resolve({ box: 'diskusi' }) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Diskusi dan Jadwal' })).toBeInTheDocument();
  });
});

describe('features of optional capabilities', () => {
  beforeEach(() => {
    me = makeMe();
  });

  it('lists organization review only where the deployment runs it', async () => {
    deployed = ['core', 'company_funding', 'organization_review'];
    const { unmount } = render((await SettingsPage({ searchParams: Promise.resolve({}) })) as ReactElement);
    expect(screen.getByRole('heading', { name: 'Tinjauan organisasi' })).toBeInTheDocument();
    unmount();

    deployed = ['core', 'company_funding'];
    render((await SettingsPage({ searchParams: Promise.resolve({}) })) as ReactElement);
    expect(screen.queryByRole('heading', { name: 'Tinjauan organisasi' })).toBeNull();
  });

  it('sends shipped company funding to its screen, and hides it in a project-support-only deployment', async () => {
    expect(await redirectOf(() => ComingSoon.default({ params: Promise.resolve({ feature: 'pendanaan-perusahaan' }) }))).toBe('/support-requests#pendanaan');

    deployed = ['core'];
    render((await ComingSoon.default({ params: Promise.resolve({ feature: 'pendanaan-perusahaan' }) })) as ReactElement);
    expect(screen.getByRole('heading', { level: 1, name: 'Fitur tidak dikenal' })).toBeInTheDocument();
  });

  it('offers no optional feature when the manifest cannot be read', async () => {
    deployed = null;

    render((await SettingsPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.queryByRole('link', { name: /Lihat rencana Tinjauan organisasi/ })).toBeNull();
    expect(screen.getByRole('link', { name: 'Lihat profil publik' })).toBeInTheDocument();
  });
});

describe('unknown addresses', () => {
  it('offer a way back', () => {
    render(<NotFound />);

    expect(screen.getByRole('link', { name: 'Kembali ke awal' })).toHaveAttribute('href', '/');
  });
});
