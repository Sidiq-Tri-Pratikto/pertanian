import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { DocumentsPanel } from '@/features/documents/DocumentsPanel';
import type { DocumentView } from '@/features/documents/model';
import { refusal, settled } from '@/features/documents/model';

import { makeMe, PERSONAL } from './fixtures';

const PDF = 'application/pdf';

function document(overrides: Partial<DocumentView['versions'][number]> = {}, grants: DocumentView['grants'] = []): DocumentView {
  return {
    id: 'd1',
    title: 'Laporan uji',
    kind: 'evidence',
    grants,
    versions: [
      {
        number: 1,
        media_type: PDF,
        size_bytes: 1000,
        sha256: 'x',
        file_state: 'AVAILABLE',
        extraction_state: 'SUCCEEDED',
        review_state: 'PROVIDED_UNREVIEWED',
        created_at: '2026-11-05T02:00:00Z',
        ...overrides,
      },
    ],
  };
}

const GRANT = { id: 'g1', version: 1, grantee_party_id: 'p2', grantee_name: 'Mitra A', purpose: 'pitch', revoked_at: null, downloads: 1 };

type Reply = { status: number; body?: unknown };
let replies: Record<string, Reply[]> = {};
const fetchMock = vi.fn(async (path: string, init?: RequestInit) => {
  const key = `${init?.method ?? 'GET'} ${path}`;
  const reply = replies[key]?.shift() ?? { status: 500, body: {} };
  return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), { status: reply.status });
});

class FakeXhr {
  static last: FakeXhr | null = null;
  static complete = true;
  status = 0;
  responseText = '';
  upload: { onprogress: ((event: { lengthComputable: boolean; loaded: number; total: number }) => void) | null } = { onprogress: null };
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onabort: (() => void) | null = null;
  method = '';
  url = '';
  constructor() {
    FakeXhr.last = this;
  }
  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }
  send() {
    this.upload.onprogress?.({ lengthComputable: true, loaded: 50, total: 100 });
    if (FakeXhr.complete) {
      this.status = 202;
      setTimeout(() => this.onload?.(), 0);
    }
  }
  abort() {
    this.onabort?.();
  }
}

function pdf(size = 100): File {
  const file = new File(['%PDF-1.4'], 'Laporan uji.pdf', { type: PDF });
  Object.defineProperty(file, 'size', { value: size });
  return file;
}

beforeEach(() => {
  replies = {};
  fetchMock.mockClear();
  FakeXhr.complete = true;
  vi.stubGlobal('fetch', fetchMock);
  vi.stubGlobal('XMLHttpRequest', FakeXhr);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('limits before upload', () => {
  it('states the limit or the accepted types, and only then', () => {
    expect(refusal({ type: PDF, size: 21 * 1024 * 1024 })).toBe('Berkas melebihi batas 20 MB untuk PDF dan DOCX. Pilih berkas yang lebih kecil.');
    expect(refusal({ type: 'image/png', size: 6 * 1024 * 1024 })).toContain('5 MB untuk gambar');
    expect(refusal({ type: 'video/mp4', size: 10 })).toContain('tidak didukung');
    expect(refusal({ type: PDF, size: 20 * 1024 * 1024 })).toBeNull();
  });

  it('shows a field error and sends nothing for a file over the limit', async () => {
    const user = userEvent.setup();
    render(<DocumentsPanel me={makeMe()} initial={[]} />);

    await user.upload(screen.getByLabelText('Unggah dokumen bukti'), pdf(21 * 1024 * 1024));

    expect(screen.getByText(/Berkas melebihi batas 20 MB/)).toBeInTheDocument();
    expect(screen.getByLabelText('Unggah dokumen bukti')).toHaveAttribute('aria-invalid', 'true');
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe('upload and states (UX-10)', () => {
  it('uploads with progress, then follows the scan until the file is available', async () => {
    const user = userEvent.setup();
    replies = {
      'POST /api/v1/documents/upload-intents': [{ status: 201, body: { intent_id: 'i1', upload_url: '/api/v1/documents/upload-intents/i1/content', max_bytes: 100, expires_at: '' } }],
      'GET /api/v1/documents': [
        { status: 200, body: [document({ file_state: 'QUARANTINED', extraction_state: 'NOT_REQUESTED' })] },
        { status: 200, body: [document()] },
      ],
    };
    render(<DocumentsPanel me={makeMe()} initial={[]} />);

    await user.upload(screen.getByLabelText('Unggah dokumen bukti'), pdf());

    expect(await screen.findByText('Sedang diperiksa keamanannya')).toBeInTheDocument();
    expect(screen.getByText(/belum dapat dipakai sampai pemeriksaan selesai/)).toBeInTheDocument();
    expect(await screen.findByText('Aman dan tersedia', {}, { timeout: 4000 })).toBeInTheDocument();
    expect(screen.getByText('Disediakan, belum diperiksa')).toBeInTheDocument();
    expect(await screen.findByText('Laporan uji: Aman dan tersedia')).toBeInTheDocument();
    expect(FakeXhr.last).toMatchObject({ method: 'PUT', url: '/api/v1/documents/upload-intents/i1/content' });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toMatchObject({ acting_party_id: PERSONAL, media_type: PDF, size_bytes: 100, title: 'Laporan uji' });
  });

  it('cancels a transfer and says so', async () => {
    const user = userEvent.setup();
    FakeXhr.complete = false;
    replies = { 'POST /api/v1/documents/upload-intents': [{ status: 201, body: { intent_id: 'i1', upload_url: '/x', max_bytes: 100, expires_at: '' } }] };
    render(<DocumentsPanel me={makeMe()} initial={[]} />);

    await user.upload(screen.getByLabelText('Unggah dokumen bukti'), pdf());
    expect(await screen.findByRole('progressbar', { name: /Kemajuan unggahan/ })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Batalkan unggahan/ }));

    expect(await screen.findByText('Laporan uji: Unggahan dibatalkan')).toBeInTheDocument();
    expect(screen.queryByRole('progressbar')).toBeNull();
  });

  it('shows a scan that needs manual reading and a rejected file, each on its own axis', () => {
    render(
      <DocumentsPanel
        me={makeMe()}
        initial={[document({ extraction_state: 'NEEDS_MANUAL_INPUT' }), { ...document({ file_state: 'REJECTED', extraction_state: 'NOT_REQUESTED' }), id: 'd2', title: 'Berkas aneh' }]}
      />,
    );

    expect(screen.getByText('Perlu diisi manual')).toBeInTheDocument();
    expect(screen.getByText('Ditolak saat pemeriksaan keamanan')).toBeInTheDocument();
    expect(screen.getByText('Berkas ini tidak dapat dipakai. Unggah berkas lain.')).toBeInTheDocument();
  });

  it('stops polling once every file is final', () => {
    expect(settled(document())).toBe(true);
    expect(settled(document({ file_state: 'QUARANTINED' }))).toBe(false);
    expect(settled(document({ extraction_state: 'RUNNING' }))).toBe(false);
  });
});

describe('grants and revocation', () => {
  it('says who has which version, and revokes through a dialog that returns focus', async () => {
    const user = userEvent.setup();
    replies = {
      'POST /api/v1/grants/g1/revoke': [{ status: 200, body: { revoked: true, copies_already_delivered: 1, message: '' } }],
      'GET /api/v1/documents': [{ status: 200, body: [document({}, [{ ...GRANT, revoked_at: '2026-11-05T03:00:00Z' }])] }],
    };
    render(<DocumentsPanel me={makeMe()} initial={[document({}, [GRANT])]} />);

    expect(screen.getByText('Dibagikan hanya kepada Mitra A, hanya versi 1.')).toBeInTheDocument();
    const opener = screen.getByRole('button', { name: /Cabut akses\s*Mitra A/ });
    await user.click(opener);
    const dialog = screen.getByRole('dialog', { name: 'Cabut akses Mitra A?' });
    expect(within(dialog).getByRole('heading', { name: 'Cabut akses Mitra A?' })).toHaveFocus();
    expect(dialog).toHaveTextContent('Salinan yang sudah diunduh sebelumnya tidak dapat ditarik kembali.');

    await user.click(within(dialog).getByRole('button', { name: 'Batal' }));
    expect(opener).toHaveFocus();

    await user.click(opener);
    await user.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cabut akses' }));

    expect(await screen.findByText(/Akses Mitra A dicabut. Unduhan baru diblokir/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText('Unggah dokumen bukti')).toHaveFocus());
  });

  it('closes on Escape without revoking', async () => {
    const user = userEvent.setup();
    render(<DocumentsPanel me={makeMe()} initial={[document({}, [GRANT])]} />);

    await user.click(screen.getByRole('button', { name: /Cabut akses\s*Mitra A/ }));
    act(() => {
      fireEvent(screen.getByRole('dialog'), new Event('cancel', { cancelable: true }));
    });

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
