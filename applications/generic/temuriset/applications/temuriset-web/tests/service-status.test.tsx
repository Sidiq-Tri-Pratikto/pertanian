import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { readFailure, ApiError } from '@/api/errors';
import { ServiceStatus } from '@/features/ServiceStatus';

const MANIFEST = { schema_version: 1, source_release: '0.1.0' };

function respond(status: number, body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ServiceStatus', () => {
  it('says the service answers and names the release', async () => {
    const fetchMock = vi.fn(() => respond(200, MANIFEST));
    vi.stubGlobal('fetch', fetchMock);

    render(<ServiceStatus />);

    expect(await screen.findByText('Layanan tersedia')).toBeInTheDocument();
    expect(screen.getByText(/Versi 0\.1\.0/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/capabilities', expect.objectContaining({ cache: 'no-store' }));
  });

  it('explains an unreachable service and retries on request', async () => {
    const fetchMock = vi.fn().mockRejectedValueOnce(new TypeError('offline')).mockImplementation(() => respond(200, MANIFEST));
    vi.stubGlobal('fetch', fetchMock);

    render(<ServiceStatus />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Layanan belum dapat dihubungi');
    await userEvent.click(screen.getByRole('button', { name: 'Coba lagi' }));

    expect(await screen.findByText('Layanan tersedia')).toBeInTheDocument();
  });

  it('shows the service message and reference without a retry for a final failure', async () => {
    const envelope = {
      error: { code: 'INTERNAL_ERROR', message: 'Permintaan belum dapat diselesaikan.', request_id: 'ref-1', recovery: { retryable: false } },
    };
    vi.stubGlobal('fetch', vi.fn(() => respond(500, envelope)));

    render(<ServiceStatus />);

    expect(await screen.findByText('Permintaan belum dapat diselesaikan.')).toBeInTheDocument();
    expect(screen.getByText('ID referensi: ref-1')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Coba lagi' })).toBeNull();
  });
});

describe('readFailure', () => {
  it('never leaks a body that is not the envelope', async () => {
    const error = await readFailure(new Response('<html>stack trace</html>', { status: 502 }));

    expect(error.code).toBe('UNEXPECTED_RESPONSE');
    expect(error.message).not.toContain('stack');
  });

  it('normalizes anything caught at a call site', () => {
    const known = ApiError.unreachable();

    expect(ApiError.from(known)).toBe(known);
    expect(ApiError.from(new Error('boom')).code).toBe('UNEXPECTED_RESPONSE');
  });
});
