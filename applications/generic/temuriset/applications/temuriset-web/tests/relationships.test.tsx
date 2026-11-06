import axe from 'axe-core';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ApiError } from '@/api/errors';
import { PartnershipConsent } from '@/components/tr/PartnershipConsent';
import { RelationshipError } from '@/features/relationships/RelationshipError';
import type { Partnership } from '@/features/relationships/model';
import { PublicProfileView } from '@/views/relationships/PublicProfileView';

const relationship: Partnership = {
  id: 'relationship', pitch_id: 'pitch', type: 'PROJECT', contested: false, invention_ids: [],
  parties: [{ party_id: 'rani', name: 'Rani' }, { party_id: 'mitra', name: 'Mitra A' }],
  current: {
    number: 2, status: 'PENDING_COUNTERPARTY', values: { name: 'Uji lapangan' },
    ceiling: ['name', 'amount'], checksum: 'checksum', proposed_by_party_id: 'rani', note: '', created_at: '2026-12-01',
    confirmations: [{ party_id: 'mitra', subset: ['name'], confirmed_at: '2026-12-01' }],
  },
  versions: [], restrictions: [], effective: { version: null, fields: [], values: {} }, allowed_actions: ['confirm'],
};

it('keeps public consent opt-in and does not infer a public field from one confirmation', async () => {
  const toggle = vi.fn();
  const { container, rerender } = render(
    <PartnershipConsent record={relationship} actingPartyId="rani" selected={[]} onToggle={toggle} />,
  );
  expect(screen.getByText('Menunggu konfirmasi')).toBeVisible();
  expect(screen.queryByText('Dikonfirmasi kedua pihak')).not.toBeInTheDocument();
  expect(screen.getByRole('checkbox', { name: 'Nama Kerja Sama' })).not.toBeChecked();
  await userEvent.click(screen.getByRole('checkbox', { name: 'Nama Kerja Sama' }));
  expect(toggle).toHaveBeenCalledWith('name', true);
  expect(screen.queryByText('Tampil di publik')).not.toBeInTheDocument();
  expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } })).violations).toEqual([]);

  rerender(<PartnershipConsent record={{ ...relationship, current: {
    ...relationship.current, status: 'CONFIRMED',
    confirmations: [...relationship.current.confirmations, { party_id: 'rani', subset: ['name'], confirmed_at: '2026-12-01' }],
  } }} actingPartyId="rani" selected={['name']} onToggle={toggle} />);
  expect(screen.getByText('Dikonfirmasi kedua pihak')).toBeVisible();
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
  expect(screen.queryByText('Tampil di publik')).not.toBeInTheDocument();
});

it('renders only projected public fields and omits private counterpart links', async () => {
  const { container } = render(<PublicProfileView profile={{
    party_id: 'rani', name: 'Rani', bio: null, inventions: [], nothing_published: false,
    relationships: [{ id: 'relationship', role: 'Mitra proyek', counterpart_name: null,
      counterpart_party_id: null, fields: { scope: 'Validasi prototipe enam bulan' }, inventions: [] }],
  }} />);
  expect(screen.getByText('Validasi prototipe enam bulan')).toBeVisible();
  expect(screen.queryByText('Jumlah dana')).not.toBeInTheDocument();
  expect(screen.queryByRole('link', { name: 'Mitra A' })).not.toBeInTheDocument();
  expect((await axe.run(container, { rules: { 'color-contrast': { enabled: false }, region: { enabled: false }, 'landmark-unique': { enabled: false } } })).violations).toEqual([]);
});

it('focuses validation feedback and links it to the editable field', () => {
  const failure = new ApiError('VALIDATION_FAILED', 'Periksa cakupan', { retryable: false }, 'ref-j05', {
    details: [{ loc: ['body', 'values', 'scope'], msg: 'Cakupan wajib diisi.' }],
  });
  render(<RelationshipError error={{ failure, attempt: 1 }} prefix="ubah" />);

  expect(screen.getByRole('group', { name: 'Periksa cakupan' })).toHaveFocus();
  expect(screen.getByRole('link', { name: 'Cakupan wajib diisi.' })).toHaveAttribute('href', '#ubah-scope');
  expect(screen.getByText('ID referensi: ref-j05')).toBeVisible();
});
