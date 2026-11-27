import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { PublicPageForm } from '@/features/portfolio/PublicPageForm';
import { TeaserView } from '@/views/subscriptions/TeaserView';

const router = { push: vi.fn(), replace: vi.fn(), refresh: vi.fn() };
vi.mock('next/navigation', () => ({ useRouter: () => router }));

const fetchMock = vi.fn(async () => new Response(JSON.stringify({}), { status: 200 }));

beforeEach(() => {
  fetchMock.mockClear();
  router.refresh.mockClear();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

const TEASER = {
  id: '11111111-1111-4111-8111-111111111111',
  title: 'Pengering surya untuk kopi',
  summary: 'Pengering tertutup untuk koperasi.',
  sector: 'Pertanian',
  stage: 'PROTOTYPE' as const,
  keywords: [],
  inventor_name: 'Dina Putri',
  published_at: '2026-11-20T10:00:00Z',
  follow_enabled: true,
  field_test_summary: 'Dua siklus pengeringan selesai di satu koperasi.',
  photo: { url: '/api/v1/teasers/inventions/x/photo?v=1', alt: 'Pengering di halaman koperasi', width: 640, height: 480, orientation: 6 },
  content_locale: 'id' as const,
};

const IMAGE_DOCUMENT = {
  id: 'doc-1',
  title: 'Foto prototipe',
  kind: 'evidence',
  versions: [{ number: 2, media_type: 'image/jpeg', size_bytes: 10, sha256: 'x', file_state: 'AVAILABLE', extraction_state: 'NOT_REQUESTED', review_state: 'PROVIDED_UNREVIEWED', created_at: '2026-11-20T10:00:00Z' }],
} as never;

describe('public invention page (spec 051)', () => {
  it('shows the photo at its size, turned as recorded, with the field test and its description', () => {
    render(<TeaserView teaser={TEASER} />);

    const photo = screen.getByRole('img', { name: 'Pengering di halaman koperasi' });
    expect(photo).toHaveAttribute('width', '640');
    expect(photo).toHaveAttribute('height', '480');
    expect(photo.style.transform).toContain('rotate(90deg)');
    expect(photo.parentElement!.style.aspectRatio).toBe('480 / 640');
    expect(screen.getByRole('heading', { name: 'Uji lapangan' })).toBeInTheDocument();
    expect(screen.getByText('Pertanian · Prototipe')).toBeInTheDocument();
  });

  it('labels content written in English on the Indonesian page', () => {
    render(<TeaserView teaser={{ ...TEASER, content_locale: 'en', photo: null }} />);

    expect(screen.getByText('Ditulis dalam bahasa Inggris')).toBeInTheDocument();
    expect(screen.getByText('Pengering tertutup untuk koperasi.')).toHaveAttribute('lang', 'en');
  });

  it('publishes the page with a photo, a description and the field test, and says it emails no one', async () => {
    const user = userEvent.setup();
    render(<PublicPageForm inventionId="inv-1" actingPartyId="party-1" version={4} page={{ enabled: false }} documents={[IMAGE_DOCUMENT]} />);

    expect(screen.getByText(/tidak mengirim email ke siapa pun/)).toBeInTheDocument();
    await user.click(screen.getByLabelText('Tampilkan halaman publik inovasi ini'));
    await user.type(screen.getByLabelText(/Ringkasan uji lapangan/), 'Dua siklus selesai.');
    await user.selectOptions(screen.getByRole('combobox', { name: /Foto/ }), 'doc-1:2');
    await user.click(screen.getByRole('button', { name: 'Simpan halaman publik' }));
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getAllByText(/Tulis apa yang terlihat di foto/).length).toBeGreaterThan(0);

    await user.type(screen.getByLabelText(/Apa yang terlihat di foto/), 'Prototipe di meja kerja');
    await user.click(screen.getByRole('button', { name: 'Simpan halaman publik' }));

    await waitFor(() => expect(router.refresh).toHaveBeenCalled());
    const [path, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(path).toBe('/api/v1/inventions/inv-1/public-page');
    expect(JSON.parse(String(init.body))).toEqual({
      acting_party_id: 'party-1',
      expected_version: 4,
      enabled: true,
      field_test: 'Dua siklus selesai.',
      photo: { document_id: 'doc-1', version: 2 },
      photo_alt: 'Prototipe di meja kerja',
      content_locale: 'id',
    });
  });

  it('points to the evidence step when there is no image to choose', () => {
    render(<PublicPageForm inventionId="inv-1" actingPartyId="party-1" version={1} page={{}} documents={[]} />);

    expect(screen.getByRole('link', { name: 'langkah bukti' })).toHaveAttribute('href', '/inventions/inv-1/edit?step=2');
  });
});
