import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { en } from '@/features/i18n/en';
import { id } from '@/features/i18n/id';
import { LocaleProvider } from '@/features/i18n/LocaleProvider';
import { localHref, switchHref, toIndonesianPath } from '@/features/i18n/locale';
import { StartView } from '@/views/StartView';
import { SubscribeView } from '@/views/subscriptions/SubscribeView';
import { TeaserView } from '@/views/subscriptions/TeaserView';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

const fetchMock = vi.fn(async () => new Response(JSON.stringify({ status: 'check_email' }), { status: 202 }));

beforeEach(() => {
  fetchMock.mockClear();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

function keysOf(value: unknown, prefix = ''): string[] {
  if (typeof value !== 'object' || value === null) return [`${prefix}:${typeof value}`];
  return Object.entries(value).flatMap(([key, child]) => keysOf(child, `${prefix}.${key}`));
}

describe('bilingual foundation (spec 050)', () => {
  it('has the same keys and kinds of message in both languages', () => {
    const shape = (messages: object) => keysOf(messages).filter((key) => !key.startsWith('.sectors.'));
    expect(shape(en)).toEqual(shape(id));
  });

  it('maps English addresses to the Indonesian pages and back, keeping the query', () => {
    expect(toIndonesianPath('/en/subscribe/manage?token=abc')).toBe('/langganan/atur?token=abc');
    expect(toIndonesianPath('/en/inventions/123')).toBe('/temuan/123');
    expect(toIndonesianPath('/en')).toBe('/');
    expect(localHref('en', '/start?masuk=1&kembali=%2Finventions%2F1')).toBe('/en/start?masuk=1&kembali=%2Finventions%2F1');
    expect(localHref('en', '/start/kode')).toBe('/en/start/code');
    expect(localHref('en', '/')).toBe('/en');
    expect(localHref('id', '/langganan')).toBe('/langganan');
    expect(switchHref('en', '/en/subscribe/confirm?token=t')).toBe('/langganan/konfirmasi?token=t');
    expect(switchHref('id', '/langganan/konfirmasi?token=t')).toBe('/en/subscribe/confirm?token=t');
  });

  it('shows the start screen in English with English field words and links that stay in English', () => {
    render(
      <LocaleProvider locale="en">
        <StartView persona={null} mode="sign_up" returnTo={null} />
      </LocaleProvider>,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Welcome to TemuRiset' })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /^Display name/ })).toBeInTheDocument();
    expect(screen.getAllByText('(required)').length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: 'Subscribe to invention news' })).toHaveAttribute('href', '/en/subscribe');
    expect(screen.getByRole('link', { name: /View this page in Indonesian/ })).toHaveAttribute('hreflang', 'id');
  });

  it('subscribes from the English page in English, so every email is English', async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider locale="en">
        <SubscribeView />
      </LocaleProvider>,
    );

    await user.type(screen.getByLabelText(/Email/), 'investor@example.com');
    await user.click(screen.getByLabelText('Water and sanitation'));
    await user.click(screen.getByRole('button', { name: 'Subscribe' }));

    expect(await screen.findByRole('heading', { name: 'Check your email' })).toBeInTheDocument();
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toMatchObject({ locale: 'en', topics: { sectors: ['Air dan sanitasi'] } });
  });

  it('labels inventor content as written in Indonesian on the English summary page', () => {
    const teaser = {
      id: '11111111-1111-4111-8111-111111111111',
      title: 'ClearSpring',
      summary: 'Filter air tenaga surya untuk desa.',
      sector: 'Air dan sanitasi',
      stage: 'PROTOTYPE' as const,
      keywords: ['filter'],
      inventor_name: 'An inventor on TemuRiset',
      published_at: '2026-11-10T10:00:00Z',
    };
    render(<TeaserView teaser={teaser} locale="en" />);

    expect(screen.getByText('Written in Indonesian')).toBeInTheDocument();
    expect(screen.getByText('Filter air tenaga surya untuk desa.')).toHaveAttribute('lang', 'id');
    expect(screen.getByText('Water and sanitation · Prototype')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign up to see the details' })).toHaveAttribute('href', `/en/start?kembali=${encodeURIComponent(`/inventions/${teaser.id}`)}`);
  });
});
