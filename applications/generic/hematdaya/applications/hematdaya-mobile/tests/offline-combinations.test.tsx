import { render, screen } from '@testing-library/react-native';

import type { Summary } from '@/api/client';
import { HDDataQuality, freshnessRows } from '@/components/hd/HDDataQuality';
import { SavedReadStatus } from '@/features/assets/ReadFailure';

it('shows the cached fetch and stale capture independently, with exact cadence', async () => {
  const freshness: Summary['source_freshness'] = [{
    source_id: 'router-source', asset_id: 'router', label: 'Router', origin: 'simulated', state: 'stale',
    last_capture_at: '2026-10-25T11:00:00Z', cadence_seconds: 3600, policy_version: 1, historical_range: null,
  }];
  await render(<>
    <SavedReadStatus offline fetchedAt={Date.parse('2026-10-26T08:00:00Z')} timezone="Asia/Jakarta" />
    <HDDataQuality rows={freshnessRows(freshness, 'Asia/Jakarta')} />
  </>);
  expect(screen.getByText('Offline · menampilkan data tersimpan')).toBeOnTheScreen();
  expect(screen.getByText(/26 Oktober 2026 15.00/)).toBeOnTheScreen();
  expect(screen.getByText(/25 Oktober 2026 18.00/)).toBeOnTheScreen();
  expect(screen.getByText(/Interval 1 jam/)).toBeOnTheScreen();
});

it('shows a historical capture and recorded range without a stale transport claim', async () => {
  await render(<HDDataQuality rows={freshnessRows([{
    source_id: 'csv', asset_id: 'dispenser', label: 'Dispenser', origin: 'import', state: 'historical',
    last_capture_at: '2026-10-20T17:00:00Z', cadence_seconds: 3600, policy_version: 1,
    historical_range: { start: '2026-10-20T11:00:00Z', end: '2026-10-20T17:00:00Z' },
  }], 'Asia/Jakarta')} />);
  expect(screen.getByText('Data historis · Impor CSV')).toBeOnTheScreen();
  expect(screen.getByText(/Pembacaan historis terakhir: 21 Oktober 2026 00.00/)).toBeOnTheScreen();
  expect(screen.queryByText(/Data belum diperbarui/)).toBeNull();
});
