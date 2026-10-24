// HematDaya Design System 1.0.0-draft — window.HD. Documentation types; the bundle is plain JS.
import type * as React from 'react';

type Node = React.ReactNode;
/** Display strings are Indonesian. Numbers are canonical JS numbers; HD formats them. */
export type Provenance = 'demo' | 'import' | 'live';

/* ---------- primitives ---------- */
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'text' | 'destructive';
  children: Node;
  onClick?: (e: React.MouseEvent) => void;
  type?: 'button' | 'submit';
  icon?: IconName;
  /** Shows a spinner and loadingLabel; clicks are ignored so a submit cannot be duplicated. Never announces success. */
  loading?: boolean;
  loadingLabel?: string;
  /** Non-empty = disabled. The control stays focusable (aria-disabled) and the reason is visible and linked. */
  disabledReason?: string | null;
  fullWidth?: boolean;
  id?: string; form?: string; describedBy?: string;
}
export declare function Button(props: ButtonProps): React.ReactElement;

export interface IconButtonProps {
  icon: IconName;
  /** Indonesian accessible name, e.g. "Tutup". Required. */
  label: string;
  /** Render the label next to the icon (recommended for unfamiliar icons). */
  showLabel?: boolean;
  /** Supplementary only; never the sole name. */
  tooltip?: string;
  onClick?: (e: React.MouseEvent) => void;
  disabledReason?: string | null;
}
export declare function IconButton(props: IconButtonProps): React.ReactElement;

interface FieldBase {
  label: string; id?: string; name?: string;
  help?: Node;
  /** Field-level message naming the correction. Sets aria-invalid. */
  error?: string | null;
  required?: boolean; optional?: boolean;
  disabledReason?: string | null;
}
export interface TextFieldProps extends FieldBase {
  value: string; onChange?: (value: string) => void; onBlur?: () => void;
  type?: 'text' | 'email' | 'date' | 'time' | 'search';
  multiline?: boolean; rows?: number;
  readOnly?: boolean;
  /** e.g. "Draf tersimpan di perangkat ini — belum dikirim". */
  draftNote?: string;
  placeholder?: string; autoComplete?: string;
}
export declare function TextField(props: TextFieldProps): React.ReactElement;

export interface ParsedDecimal { empty: boolean; valid: boolean; value: number | null; error?: string }
export interface NumericFieldProps extends FieldBase {
  /** Raw text as typed ("1,5"). Empty string stays empty: never coerced to 0. */
  value: string;
  onChange?: (text: string, parsed: ParsedDecimal) => void;
  unit?: string;
  allowNegative?: boolean; max?: number;
  /** Show parse/rule errors before blur (e.g. after submit). */
  showErrors?: boolean;
  note?: string;
}
export declare function NumericField(props: NumericFieldProps): React.ReactElement;

export interface ChoiceOption { value: string; label: string; description?: string; disabledReason?: string | null; id?: string }
export interface ChoiceGroupProps {
  type?: 'radio' | 'checkbox' | 'select';
  legend: string; options: ChoiceOption[];
  value: string | string[] | null;
  onChange?: (value: any) => void;
  help?: Node; error?: string | null; optional?: boolean; required?: boolean; inline?: boolean; placeholder?: string; id?: string;
}
/** Ordinary settings only — never an appliance on/off control. */
export declare function ChoiceGroup(props: ChoiceGroupProps): React.ReactElement;

export interface Period { preset: 'today' | 'last7' | 'range'; start: string; end: string }
export interface PeriodSelectorProps {
  /** Committed period (ISO dates, local Asia/Jakarta days). */
  value: Period;
  /** Presets commit when chosen; an explicit range commits only on "Terapkan". */
  onCommit: (p: Period) => void;
  /** Local "today" (virtual now in demos), ISO date. */
  today: string;
  label?: string; timezone?: string;
}
export declare function PeriodSelector(props: PeriodSelectorProps): React.ReactElement;

export interface TabNavigationProps {
  /** Exactly three destinations; a fourth cannot be added. */
  current: 'beranda' | 'perangkat' | 'saran';
  onNavigate?: (id: 'beranda' | 'perangkat' | 'saran') => void;
  hrefs?: Partial<Record<'beranda' | 'perangkat' | 'saran', string>>;
}
export declare function TabNavigation(props: TabNavigationProps): React.ReactElement;

export interface SheetDialogProps {
  open: boolean; title: string;
  /** Called for Escape/back ('escape') and the close button ('close'). Parent decides; draft stays unless parent clears it. */
  onClose: (reason: 'escape' | 'close') => void;
  children: Node; footer?: Node; closeLabel?: string;
}
/** Native <dialog> (modal): focus moves to the title (or [data-autofocus]), is contained, and returns to the opener. */
export declare function SheetDialog(props: SheetDialogProps): React.ReactElement;

export interface DisclosureProps { summary: string; children: Node; defaultOpen?: boolean; onToggle?: (e: React.SyntheticEvent) => void }
export declare function Disclosure(props: DisclosureProps): React.ReactElement;

export interface NoticeProps {
  tone?: 'info' | 'attention' | 'error' | 'success' | 'neutral';
  title: Node; children?: Node; action?: Node; icon?: IconName;
  /** Announce on render (role=status, or alert for error). Default off: persistent explanation, not a toast. */
  live?: boolean;
}
export declare function Notice(props: NoticeProps): React.ReactElement;

export interface ErrorSummaryProps {
  errors: { targetId: string; text: string }[];
  title?: string;
  /** e.g. "Nomor baris = baris data, tanpa header." */
  convention?: string;
  /** Increment on each submit to move focus to the summary again. */
  submitCount?: number;
  autoFocus?: boolean;
}
export declare function ErrorSummary(props: ErrorSummaryProps): React.ReactElement | null;

export interface ProgressStatusProps {
  state: null | 'loading' | 'saving' | 'unknown' | 'success' | 'failure';
  label?: string; detail?: string;
  onRetry?: () => void; onCheck?: () => void; checking?: boolean;
}
/** Always-present polite live region; never moves focus. */
export declare function ProgressStatus(props: ProgressStatusProps): React.ReactElement;

/* ---------- domain ---------- */
export interface EnergyMetricProps {
  /** Recorded kWh in scope. null/undefined with quality 'unavailable' shows no number. */
  kwh: number | null;
  quality?: 'complete' | 'partial' | 'unavailable';
  /** 0–1 temporal completeness, shown as "Kelengkapan data: 50% periode". */
  completeness?: number;
  gapLabel?: string;
  periodLabel: string; scopeLabel: string;
  provenance?: Provenance;
  label?: string; unit?: string; headingLevel?: 2 | 3 | 4;
  emptyAction?: Node; emptyDetail?: string; children?: Node;
}
export declare function EnergyMetric(props: EnergyMetricProps): React.ReactElement;

export interface CostEstimateProps {
  kwh: number | null;
  /** IDR per kWh. null = unknown cost (never Rp0); 0 = explicit zero tariff. */
  tariff: number | null;
  tariffSource?: 'synthetic' | 'user';
  partial?: boolean;
  onSetTariff?: () => void;
  headingLevel?: 2 | 3 | 4;
}
export declare function CostEstimate(props: CostEstimateProps): React.ReactElement;

export interface ScopeSummaryProps {
  included?: string[]; excluded?: string[]; count?: number; unitLabel?: string;
  overlap?: 'none' | 'parentChild' | 'unknown';
  parent?: { name: string; kwh: number; description?: string };
  child?: { name: string; kwh: number; description?: string };
  view?: 'parent' | 'child'; onViewChange?: (v: 'parent' | 'child') => void;
  /** Individual values shown when overlap is unknown; no combined total is rendered. */
  values?: { name: string; kwh: number }[];
}
export declare function ScopeSummary(props: ScopeSummaryProps): React.ReactElement;

export interface DataQualityProps {
  completeness?: number | null; gaps?: string;
  freshness?: { state: 'fresh' | 'stale' | 'historical'; lastMeasurement?: string; importRange?: string };
  client?: 'online' | 'offline'; cachedAge?: string;
  source?: Provenance;
  onCheckSource?: () => void; checkingSource?: boolean; onViewPeriod?: () => void; label?: string;
}
/** Temporal completeness, source freshness and client offline stay separate rows. No accuracy score. */
export declare function DataQuality(props: DataQualityProps): React.ReactElement;

export interface AssetRowProps {
  name: string; location?: string;
  kind: 'device' | 'circuit' | 'group' | 'meter';
  kwh: number | null;
  quality?: 'complete' | 'partial' | 'stale' | 'unavailable'; qualityLabel?: string;
  href?: string; onOpen?: () => void;
}
/** The whole row is one link; no nested buttons. Long names wrap. */
export declare function AssetRow(props: AssetRowProps): React.ReactElement;

export interface ContributionRankingProps {
  items: { name: string; kwh: number }[];
  title?: string; periodLabel?: string;
  /** Names the denominator, default "perangkat terukur yang dipilih". */
  denominatorLabel?: string; headingLevel?: 2 | 3 | 4;
}
export declare function ContributionRanking(props: ContributionRankingProps): React.ReactElement;

export interface HistoryPoint { label: string; current: number | null; reference?: number | null }
export interface HistoryChartProps {
  title: string; points: HistoryPoint[];
  periodLabel?: string; scopeLabel?: string; unit?: string;
  currentLabel?: string; referenceLabel?: string;
  /** Text summary resolving the same values as the bars. */
  summary: Node; gapNote?: string; headingLevel?: 2 | 3 | 4; children?: Node;
  /** Many points (e.g. 24 hours): thin gaps, tick labels only (give other points label ""), no per-bar values. */
  dense?: boolean;
}
/** null = no data (hatched, never zero). 0 = measured zero (baseline tick). */
export declare function HistoryChart(props: HistoryChartProps): React.ReactElement;

export interface ChartDataAlternativeProps {
  caption: string;
  columns: { key: string; label: string; numeric?: boolean; format?: (v: any) => string }[];
  rows: Record<string, any>[];
  summary?: Node; collapsed?: boolean; toggleLabel?: string;
}
export declare function ChartDataAlternative(props: ChartDataAlternativeProps): React.ReactElement;

export interface InsightSummaryProps {
  kind?: 'change' | 'learning' | 'none';
  title?: string; periodLabel?: string;
  comparison?: { eligible: true; label: string } | { eligible: false; reason: string };
  cause?: string; qualification?: string; detail?: string;
  onOpenEvidence?: () => void; evidenceLabel?: string; headingLevel?: 2 | 3 | 4;
}
export declare function InsightSummary(props: InsightSummaryProps): React.ReactElement;

export interface EvidencePanelProps {
  observed: Node; comparison?: Node; qualityScope?: Node; unknown?: Node; guidance?: Node;
  onFeedback?: (v: 'helpful' | 'notHelpful') => void;
  feedbackState?: null | 'saving' | 'success' | 'failure' | 'unknown'; feedbackChoice?: 'helpful' | 'notHelpful';
  onFeedbackRetry?: () => void; onFeedbackCheck?: () => void;
  metadata?: [string, Node][]; label?: string;
}
export declare function EvidencePanel(props: EvidencePanelProps): React.ReactElement;

export interface ImportPreviewProps {
  fileName: string; periodLabel?: string;
  totalRows: number; invalidRows?: number; duplicateRows?: number; conflictRows?: number;
  /** Share of invalid rows that may be skipped after explicit acknowledgment. Default 0.2 (2 of 10). */
  maxInvalidShare?: number;
  mapping?: [string, string][]; assumptions?: string[];
  errors?: { id: string; dataRow: number; field: string; message: string }[];
  acknowledged?: boolean; onAcknowledge?: (v: boolean) => void; ackError?: string | null; ackInputId?: string;
  saveState?: null | 'saving' | 'success' | 'failure' | 'unknown';
  onConfirm?: () => void; onCheckStatus?: () => void; checking?: boolean; onCancel?: () => void; confirmedAt?: string;
}
export declare function ImportPreview(props: ImportPreviewProps): React.ReactElement;

export interface ScheduleWindowsProps {
  mode: 'none' | 'continuous' | 'inherit' | 'windows';
  onModeChange?: (m: ScheduleWindowsProps['mode']) => void;
  inheritLabel?: string;
  windows?: { days: string; start: string; end: string; nextDay?: boolean }[];
  help?: Node;
}
export declare function ScheduleWindows(props: ScheduleWindowsProps): React.ReactElement;

export interface OutputMetricPreviewProps {
  /** false renders nothing: the metric is optional and the core stays complete. */
  enabled: boolean;
  energyKwh: number | null; output: number | null; unit?: string;
  method?: 'actual' | 'estimated'; periodLabel?: string; headingLevel?: 2 | 3 | 4;
}
export declare function OutputMetricPreview(props: OutputMetricPreviewProps): React.ReactElement | null;

/* ---------- intentional additions ---------- */
export interface ScreenProps {
  title: string; subtitle?: string; children: Node; aside?: Node; asideLabel?: string;
  current?: 'beranda' | 'perangkat' | 'saran'; onNavigate?: TabNavigationProps['onNavigate'];
  back?: { label: string; onClick: () => void };
  provenance?: Provenance;
}
export declare function Screen(props: ScreenProps): React.ReactElement;

export type IconName = 'home' | 'devices' | 'saran' | 'chevronRight' | 'chevronLeft' | 'chevronDown' | 'close' | 'info' | 'attention' | 'error' | 'success' | 'unknown' | 'refresh' | 'calendar' | 'clock' | 'offline' | 'upload' | 'scope' | 'file';
export declare function Icon(props: { name: IconName; size?: 'default' | 'small'; className?: string }): React.ReactElement;

export declare const format: {
  kwh(v: number | null, unit?: string): string | null;
  signedKwh(v: number | null): string | null;
  rupiah(v: number | null): string | null;
  percent(part: number, whole: number): string | null;
  signedPercent(delta: number, reference: number): string | null;
  number(v: number | null): string | null;
  dateRange(startIso: string, endIso?: string): string;
  time(hhmm: string): string;
  parseDecimal(text: string): ParsedDecimal;
};

declare global {
  interface Window {
    HD: {
      Button: typeof Button; IconButton: typeof IconButton; TextField: typeof TextField; NumericField: typeof NumericField;
      ChoiceGroup: typeof ChoiceGroup; PeriodSelector: typeof PeriodSelector; TabNavigation: typeof TabNavigation;
      SheetDialog: typeof SheetDialog; Disclosure: typeof Disclosure; Notice: typeof Notice; ErrorSummary: typeof ErrorSummary;
      ProgressStatus: typeof ProgressStatus; EnergyMetric: typeof EnergyMetric; CostEstimate: typeof CostEstimate;
      ScopeSummary: typeof ScopeSummary; DataQuality: typeof DataQuality; AssetRow: typeof AssetRow;
      ContributionRanking: typeof ContributionRanking; HistoryChart: typeof HistoryChart; ChartDataAlternative: typeof ChartDataAlternative;
      InsightSummary: typeof InsightSummary; EvidencePanel: typeof EvidencePanel; ImportPreview: typeof ImportPreview;
      ScheduleWindows: typeof ScheduleWindows; OutputMetricPreview: typeof OutputMetricPreview; Screen: typeof Screen; Icon: typeof Icon;
      format: typeof format; version: string;
    };
  }
}
