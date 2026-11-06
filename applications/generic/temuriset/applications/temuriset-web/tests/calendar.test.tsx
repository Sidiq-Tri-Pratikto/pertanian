import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { CalendarConnection } from '@/views/settings/CalendarConnection';

const refresh = vi.fn();
vi.mock('next/navigation', () => ({ useRouter: () => ({ refresh }) }));

const fetchMock = vi.fn<(path: string, options?: RequestInit) => Promise<Response>>();

beforeEach(() => {
  fetchMock.mockReset();
  refresh.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

function reply(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

describe('local calendar connection in S18', () => {
  it('requires explicit read-only consent and provides the safe next navigation', async () => {
    fetchMock.mockResolvedValue(reply({ state: 'pending', version: 1, authorization_path: '/api/v1/me/calendar/connect' }));
    const { container } = render(<CalendarConnection initial={{ state: 'disconnected', version: 0 }} />);

    const connect = screen.getByRole('button', { name: 'Siapkan sambungan kalender' });
    expect(connect).toHaveAttribute('aria-disabled', 'true');
    await userEvent.click(connect);
    expect(fetchMock).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('checkbox', { name: /Saya setuju TemuRiset membaca waktu sibuk atau kosong/ }));
    await userEvent.click(screen.getByRole('button', { name: 'Siapkan sambungan kalender' }));

    expect(await screen.findByRole('link', { name: 'Lanjut ke kalender uji' })).toHaveAttribute('href', '/api/v1/me/calendar/connect?version=1');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/me/calendar/connect', expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      body: JSON.stringify({ expected_version: 0, consent: true }),
    }));
    expect((await axe.run(container)).violations).toEqual([]);
  });

  it('shows confirmed provider revocation from owner status after local disconnect', async () => {
    fetchMock
      .mockResolvedValueOnce(reply({ state: 'disconnected', version: 3, revocation: 'unconfirmed' }))
      .mockResolvedValueOnce(reply({ state: 'disconnected', version: 3, revocation: 'confirmed' }));
    render(<CalendarConnection initial={{ state: 'connected', version: 2 }} />);

    await userEvent.click(screen.getByRole('button', { name: 'Putuskan sambungan kalender' }));

    expect(await screen.findByText('Kalender terputus. Akses juga sudah dicabut di kalender.')).toBeVisible();
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/v1/me/calendar/disconnect', expect.objectContaining({
      method: 'POST',
      headers: expect.objectContaining({ 'Idempotency-Key': expect.any(String) }),
      body: JSON.stringify({ expected_version: 2 }),
    }));
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/v1/me/calendar', expect.objectContaining({ cache: 'no-store' }));
  });

  it('hides default-off controls and permits local cleanup when the adapter was switched off', async () => {
    const { rerender } = render(<CalendarConnection key="off" initial={{ state: 'off', version: 0 }} />);
    expect(screen.queryByRole('region', { name: 'Kalender luar' })).not.toBeInTheDocument();

    fetchMock.mockResolvedValue(reply({ state: 'off', version: 3, revocation: 'unconfirmed' }));
    rerender(<CalendarConnection key="cleanup" initial={{ state: 'off_with_connection', version: 2 }} />);
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Putuskan sambungan kalender' }));

    expect(await screen.findByText(/Periksa pencabutan akses di pengaturan kalender Anda/)).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('keeps the connected state on a stale disconnect and shows the reference and refresh action', async () => {
    fetchMock.mockResolvedValue(reply({
      error: {
        code: 'STALE_VERSION', request_id: 'ref_test', message: 'Data sudah berubah. Muat ulang data terbaru.',
        recovery: { retryable: false },
      },
    }, 409));
    render(<CalendarConnection initial={{ state: 'connected', version: 2 }} />);
    await userEvent.click(screen.getByRole('button', { name: 'Putuskan sambungan kalender' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('ID referensi ref_test');
    expect(screen.getByRole('status')).toHaveTextContent('Kalender tersambung');
    await userEvent.click(screen.getByRole('button', { name: 'Muat status terbaru' }));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
  });
});
