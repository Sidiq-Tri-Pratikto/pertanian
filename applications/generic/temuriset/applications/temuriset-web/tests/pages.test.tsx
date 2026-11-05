import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';

const cookieJar = new Map<string, string>();
const setCookie = vi.fn((name: string, value: string) => cookieJar.set(name, value));

vi.mock('next/headers', () => ({
  cookies: async () => ({ get: (name: string) => (cookieJar.has(name) ? { value: cookieJar.get(name) } : undefined), set: setCookie }),
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
}));

const { choosePersona } = await import('@/features/actions');
const RootPage = (await import('@/app/page')).default;
const StartPage = (await import('@/app/start/page')).default;
const HomePage = (await import('@/app/home/page')).default;
const InventionsPage = (await import('@/app/inventions/page')).default;
const DiscoverPage = (await import('@/app/discover/page')).default;
const OpportunitiesPage = (await import('@/app/opportunities/page')).default;
const PitchesPage = (await import('@/app/pitches/page')).default;
const SettingsPage = (await import('@/app/settings/page')).default;
const ComingSoon = await import('@/app/segera-hadir/[feature]/page');
const NotFound = (await import('@/app/not-found')).default;

async function redirectOf(run: () => Promise<unknown>): Promise<string> {
  try {
    await run();
  } catch (error) {
    if (error instanceof Redirect) return error.url;
    throw error;
  }
  throw new Error('expected a redirect');
}

function form(values: Record<string, string>): FormData {
  const data = new FormData();
  Object.entries(values).forEach(([key, value]) => data.set(key, value));
  return data;
}

beforeEach(() => {
  cookieJar.clear();
  setCookie.mockClear();
  vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('routing without a persona', () => {
  it('sends a first visit to the start screen', async () => {
    expect(await redirectOf(() => RootPage())).toBe('/start');
    expect(await redirectOf(() => HomePage())).toBe('/start');
  });

  it('shows the start screen with no form to complete beyond one choice', async () => {
    render((await StartPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Selamat datang di TemuRiset' })).toBeInTheDocument();
    expect(screen.getAllByRole('radio')).toHaveLength(2);
    expect(screen.queryByRole('textbox')).toBeNull();
  });

  it('explains a submission with no choice', async () => {
    render((await StartPage({ searchParams: Promise.resolve({ galat: 'peran' }) })) as ReactElement);

    expect(screen.getByRole('alert')).toHaveTextContent('Pilih salah satu cara memakai TemuRiset');
  });
});

describe('choosing a persona', () => {
  it('stores the persona in an http-only cookie and opens its first destination', async () => {
    expect(await redirectOf(() => choosePersona(form({ persona: 'mitra', origin: 'start' })))).toBe('/discover');
    expect(setCookie).toHaveBeenCalledWith('tr_persona', 'mitra', expect.objectContaining({ httpOnly: true, sameSite: 'lax' }));
  });

  it('returns to settings with a saved notice when changed there', async () => {
    expect(await redirectOf(() => choosePersona(form({ persona: 'inovator', origin: 'settings' })))).toBe('/settings?tersimpan=1');
  });

  it('rejects anything but the two personas without storing it', async () => {
    expect(await redirectOf(() => choosePersona(form({ persona: 'operator', origin: 'start' })))).toBe('/start?galat=peran');
    expect(setCookie).not.toHaveBeenCalled();
  });
});

describe('destinations for an inventor', () => {
  beforeEach(() => {
    cookieJar.set('tr_persona', 'inovator');
  });

  it('opens Beranda for a returning inventor', async () => {
    expect(await redirectOf(() => RootPage())).toBe('/home');
  });

  it('shows an honest empty Beranda with the service check and planned features', async () => {
    render((await HomePage()) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Beranda' })).toBeInTheDocument();
    expect(screen.getByText('Belum ada yang perlu dikerjakan')).toBeInTheDocument();
    expect(screen.getByText('Memeriksa layanan…')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Lihat rencana Portofolio inovasi/ })).toHaveAttribute('href', '/segera-hadir/inovasi');
  });

  it.each([
    [InventionsPage, 'Inovasi Saya'],
    [DiscoverPage, 'Temukan Investor/Mitra'],
    [OpportunitiesPage, 'Kebutuhan/Mandat'],
  ])('renders %#: %s', async (Page, title) => {
    render((await Page()) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: title })).toBeInTheDocument();
  });

  it('lists outgoing pitches', async () => {
    render((await PitchesPage({ searchParams: Promise.resolve({}) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Pitching dan Diskusi' })).toBeInTheDocument();
  });

  it('describes a planned feature without creating anything', async () => {
    render((await ComingSoon.default({ params: Promise.resolve({ feature: 'jadwal' }) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Jadwal pertemuan' })).toBeInTheDocument();
    expect(screen.getByText(/Tidak ada data yang dibuat atau disimpan/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Kembali' })).toHaveAttribute('href', '/home');
    expect(screen.queryByText(/Spesifikasi/)).toBeNull();
    expect(await ComingSoon.generateMetadata({ params: Promise.resolve({ feature: 'jadwal' }) })).toEqual({ title: 'Jadwal pertemuan' });
  });

  it('says so when a feature address is unknown, and offers a way back', async () => {
    render((await ComingSoon.default({ params: Promise.resolve({ feature: 'escrow' }) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Fitur tidak dikenal' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Lihat semua rencana fitur' })).toHaveAttribute('href', '/settings#rencana');
    expect(await ComingSoon.generateMetadata({ params: Promise.resolve({ feature: 'escrow' }) })).toEqual({ title: 'Fitur tidak dikenal' });
  });

  it('lists every planned feature in settings and confirms a saved view', async () => {
    render((await SettingsPage({ searchParams: Promise.resolve({ tersimpan: '1' }) })) as ReactElement);

    expect(screen.getByRole('heading', { name: 'Rencana fitur' })).toBeInTheDocument();
    expect(screen.getByText('Tampilan tersimpan')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Saya punya inovasi/ })).toBeChecked();
  });

  it('explains an unsaved view change in settings', async () => {
    render((await SettingsPage({ searchParams: Promise.resolve({ galat: 'peran' }) })) as ReactElement);

    expect(screen.getByRole('alert')).toHaveTextContent('Pilih salah satu tampilan');
  });
});

describe('destinations for a partner', () => {
  beforeEach(() => {
    cookieJar.set('tr_persona', 'mitra');
  });

  it('starts at Jelajahi', async () => {
    render((await DiscoverPage()) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Jelajahi' })).toBeInTheDocument();
  });

  it('reads incoming and discussion boxes', async () => {
    render((await PitchesPage({ searchParams: Promise.resolve({ box: 'diskusi' }) })) as ReactElement);

    expect(screen.getByRole('heading', { level: 1, name: 'Diskusi dan Jadwal' })).toBeInTheDocument();
  });

  it('still opens Beranda when asked directly', async () => {
    render((await HomePage()) as ReactElement);

    expect(screen.getByText(/Pitching yang menunggu keputusan Anda/)).toBeInTheDocument();
  });
});

describe('unknown addresses', () => {
  it('offer a way back', () => {
    render(<NotFound />);

    expect(screen.getByRole('link', { name: 'Kembali ke awal' })).toHaveAttribute('href', '/');
  });
});
