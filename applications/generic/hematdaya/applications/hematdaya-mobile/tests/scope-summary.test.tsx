import { render, screen } from '@testing-library/react-native';

import type { Summary } from '@/api/client';
import { HDScopeSummary } from '@/components/hd/HDScopeSummary';

import assets from './fixtures/assets.json';

const summary = assets['h-base'].summary as Summary;

it('labels physical scope and time completeness and keeps measured zero separate from unavailable energy', async () => {
  await render(<HDScopeSummary summary={{
    ...summary,
    energy_kwh: '0.000',
    assets: [
      { ...summary.assets[0], name: 'Kulkas', energy_kwh: null, energy_unavailable_reason: 'source_conflict',
        conflict_sources: [{ source_id: 'a', label: 'Sumber A', energy_kwh: '1.000' }, { source_id: 'b', label: 'Sumber B', energy_kwh: '1.000' }] },
    ],
  }} />);
  expect(screen.getByText(/Cakupan pengukuran:/)).toBeOnTheScreen();
  expect(screen.getByText(/Kelengkapan data:/)).toBeOnTheScreen();
  expect(screen.getByText('0,000 kWh')).toBeOnTheScreen();
  expect(screen.getByText(/Kulkas · Sumber bertentangan/)).toBeOnTheScreen();
  expect(screen.getByText('Sumber A · 1,000 kWh')).toBeOnTheScreen();
  expect(screen.getByText('Sumber B · 1,000 kWh')).toBeOnTheScreen();
});

it('explains overlap and exclusion while showing individual readings without a combined value', async () => {
  const conflict = assets['h-scope'].summary as Summary;
  await render(<HDScopeSummary summary={{
    ...conflict,
    scope: { ...conflict.scope, excluded: [
      { asset_id: 'old', name: 'Aset lama', reason: 'archived' },
      { asset_id: 'excluded', name: 'Cadangan', reason: 'not_selected' },
    ] },
  }} />);
  expect(screen.getByText('Total gabungan belum dapat dihitung')).toBeOnTheScreen();
  expect(screen.getByText('Meter utama · 10,000 kWh')).toBeOnTheScreen();
  expect(screen.getByText('Pompa Air · 0,300 kWh')).toBeOnTheScreen();
  expect(screen.getByText('Aset lama · Diarsipkan')).toBeOnTheScreen();
  expect(screen.getByText('Cadangan · Di luar pilihan')).toBeOnTheScreen();
  expect(screen.queryByText('10,300 kWh')).toBeNull();
});
