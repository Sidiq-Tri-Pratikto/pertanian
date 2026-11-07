import { render, screen } from '@testing-library/react-native';

import { HDHistoryChart, type HistoryPoint } from '@/components/hd/HDHistoryChart';
import { tokens } from '@/design/tokens.generated';

const hidden = { includeHiddenElements: true };

function plot(points: HistoryPoint[]) {
  return render(<HDHistoryChart
    title="Riwayat energi" points={points} periodLabel="19–25 Oktober 2026 · Asia/Jakarta"
    scopeLabel="Kulkas" unit="kWh" summary="Energi tercatat tertinggi 1,200 kWh." dense
  />);
}

it('distinguishes every asset history state on one accessible zero-based plot', async () => {
  await plot([
    { label: '19', current: '1.200', state: 'measured' },
    { label: '20', current: '0.000', state: 'measured' },
    { label: '21', current: '1.100', state: 'partial' },
    { label: '22', current: '0.001', state: 'partial' },
    { label: '23', current: '0.000', state: 'partial' },
    { label: '24', current: null, state: 'missing' },
    { label: '25', current: null, state: 'future' },
    { label: '26', current: null, state: 'unavailable' },
  ]);

  expect(screen.getAllByRole('img')).toHaveLength(1);
  expect(screen.getByRole('img', { name: /Riwayat energi.*1,200 kWh/ })).toBeOnTheScreen();
  expect(screen.getByText('Skala mulai dari 0 kWh.')).toBeOnTheScreen();
  expect(screen.getByTestId('chart-current', hidden).props.height).toBeCloseTo(
    (tokens.size.chartPlotHeight - tokens.size.strokeChart) / 1.2,
  );
  expect(screen.getByTestId('chart-zero', hidden).props.height).toBe(tokens.size.strokeChart);
  expect(screen.getAllByTestId('chart-partial', hidden)).toHaveLength(2);
  expect(screen.getAllByTestId('chart-partial-marker', hidden)).toHaveLength(3);
  expect(screen.getByTestId('chart-missing', hidden).props.fill).toMatchObject({ type: 1 });
  expect(screen.getByTestId('chart-unavailable', hidden)).toBeOnTheScreen();
  expect(screen.queryByTestId('chart-future', hidden)).toBeNull();
  expect(screen.getByText('Tidak ada data')).toBeOnTheScreen();
});

it('keeps the frozen current and dashed reference aligned, with a dotted gap', async () => {
  await plot([
    { label: '19', current: '1.200', reference: '1.200' },
    { label: '20', current: null, reference: null },
  ]);

  expect(screen.getAllByRole('img')).toHaveLength(1);
  const current = screen.getByTestId('chart-current', hidden);
  const reference = screen.getByTestId('chart-reference', hidden);
  expect(current.props.y).toBe(reference.props.y);
  expect(current.props.x).toBeLessThan(reference.props.x);
  expect(current.props.strokeDasharray).toBeUndefined();
  expect(reference.props.strokeDasharray).toEqual(['4', '3']);
  expect(screen.getByTestId('chart-gap', hidden).props.strokeDasharray).toEqual(['1', '3']);
  expect(screen.queryByTestId('chart-missing', hidden)).toBeNull();
});
