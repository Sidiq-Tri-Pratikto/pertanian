import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axe from 'axe-core';

import { ApiError } from '@/api/errors';
import {
  changeImport, createExport, downloadExport, readExport, readImport, validateImport, type ExportStatus, type ImportStatus,
} from '@/features/portability/api';
import { PortabilityView } from '@/views/PortabilityView';

import { makeMe, ORGANIZATION_PARTY } from './fixtures';

const refresh = vi.fn();
vi.mock('next/navigation', () => ({ useRouter: () => ({ refresh }) }));
vi.mock('@/features/actions', () => ({ forgetPersona: async () => {} }));
vi.mock('@/features/portability/api', () => ({
  changeImport: vi.fn(), createExport: vi.fn(), downloadExport: vi.fn(),
  readExport: vi.fn(), readImport: vi.fn(), validateImport: vi.fn(),
}));

const stage = (status: ImportStatus['validation']['status'], processed = 0) => ({ status, processed });
const PENDING: ImportStatus = {
  id: 'import-1', version: 1, validation: stage('PENDING'), preview: stage('NOT_STARTED'), apply: stage('NOT_STARTED'),
  total: 0, committed: 0, skipped: 0, expires_at: '2026-11-06T02:00:00Z',
};
const PREVIEW: ImportStatus = {
  ...PENDING, version: 2, total: 1, validation: stage('SUCCEEDED', 1), preview: stage('SUCCEEDED', 1),
  rows: [{
    external_id: 'inventor-source', resource: 'INVENTION', action: 'CONFLICT',
    mapped_fields: ['title'], skipped_fields: ['private_notes'], conflicts: ['facts'],
  }],
};
const EXPORT: ExportStatus = { id: 'export-1', status: 'PENDING', expires_at: '2026-11-06T02:00:00Z' };
const me = makeMe({ organization: true, actingAsOrganization: true });
const denied = new ApiError('FORBIDDEN', 'Izin tidak tersedia. Periksa akses Anda.', { retryable: false }, 'ref_demo');

beforeEach(() => {
  vi.resetAllMocks();
});

describe('workspace portability', () => {
  it('keeps the file and operation key after an upload error, then requires reviewed preview before apply', async () => {
    const user = userEvent.setup();
    vi.mocked(validateImport).mockRejectedValueOnce(denied).mockResolvedValueOnce(PENDING);
    vi.mocked(readImport).mockResolvedValueOnce(PREVIEW);
    vi.mocked(changeImport).mockResolvedValueOnce({ ...PREVIEW, version: 3, rows: [], apply: stage('PENDING') });
    render(<PortabilityView me={me} inventions={[]} />);
    const file = new File(['{}'], 'sumber.json', { type: 'application/json' });
    const input = screen.getByLabelText('Berkas JSON');
    await user.upload(input, file);
    await user.click(screen.getByRole('checkbox', { name: 'Petakan catatan privat ke draf' }));
    await user.click(screen.getByRole('button', { name: 'Validasi berkas' }));
    expect(await screen.findByText('Kode rujukan ref_demo.')).toBeInTheDocument();
    expect((input as HTMLInputElement).files?.[0]).toBe(file);
    await user.click(screen.getByRole('button', { name: 'Validasi berkas' }));
    expect(vi.mocked(validateImport).mock.calls[0]).toEqual(vi.mocked(validateImport).mock.calls[1]);
    expect(vi.mocked(validateImport).mock.calls[1]?.slice(0, 3)).toEqual([file, ORGANIZATION_PARTY, true]);
    expect(await screen.findByText(/Validasi · Sedang diproses/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Terapkan impor' })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Periksa status impor' }));
    expect(await screen.findByText('Fakta yang dilindungi berbeda.')).toBeInTheDocument();
    const apply = screen.getByRole('button', { name: 'Terapkan impor' });
    expect(apply).toHaveAttribute('aria-disabled', 'true');
    await user.click(screen.getByRole('checkbox', { name: 'Saya sudah meninjau pratinjau' }));
    await user.click(screen.getByRole('button', { name: 'Terapkan impor' }));
    expect(changeImport).toHaveBeenCalledWith('import-1', 'apply', ORGANIZATION_PARTY, 2, expect.any(String));
    expect(await screen.findByText(/Penerapan · Sedang diproses/)).toBeInTheDocument();
    expect(screen.getByText('Fakta yang dilindungi berbeda.')).toBeInTheDocument();
  });

  it('reports committed work after cancellation', async () => {
    const user = userEvent.setup();
    vi.mocked(validateImport).mockResolvedValueOnce({ ...PREVIEW, apply: stage('PENDING', 1), committed: 1 });
    vi.mocked(changeImport).mockResolvedValueOnce({ ...PREVIEW, apply: stage('CANCELLED', 1), committed: 1 });
    render(<PortabilityView me={me} inventions={[]} />);
    await user.upload(screen.getByLabelText('Berkas JSON'), new File(['{}'], 'sumber.json', { type: 'application/json' }));
    await user.click(screen.getByRole('button', { name: 'Validasi berkas' }));
    await user.click(await screen.findByRole('button', { name: 'Batalkan impor' }));
    expect(changeImport).toHaveBeenCalledWith('import-1', 'cancel', ORGANIZATION_PARTY, 2, expect.any(String));
    expect(await screen.findByText(/Penerapan · Dibatalkan/)).toBeInTheDocument();
    expect(screen.getByText('1 tersimpan · 0 dilewati')).toBeInTheDocument();
  });

  it('keeps the selection and shows download denial and subsequent expiry', async () => {
    const user = userEvent.setup();
    vi.mocked(createExport).mockResolvedValueOnce(EXPORT);
    vi.mocked(readExport).mockResolvedValueOnce({ ...EXPORT, status: 'SUCCEEDED' })
      .mockResolvedValueOnce({ ...EXPORT, status: 'EXPIRED' });
    vi.mocked(downloadExport).mockRejectedValueOnce(denied);
    render(<PortabilityView me={me} inventions={[{
      id: 'invention-1', title: 'Saringan air', has_draft: true, status: 'DRAFT', version: 2, published_number: null,
    }]} />);
    const select = screen.getByLabelText('Versi inovasi');
    await user.selectOptions(select, 'DRAFT:invention-1');
    await user.click(screen.getByRole('button', { name: 'Siapkan ekspor' }));
    await user.click(await screen.findByRole('button', { name: 'Periksa status ekspor' }));
    await user.click(await screen.findByRole('button', { name: 'Unduh JSON' }));
    expect(await screen.findByText(/Izin tidak tersedia/)).toBeInTheDocument();
    expect(select).toHaveValue('DRAFT:invention-1');
    await user.click(screen.getByRole('button', { name: 'Periksa status ekspor' }));
    expect(await screen.findByText('Ekspor · Kedaluwarsa')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Unduh JSON' })).not.toBeInTheDocument();
  });

  it('has no axe violations in jsdom', async () => {
    const { container } = render(<PortabilityView me={me} inventions={[]} />);
    await act(async () => {
      const result = await axe.run(container, {
        rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } },
      });
      expect(result.violations.map(({ id, nodes }) => [id, nodes.map(({ target }) => target)])).toEqual([]);
    });
  });
});
