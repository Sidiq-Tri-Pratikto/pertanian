import { useCopy } from '@/features/localization/messages';
import { useId, useState } from 'react';
import { StyleSheet, useWindowDimensions, View } from 'react-native';
import Svg, { Defs, Line, Path, Pattern, Rect } from 'react-native-svg';

import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { formatDecimal } from '@/lib/format';

export type HistoryPoint = {
  id?: string;
  label: string;
  current: string | null;
  reference?: string | null;
  /** The live asset states are absent for S08's frozen comparison mask. */
  state?: 'measured' | 'partial' | 'missing' | 'future' | 'unavailable';
};

type HDHistoryChartProps = {
  title: string;
  points: HistoryPoint[];
  periodLabel: string;
  scopeLabel: string;
  unit: string;
  summary: string;
  gapNote?: string;
  /** Sparse axes omit per-bar values. */
  dense?: boolean;
  showValues?: boolean;
};

const { color, size } = tokens;
const baseline = size.chartPlotHeight - size.strokeChart;
const headroom = 1.2;
const referenceDash = '4 3';
const gapDash = '1 3';
const hatch = 'M-1 1 L1 -1 M0 6 L6 0 M5 7 L7 5';

function barHeight(value: string, max: number): number {
  return max === 0 ? 0 : (Number(value) / max) * baseline / headroom;
}

type AxisLabel = { id: string | number; label: string; left: number; width: number };

/** Stagger labels that would otherwise overlap, keeping each one near its own tick. */
function axisRows(points: HistoryPoint[], width: number, fontScale: number): AxisLabel[][] {
  const lanes: AxisLabel[][] = [];
  points.forEach((point, index) => {
    if (!point.label) return;
    const textWidth = Math.min(width, Math.max(20, point.label.length * 8 * fontScale));
    const center = (index + 0.5) * width / points.length;
    const left = Math.min(width - textWidth, Math.max(0, center - textWidth / 2));
    const label = { id: point.id ?? index, label: point.label, left, width: textWidth };
    const lane = lanes.find((row) => {
      const previous = row[row.length - 1];
      return previous.left + previous.width + 4 <= left;
    });
    if (lane) lane.push(label);
    else lanes.push([label]);
  });
  return lanes;
}

/** Plot the current series and, when supplied, its aligned frozen reference on one zero baseline. */
export function HDHistoryChart({
  title, points, periodLabel, scopeLabel, unit, summary, gapNote, dense = false, showValues = true,
}: HDHistoryChartProps) {
  const say = useCopy();
  const [width, setWidth] = useState(288);
  const { fontScale } = useWindowDimensions();
  const hasReference = points.some((point) => point.reference !== undefined);
  const states = new Set(points.map((point) => point.state));
  const hatchId = `history-gap-${useId().replace(/[^a-zA-Z0-9_-]/g, '_')}`;
  const max = Math.max(0, ...points.flatMap((point) => [point.current, point.reference]).map((value) => Number(value ?? 0)));
  const step = width / Math.max(points.length, 1);
  const barWidth = Math.min(size.chartBarThickness, step / (hasReference ? 2.7 : 1.35));

  return (
    <View style={styles.block}>
      <HDText variant="section" role="heading">{title}</HDText>
      <HDText variant="label" tone="secondary">{periodLabel} · {scopeLabel} · {unit}</HDText>
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View aria-hidden style={[styles.swatch, styles.current]} />
          <HDText variant="label">{say("Periode ini", "This period")}</HDText>
        </View>
        {hasReference ? (
          <View style={styles.legendItem}>
            <View aria-hidden style={[styles.swatch, styles.reference]} />
            <HDText variant="label">{say("Pembanding (median)", "Comparison (median)")}</HDText>
          </View>
        ) : null}
        {states.has('partial') ? <LegendMark label={say("Data sebagian", "Partial data")} path="M6 1 L11 6 L6 11 L1 6 Z" stroke={color.chartCurrent} /> : null}
        {states.has('missing') ? <LegendMark label={say("Tidak ada data", "No data")} path="M1 5 L5 1 M1 11 L11 1 M7 11 L11 7" stroke={color.chartMissingMarker} /> : null}
        {states.has('unavailable') ? <LegendMark label={say("Data tidak tersedia", "Data unavailable")} path="M2 2 L10 10 M10 2 L2 10" stroke={color.chartMissingMarker} /> : null}
        {states.has('future') ? <HDText variant="label">{say("Belum terjadi (kolom kosong)", "Future period (blank column)")}</HDText> : null}
      </View>
      <HDText variant="label" tone="secondary">{say("Skala mulai dari 0", "Scale starts at 0")} {unit}.</HDText>
      <View
        accessible
        role="img"
        aria-label={`${title}. ${summary}`}
        onLayout={(event) => setWidth(event.nativeEvent.layout.width || 288)}>
        <View aria-hidden importantForAccessibility="no-hide-descendants">
          <Svg width="100%" height={size.chartPlotHeight}>
            {states.has('missing') ? (
              <Defs>
                <Pattern id={hatchId} width={6} height={6} patternUnits="userSpaceOnUse">
                  <Path d={hatch} fill="none" stroke={color.chartMissingMarker} strokeWidth={1.5} />
                </Pattern>
              </Defs>
            ) : null}
            <Line x1={0} x2={width} y1={baseline} y2={baseline} stroke={color.chartBaseline} strokeWidth={size.strokeChart} />
            {points.map((point, index) => {
              const center = (index + 0.5) * step;
              const x = hasReference ? center - barWidth - 1 : center - barWidth / 2;
              const currentHeight = point.current === null ? 0 : barHeight(point.current, max);
              const referenceHeight = point.reference == null ? 0 : barHeight(point.reference, max);
              return (
                <SvgMarks
                  key={point.id ?? index}
                  point={point}
                  x={x}
                  center={center}
                  barWidth={barWidth}
                  currentHeight={currentHeight}
                  referenceHeight={referenceHeight}
                  hatchId={hatchId}
                />
              );
            })}
          </Svg>
          {axisRows(points, width, fontScale).map((row, index) => (
            <View key={index} style={styles.axisRow}>
              {row.map(({ id, label, left, width: labelWidth }, column) => {
                const previous = row[column - 1];
                return (
                  <HDText key={id} variant="label" style={[styles.center, { width: labelWidth, marginLeft: previous ? left - previous.left - previous.width : left }]}>
                    {label}
                  </HDText>
                );
              })}
            </View>
          ))}
          {showValues && !dense && step >= 64 * fontScale ? (
            <View style={styles.axisRow}>
              {points.map((point, index) => (
                <HDText key={point.id ?? index} variant="label" tone="secondary" style={[styles.center, { flex: 1 }]}>
                  {point.current === null ? '—' : formatDecimal(point.current)}
                </HDText>
              ))}
            </View>
          ) : null}
        </View>
      </View>
      <HDText>{summary}</HDText>
      {gapNote ? <HDText variant="label">{gapNote}</HDText> : null}
    </View>
  );
}

function LegendMark({ label, path, stroke }: { label: string; path: string; stroke: string }) {
  return (
    <View style={styles.legendItem}>
      <View aria-hidden>
        <Svg width={tokens.space['12']} height={tokens.space['12']} viewBox="0 0 12 12">
          <Path d={path} stroke={stroke} strokeWidth={1.5} fill="none" />
        </Svg>
      </View>
      <HDText variant="label">{label}</HDText>
    </View>
  );
}

type MarksProps = {
  point: HistoryPoint;
  x: number;
  center: number;
  barWidth: number;
  currentHeight: number;
  referenceHeight: number;
  hatchId: string;
};

function SvgMarks({ point, x, center, barWidth, currentHeight, referenceHeight, hatchId }: MarksProps) {
  return (
    <>
      {point.label ? <Line x1={center} x2={center} y1={baseline} y2={size.chartPlotHeight} stroke={color.chartBaseline} /> : null}
      <CurrentMark point={point} x={x} barWidth={barWidth} currentHeight={currentHeight} hatchId={hatchId} />
      {point.reference != null ? (
        <Rect testID="chart-reference" x={center + 1} y={baseline - Math.max(referenceHeight, size.strokeChart)}
          width={barWidth} height={Math.max(referenceHeight, size.strokeChart)}
          fill={color.chartReferenceFill} stroke={color.chartReference} strokeWidth={size.strokeChart}
          strokeDasharray={referenceDash} />
      ) : null}
    </>
  );
}

function CurrentMark({ point, x, barWidth, currentHeight, hatchId }: Omit<MarksProps, 'center' | 'referenceHeight'>) {
  const measuredHeight = Math.max(currentHeight, size.strokeChart);
  const center = x + barWidth / 2;
  const radius = Math.min(4, barWidth / 2);
  if (point.state === 'future') return null;
  if (point.state === 'unavailable') {
    return (
      <Path testID="chart-unavailable"
        d={`M${center - radius} ${baseline - 9} L${center + radius} ${baseline - 1} M${center + radius} ${baseline - 9} L${center - radius} ${baseline - 1}`}
        fill="none" stroke={color.chartMissingMarker} strokeWidth={size.strokeChart} />
    );
  }
  if (point.state === 'partial') {
    const markerY = baseline - measuredHeight - radius;
    const positive = Number(point.current) > 0;
    return (
      <>
        {positive ? (
          <Rect testID="chart-partial" x={x} y={baseline - measuredHeight} width={barWidth} height={measuredHeight}
            fill={color.chartCurrent} />
        ) : null}
        <Path testID="chart-partial-marker"
          d={`M${center} ${markerY - radius} L${center + radius} ${markerY} L${center} ${markerY + radius} L${center - radius} ${markerY} Z`}
          fill={color.backgroundSurface} stroke={color.chartCurrent} strokeWidth={1.5} />
      </>
    );
  }
  if (point.current === null) {
    const missing = point.state === 'missing';
    return (
      <Rect testID={missing ? 'chart-missing' : 'chart-gap'} x={x} y={size.strokeChart}
        width={barWidth} height={baseline - size.strokeChart} fill={missing ? `url(#${hatchId})` : 'none'}
        stroke={color.chartMissingMarker} strokeWidth={size.strokeChart} strokeDasharray={missing ? undefined : gapDash} />
    );
  }
  return (
    <Rect testID={Number(point.current) === 0 ? 'chart-zero' : 'chart-current'} x={x}
      y={baseline - measuredHeight} width={barWidth} height={measuredHeight} fill={color.chartCurrent} />
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stackTight },
  legend: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.stack, alignItems: 'center' },
  legendItem: { flexDirection: 'row', alignItems: 'center', gap: tokens.space['4'], flexShrink: 1 },
  swatch: { width: tokens.space['12'], height: tokens.space['12'] },
  current: { backgroundColor: color.chartCurrent },
  reference: {
    backgroundColor: color.chartReferenceFill,
    borderWidth: size.strokeChart,
    borderStyle: 'dashed',
    borderColor: color.chartReference,
  },
  axisRow: { flexDirection: 'row' },
  center: { textAlign: 'center' },
});
