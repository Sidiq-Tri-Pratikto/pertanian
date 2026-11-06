import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { readReportSubject, reportHref } from '@/features/privacy/model';
import { PrivacyRequests } from '@/views/settings/PrivacyRequests';
import { ReportForm } from '@/views/settings/ReportForm';

import { PERSONAL } from './fixtures';

const subjectId = '92d3a99e-3266-4e76-9252-72cc2b47ed9b';
const scope = { id: PERSONAL, label: 'Diri sendiri' };
const fetchMock = vi.fn<typeof fetch>();

const held = {
  id: 'deletion-1', version: 1, kind: 'DELETION' as const, status: 'RECEIVED' as const,
  created_at: '2026-11-05T08:00:00Z', fulfilled_at: null,
  policy_version: 'retention-1',
  answer: {
    to_remove: [{ key: 'private_documents', label: 'Isi berkas pribadi' }],
    removed: [],
    retained: [{ key: 'audit', label: 'Catatan audit', reason: 'Diperlukan untuk audit.', period: 'Sampai audit selesai' }],
    notice: 'Salinan yang sudah diunduh tidak dapat ditarik kembali.',
  },
};
const exported = { ...held, id: 'export-1', kind: 'EXPORT' as const, status: 'FULFILLED' as const };

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
});
afterEach(() => vi.unstubAllGlobals());

it('prefills an opaque pitch identifier without accepting a title from the URL', () => {
  expect(readReportSubject('PITCH', subjectId)).toEqual({ type: 'PITCH', id: subjectId });
  expect(readReportSubject('PITCH', 'bad')).toBeNull();
  expect(readReportSubject('UNKNOWN', subjectId)).toBeNull();
  expect(readReportSubject(undefined, undefined)).toBeNull();
  expect(reportHref('PITCH', subjectId)).toBe(`/settings?lapor=PITCH&objek=${subjectId}#laporkan`);
});

it('links the required reason error, then sends the versioned private report', async () => {
  const user = userEvent.setup();
  fetchMock.mockResolvedValueOnce(Response.json({ id: 'r1', case_number: 'TR-000001', status: 'RECEIVED' }, { status: 201 }));
  render(<ReportForm scope={scope} subject={{ type: 'PITCH', id: subjectId }} initial={{ data: [], failure: null }} />);
  await user.click(screen.getByRole('button', { name: 'Kirim laporan' }));
  expect(fetchMock).not.toHaveBeenCalled();
  expect(screen.getByRole('group', { name: 'Masih ada yang perlu diperbaiki' })).toHaveFocus();
  await user.type(screen.getByRole('textbox', { name: /Alasan laporan/ }), 'Ada dugaan penyamaran');
  await user.click(screen.getByRole('button', { name: 'Kirim laporan' }));
  await screen.findByText('Laporan TR-000001 diterima.');
  const [path, request] = fetchMock.mock.calls[0];
  expect(path).toBe('/api/v1/reports');
  expect(request?.headers).toMatchObject({ 'Idempotency-Key': expect.any(String) });
  expect(JSON.parse(String(request?.body))).toMatchObject({
    acting_party_id: PERSONAL, expected_version: null, subject_type: 'PITCH', subject_id: subjectId,
    reason: 'Ada dugaan penyamaran',
  });
});

it('preserves the report draft and retries the same intent with the same key', async () => {
  const user = userEvent.setup();
  fetchMock.mockRejectedValueOnce(new TypeError('offline'));
  fetchMock.mockResolvedValueOnce(Response.json({ id: 'r1', case_number: 'TR-000001', status: 'RECEIVED' }, { status: 201 }));
  render(<ReportForm scope={scope} subject={null} initial={{ data: [], failure: null }} />);
  const reason = screen.getByRole('textbox', { name: /Alasan laporan/ });
  await user.type(reason, 'Salah satu klaim perlu diperiksa');
  await user.click(screen.getByRole('button', { name: 'Kirim laporan' }));
  await screen.findByText(/Layanan belum dapat dihubungi/);
  expect(reason).toHaveValue('Salah satu klaim perlu diperiksa');
  await user.click(screen.getByRole('button', { name: 'Kirim laporan' }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(fetchMock.mock.calls[1][1]?.headers).toEqual(fetchMock.mock.calls[0][1]?.headers);
});

it('confirms a deletion, then renders the reasons returned by the service', async () => {
  const user = userEvent.setup();
  fetchMock.mockResolvedValueOnce(Response.json(held, { status: 201 }));
  render(<PrivacyRequests scope={scope} initial={{ data: [], failure: null }} />);
  await user.click(screen.getByRole('button', { name: 'Minta penghapusan data' }));
  expect(fetchMock).not.toHaveBeenCalled();
  await user.click(screen.getByRole('button', { name: 'Ajukan penghapusan' }));
  expect(await screen.findByText(/Diperlukan untuk audit/)).toBeVisible();
  expect(screen.getByText('Akan dihapus')).toBeVisible();
  expect(screen.queryByText('Sudah dihapus')).not.toBeInTheDocument();
  expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({
    kind: 'DELETION', acting_party_id: PERSONAL, expected_version: null,
  });
});

it('renders a denied fresh download without replacing the settings page', async () => {
  const user = userEvent.setup();
  fetchMock.mockResolvedValueOnce(Response.json({
    error: { code: 'NOT_FOUND', message: 'Ekspor tidak tersedia. Muat ulang daftar permintaan.', request_id: 'ref_export', recovery: { retryable: false } },
  }, { status: 404 }));
  render(<PrivacyRequests scope={scope} initial={{ data: [exported], failure: null }} />);
  await user.click(screen.getByRole('button', { name: 'Unduh ekspor' }));
  expect(await screen.findByText(/ref_export/)).toBeVisible();
  expect(screen.getByRole('heading', { name: 'Permintaan privasi' })).toBeVisible();
  expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/privacy-requests/export-1/export');
});

it('provides accessible names and controls for reporting and privacy', async () => {
  const { container } = render(<main>
    <ReportForm scope={scope} subject={null} initial={{ data: [], failure: null }} />
    <PrivacyRequests scope={scope} initial={{ data: [held], failure: null }} />
  </main>);
  let result: axe.AxeResults | undefined;
  await act(async () => {
    result = await axe.run(container, { rules: { 'color-contrast': { enabled: false } } });
  });
  expect(result?.violations).toEqual([]);
});
