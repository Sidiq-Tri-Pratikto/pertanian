import { useState } from 'react';
import { AccessibilityInfo } from 'react-native';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import type { AssetDetail } from '@/api/client';
import { ApiError } from '@/api/errors';
import { createAssetDraft, EditAssetSheet, type AssetDraft } from '@/features/assets/EditAssetSheet';
import type { AssetWriteState } from '@/features/assets/useAssetMutations';

const asset: AssetDetail = {
  id: 'asset', name: 'Kulkas', category: null, location: 'Dapur', archived: false,
  scope_kind: 'device', parent_asset_id: null, expected_use: 'unknown', bindings: [], sources: [],
};
const field = (name: string) => screen.getByLabelText(name);
const save = () => fireEvent.press(screen.getByRole('button', { name: 'Simpan' }));

async function edit(state?: AssetWriteState, initial = createAssetDraft(asset)) {
  const submit = jest.fn();
  const discard = jest.fn();
  const review = jest.fn();
  function Harness() {
    const [draft, setDraft] = useState<AssetDraft>(initial);
    const [current, setCurrent] = useState(state);
    return <EditAssetSheet open draft={draft} onDraft={setDraft} onClose={() => undefined} onDiscard={discard}
      onSubmit={submit} state={current} blocked={current?.kind === 'diverged'}
      onReview={() => { review(); if (current?.kind === 'diverged') setCurrent({ ...current, kind: 'reviewed' }); }} />;
  }
  await render(<Harness />);
  return { submit, discard, review };
}

it('focuses the summary for a blank name and links to the invalid field', async () => {
  const focus = jest.spyOn(AccessibilityInfo, 'sendAccessibilityEvent').mockImplementation(() => undefined);
  const { submit } = await edit();
  const initialFocus = focus.mock.calls.length;
  await fireEvent.changeText(field('Nama perangkat'), '   ');
  await save();
  expect(screen.getByLabelText('Periksa 1 hal berikut').props.role).toBe('alert');
  const link = screen.getByRole('link', { name: /Nama perangkat.*Isi nama perangkat/ });
  await waitFor(() => expect(focus.mock.calls.length).toBeGreaterThan(initialFocus));
  const summaryFocus = focus.mock.calls.length;
  await fireEvent.press(link);
  expect(focus.mock.calls.length).toBeGreaterThan(summaryFocus);
  expect(submit).not.toHaveBeenCalled();
  focus.mockRestore();
});

it.each([['Nama perangkat', 'name'], ['Kategori', 'category'], ['Lokasi', 'location']])(
  'validates %s after trimming, by Unicode code point', async (label, key) => {
    const { submit } = await edit();
    const value = '🧊'.repeat(60);
    await fireEvent.changeText(field(label), `  ${value}🧊  `);
    await save();
    expect(screen.getByRole('link', { name: /paling banyak 60 karakter/ })).toBeOnTheScreen();
    expect(submit).not.toHaveBeenCalled();
    await fireEvent.changeText(field(label), `  ${value}  `);
    await save();
    expect(submit).toHaveBeenCalledWith({ [key]: value });
  },
);

it('omits untouched nullable fields and whitespace-only changes, but sends an explicit optional clear', async () => {
  const { submit, discard } = await edit();
  await fireEvent.changeText(field('Nama perangkat'), ' Kulkas ');
  await fireEvent.changeText(field('Kategori'), '  ');
  await save();
  expect(submit).not.toHaveBeenCalled();
  await fireEvent.changeText(field('Lokasi'), '   ');
  await save();
  expect(submit).toHaveBeenCalledWith({ location: '' });
  await fireEvent.press(screen.getByRole('button', { name: 'Buang draf' }));
  expect(discard).toHaveBeenCalledTimes(1);
});

it('shows safe validation links and the reference on a known refusal', async () => {
  await edit({
    kind: 'refused', changes: { name: 'Draf' },
    error: new ApiError('VALIDATION_FAILED', 'Isian belum valid. Perbaiki isian.', { retryable: false }, 'ref-edit', [
      { loc: ['body', 'name'], msg: 'Nama tidak valid.', type: 'string_too_long' },
      { loc: ['body', 'unknown'], msg: 'FAKE_SECRET', type: 'string_too_long' },
    ]),
  }, { ...createAssetDraft(asset), values: { name: 'Draf', category: '', location: 'Dapur' } });
  expect(screen.getByRole('link', { name: /Nama perangkat.*Nama tidak valid/ })).toBeOnTheScreen();
  expect(screen.getByText(/ref-edit/)).toBeOnTheScreen();
  expect(screen.queryByText('FAKE_SECRET')).toBeNull();
});

it('rebases the reviewed intent over fresh values without resending an untouched concurrent field', async () => {
  const { submit, review } = await edit({
    kind: 'diverged', changes: { name: 'Draf' },
    error: ApiError.unreachable(),
    observed: { ...asset, name: 'Nama serentak', category: 'Pendingin', location: 'Garasi' },
  }, {
    baseline: createAssetDraft(asset).baseline,
    values: { name: 'Draf', category: '  ', location: ' Dapur ' },
    touched: { name: true, category: true, location: true },
  });
  expect(screen.getByText(/Saat diperiksa: Nama serentak, kategori Pendingin, lokasi Garasi/)).toBeOnTheScreen();
  expect(screen.getByLabelText('Nama perangkat').props.value).toBe('Draf');
  await fireEvent.press(screen.getByRole('button', { name: 'Tinjau data terkini' }));
  expect(review).toHaveBeenCalledTimes(1);
  expect(field('Kategori').props.value).toBe('Pendingin');
  expect(field('Lokasi').props.value).toBe('Garasi');
  await save();
  expect(submit).toHaveBeenCalledWith({ name: 'Draf' });
});

it('uses the service whitespace boundary for an exact Unicode acknowledgment', async () => {
  const { submit } = await edit();
  await fireEvent.changeText(field('Nama perangkat'), '\u0085\ufeffKulkas\u0085');
  await save();
  expect(submit).toHaveBeenCalledWith({ name: '\ufeffKulkas' });
});
