import { StyleSheet, View } from 'react-native';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatDecimal } from '@/lib/format';

export type HistoryPoint = { label: string; current: string | null; reference?: string | null };

type HDHistoryChartProps = {
  title: string;
  points: HistoryPoint[];
  periodLabel: string;
  scopeLabel: string;
  unit: string;
  summary: string;
  gapNote?: string;
  /** Drops per-bar values for many columns, such as 24 hours. */
  dense?: boolean;
};

/** Bar length only; the value text always comes from the service string. */
function height(value: string | null | undefined, max: number): number {
  return value === null || value === undefined || max === 0 ? 0 : (Number(value) / max) * 100;
}

/**
 * Aligned bars: current filled, reference outlined and dashed, so they differ beyond colour. A gap is a marked
 * empty column, never a zero bar; a measured zero is a tick. No smoothing or inferred values.
 */
export function HDHistoryChart({ title, points, periodLabel, scopeLabel, unit, summary, gapNote, dense = false }: HDHistoryChartProps) {
  const hasReference = points.some((point) => point.reference !== undefined);
  const max = Math.max(0, ...points.flatMap((point) => [point.current, point.reference]).map((value) => Number(value ?? 0)));

  return (
    <View style={styles.block}>
      <HDText variant="section" role="heading">
        {title}
      </HDText>
      <HDText variant="label" tone="secondary">
        {periodLabel} · {scopeLabel} · {unit}
      </HDText>
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.swatch, styles.current]} />
          <HDText variant="label">Periode ini</HDText>
        </View>
        {hasReference ? (
          <View style={styles.legendItem}>
            <View style={[styles.swatch, styles.reference]} />
            <HDText variant="label">Pembanding (median)</HDText>
          </View>
        ) : null}
      </View>
      <HDText variant="label" tone="secondary">
        Skala mulai dari 0 {unit}.
      </HDText>
      <View accessible role="img" aria-label={`${title}. ${summary}`} style={styles.plot}>
        {points.map((point, index) => (
          <View key={index} style={styles.column}>
            <View style={styles.bars}>
              {point.current === null ? (
                <View testID="chart-gap" style={styles.gap} />
              ) : (
                <View style={[styles.bar, styles.current, { height: `${height(point.current, max)}%` }, point.current && Number(point.current) === 0 ? styles.tick : null]} />
              )}
              {hasReference ? (
                <View style={[styles.bar, styles.reference, { height: `${height(point.reference, max)}%` }]} />
              ) : null}
            </View>
            <HDText variant="label" style={styles.center}>
              {point.label}
            </HDText>
            {!dense ? (
              <HDText variant="label" tone="secondary" style={styles.center}>
                {point.current === null ? '—' : formatDecimal(point.current)}
              </HDText>
            ) : null}
          </View>
        ))}
      </View>
      <HDText>{summary}</HDText>
      {gapNote ? <HDText variant="label">{gapNote}</HDText> : null}
    </View>
  );
}

const { color, size } = tokens;

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.stack },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: tokens.space['4'] },
  swatch: { width: tokens.space['12'], height: tokens.space['12'] },
  plot: {
    flexDirection: 'row',
    gap: tokens.space['4'],
    borderBottomWidth: size.strokeChart,
    borderBottomColor: color.chartBaseline,
  },
  column: { flex: 1, minWidth: 0, gap: tokens.space['4'] },
  bars: { height: size.chartPlotHeight, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'center', gap: 2 },
  bar: { flex: 1, maxWidth: size.chartBarThickness },
  current: { backgroundColor: color.chartCurrent },
  reference: {
    backgroundColor: color.chartReferenceFill,
    borderWidth: size.strokeChart,
    borderStyle: 'dashed',
    borderColor: color.chartReference,
  },
  tick: { height: size.strokeChart },
  gap: {
    flex: 1,
    maxWidth: size.chartBarThickness,
    height: '100%',
    borderWidth: size.strokeChart,
    borderStyle: 'dotted',
    borderColor: color.chartMissingMarker,
  },
  center: { textAlign: 'center' },
});
