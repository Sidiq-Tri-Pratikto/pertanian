/**
 * What S10 shows, from the service's import responses. Every count, reason, question and assumption is the
 * service's: nothing here adds, subtracts or divides a count, or decides whether an import is blocked.
 */
import type { AssetCandidate, ImportAnswers, ImportCommit, ImportPeriod, ImportPreview, ImportResult } from '@/api/client';
import type { ApiError } from '@/api/errors';
import type { Period } from '@/features/workspace/workspace-store';
import { formatCadence, formatDateRange, formatDateTime, KIND_LABEL, type AssetKind } from '@/lib/format';

export type ImportStream = {
  stream_key: string;
  asset_name: string;
  asset_id: string | null;
  source_id: string | null;
  kind: string;
  unit: string | null;
  cadence_seconds: number | null;
  interval_basis: 'inferred' | 'declared' | 'explicit' | null;
};

type ImportColumns = {
  timestamp: string | null;
  interval_start: string | null;
  interval_end: string | null;
  value: string | null;
  unit: string | null;
};

type ImportMapping = { timezone: string; streams: ImportStream[]; columns: ImportColumns };

const NO_COLUMNS: ImportColumns = { timestamp: null, interval_start: null, interval_end: null, value: null, unit: null };

function text(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

/** The preview's `mapping` is an open record in the contract, so each field is read defensively. */
export function mappingOf(preview: ImportPreview): ImportMapping {
  const raw = preview.mapping as Record<string, unknown>;
  const columns = (raw.columns ?? {}) as Record<string, unknown>;
  const streams = Array.isArray(raw.streams) ? (raw.streams as Record<string, unknown>[]) : [];
  return {
    timezone: text(raw.timezone) ?? '',
    columns: {
      ...NO_COLUMNS,
      timestamp: text(columns.timestamp),
      interval_start: text(columns.interval_start),
      interval_end: text(columns.interval_end),
      value: text(columns.value),
      unit: text(columns.unit),
    },
    streams: streams
      .filter((stream) => typeof stream.stream_key === 'string' && typeof stream.asset_name === 'string')
      .map((stream) => ({
        stream_key: String(stream.stream_key),
        asset_name: String(stream.asset_name),
        asset_id: text(stream.asset_id),
        source_id: text(stream.source_id),
        kind: text(stream.kind) ?? '',
        unit: text(stream.unit),
        cadence_seconds: Number.isInteger(stream.cadence_seconds) ? (stream.cadence_seconds as number) : null,
        interval_basis:
          stream.interval_basis === 'inferred' || stream.interval_basis === 'declared' || stream.interval_basis === 'explicit'
            ? stream.interval_basis
            : null,
      })),
  };
}

export const VALUE_KIND_OPTIONS = [
  { value: 'interval_energy' as const, label: 'Energi interval (Wh)' },
  { value: 'average_power' as const, label: 'Daya rata-rata (W)' },
  { value: 'counter' as const, label: 'Penghitung kumulatif (Wh)' },
];

export const POWER_OPTIONS = [
  { value: 'average' as const, label: 'Daya rata-rata selama interval', description: 'Diubah menjadi energi: W × durasi.' },
  { value: 'instantaneous' as const, label: 'Daya sesaat (titik waktu)', description: 'Tidak dapat menjadi energi; impor diblokir.' },
];

export const SCOPE_OPTIONS = [
  {
    value: 'disjoint' as const,
    label: 'Ya, terpisah satu sama lain dan dari perangkat lain',
    description: 'Nilainya boleh dijumlahkan.',
  },
  {
    value: 'unknown_overlap' as const,
    label: 'Belum tahu',
    description: 'Nilai tampil per perangkat; total gabungan tidak dihitung.',
  },
];

export const NEW_ASSET = 'new';
const NEW_ASSET_LABEL = 'Buat perangkat baru';

export type Control =
  | { kind: 'timezone'; key: string; message: string; timezone: string }
  | { kind: 'scope'; key: string; message: string }
  | { kind: 'power_meaning'; key: string; message: string }
  | { kind: 'value_kind'; key: string; message: string }
  | { kind: 'interval_duration'; key: string; message: string; streamKey: string; assetName: string }
  | { kind: 'asset_choice'; key: string; message: string; assetName: string; options: { value: string; label: string }[] }
  | { kind: 'other_source'; key: string; message: string; assetName: string; streamKey: string; writtenName: string }
  | { kind: 'unanswerable'; key: string; message: string };

export type AnswerValue = boolean | string | number;

const ASSET_KIND: Record<string, AssetKind> = { device: 'device', circuit: 'circuit', group: 'group', site_total: 'meter' };

/** `Kulkas · Perangkat · Dapur · Pendingin makanan · ID …a1b2c3`, leaving out what is absent. */
export function assetOptionLabel(candidate: AssetCandidate): string {
  const kind = ASSET_KIND[candidate.scope_kind];
  return [candidate.name, kind ? KIND_LABEL[kind] : null, candidate.location, candidate.category, `ID …${candidate.id.slice(-6)}`]
    .filter(Boolean)
    .join(' · ');
}

/** One control per open question (027 D13). Names only a file can separate or merge get no control. */
export function questionControls(preview: ImportPreview): Control[] {
  const { timezone, streams } = mappingOf(preview);
  const streamOf = (key: string | undefined) => streams.find((stream) => stream.stream_key === key);
  return preview.questions.flatMap((question, index): Control[] => {
    const message = question.message;
    switch (question.kind) {
      case 'timezone':
        return [{ kind: 'timezone', key: 'timezone', message, timezone }];
      case 'scope':
        return [{ kind: 'scope', key: 'scope', message }];
      case 'power_meaning':
        return [{ kind: 'power_meaning', key: 'power_meaning', message }];
      case 'value_kind':
        return [{ kind: 'value_kind', key: 'value_kind', message }];
      case 'interval_duration':
        return (question.streams ?? []).map((streamKey) => ({
          kind: 'interval_duration' as const,
          key: `interval:${streamKey}`,
          message,
          streamKey,
          assetName: streamOf(streamKey)?.asset_name ?? streamKey,
        }));
      case 'asset_choice': {
        const assetName = question.asset_name ?? '';
        return [
          {
            kind: 'asset_choice',
            key: `asset:${assetName}`,
            message,
            assetName,
            options: [
              ...(question.candidates ?? []).map((candidate) => ({ value: candidate.id, label: assetOptionLabel(candidate) })),
              { value: NEW_ASSET, label: NEW_ASSET_LABEL },
            ],
          },
        ];
      }
      case 'other_source': {
        const streamKey = question.streams?.[0] ?? '';
        const assetName = question.asset_name ?? streamOf(streamKey)?.asset_name ?? streamKey;
        return [
          {
            kind: 'other_source',
            key: `source:${streamKey}`,
            message,
            assetName,
            streamKey,
            writtenName: streamOf(streamKey)?.asset_name ?? assetName,
          },
        ];
      }
      default:
        return [{ kind: 'unanswerable', key: `unanswerable:${index}`, message }];
    }
  });
}

/** The current answer of a control, or undefined while it has none. */
export function answerOf(control: Control, answers: ImportAnswers): AnswerValue | undefined {
  switch (control.kind) {
    case 'timezone':
      return answers.timezone_confirmed === true ? true : undefined;
    case 'scope':
      return answers.scope;
    case 'power_meaning':
      return answers.power_meaning;
    case 'value_kind':
      return answers.value_kind;
    case 'interval_duration':
      return answers.interval_minutes?.[control.streamKey];
    case 'asset_choice':
      return answers.asset_map?.[control.assetName];
    case 'other_source':
      return answers.asset_map?.[control.writtenName];
    default:
      return undefined;
  }
}

/**
 * Sets one answer. `asset_map` is keyed by the name as the file writes it (027 D14): the service reads it that
 * way, while `other_source` names the stored asset. Both keys are sent when they differ.
 */
export function answerFor(_preview: ImportPreview, control: Control, value: AnswerValue | undefined, answers: ImportAnswers): ImportAnswers {
  const next: ImportAnswers = { ...answers };
  switch (control.kind) {
    case 'timezone':
      next.timezone_confirmed = value === true;
      break;
    case 'scope':
      next.scope = value as ImportAnswers['scope'];
      break;
    case 'power_meaning':
      next.power_meaning = value as ImportAnswers['power_meaning'];
      break;
    case 'value_kind':
      next.value_kind = value as ImportAnswers['value_kind'];
      break;
    case 'interval_duration': {
      const minutes = { ...answers.interval_minutes };
      if (typeof value === 'number') {
        minutes[control.streamKey] = value;
      } else {
        delete minutes[control.streamKey];
      }
      next.interval_minutes = minutes;
      break;
    }
    case 'asset_choice':
      next.asset_map = { ...answers.asset_map, [control.assetName]: String(value) };
      break;
    case 'other_source':
      next.asset_map = { ...answers.asset_map, [control.writtenName]: String(value), [control.assetName]: String(value) };
      break;
    default:
      break;
  }
  return next;
}

export type SummaryItem = { key: string; text: string; unanswerable: boolean };

function missingText(control: Control): string {
  switch (control.kind) {
    case 'timezone':
      return `Konfirmasi zona waktu ${control.timezone}.`;
    case 'scope':
      return 'Pilih apakah beban perangkat terukur terpisah.';
    case 'power_meaning':
      return 'Pilih arti kolom daya.';
    case 'value_kind':
      return 'Pilih jenis nilai.';
    case 'interval_duration':
      return `Isi panjang interval untuk ${control.assetName}.`;
    case 'asset_choice':
      return `Pilih perangkat untuk “${control.assetName}”.`;
    case 'other_source':
      return `Pilih cara mengimpor ${control.assetName}.`;
    default:
      return control.message;
  }
}

/** Controls still without an answer, and questions only a changed file can answer. Checked before any request. */
export function unanswered(preview: ImportPreview, answers: ImportAnswers): SummaryItem[] {
  return questionControls(preview)
    .filter((control) => control.kind === 'unanswerable' || answerOf(control, answers) === undefined)
    .map((control) => ({ key: control.key, text: missingText(control), unanswerable: control.kind === 'unanswerable' }));
}

/** Questions the service still asks after an answer was sent, in its own words. */
export function askedAgain(preview: ImportPreview, answers: ImportAnswers): SummaryItem[] {
  return questionControls(preview)
    .filter((control) => control.kind !== 'unanswerable' && answerOf(control, answers) !== undefined)
    .map((control) => ({
      key: control.key,
      text: control.kind === 'value_kind' ? `Jenis nilai ini tidak ada di berkas. Pilih jenis lain. ${control.message}` : control.message,
      unanswerable: false,
    }));
}

function canonical(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(canonical);
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter((entry) => entry[1] !== undefined)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([key, item]) => [key, canonical(item)]),
    );
  }
  return value;
}

/** Whether answers differ from the ones last sent, regardless of key order. No answers sent yet counts as changed. */
export function answersChanged(sent: ImportAnswers | null, answers: ImportAnswers): boolean {
  return sent === null || JSON.stringify(canonical(sent)) !== JSON.stringify(canonical(answers));
}

const DAY_MS = 86_400_000;
const MAX_RANGE_DAYS = 366;

function isoDay(isoDate: string): number {
  const [year, month, day] = isoDate.split('-').map(Number);
  return Date.UTC(year, month - 1, day);
}

export type Landing = Period & { clamped: boolean };

/**
 * Where Beranda lands after an import: the imported dates, or their last 366 days, because the summary refuses
 * a longer range (`(end − start).days + 1 > 366`). Calendar arithmetic on ISO dates only, never on energy.
 */
export function landingPeriod(period: Pick<ImportPeriod, 'start_date' | 'end_date'> & Partial<ImportPeriod> | null): Landing | null {
  if (!period) {
    return null;
  }
  const end = isoDay(period.end_date);
  const days = (end - isoDay(period.start_date)) / DAY_MS + 1;
  if (days <= MAX_RANGE_DAYS) {
    return { preset: 'range', start_date: period.start_date, end_date: period.end_date, clamped: false };
  }
  const start = new Date(end - (MAX_RANGE_DAYS - 1) * DAY_MS).toISOString().slice(0, 10);
  return { preset: 'range', start_date: start, end_date: period.end_date, clamped: true };
}

export type ResultModel = {
  title: string;
  note: string | null;
  confirmedAt: string;
  rows: { term: string; value: string }[];
  primary: 'landing' | 'home';
  landing: Landing | null;
  clockNotice: { tone: 'attention'; text: string } | null;
  nothingNew: string | null;
  longRange: string | null;
};

function names(assets: { name: string }[] | undefined): string {
  return assets?.length ? assets.map((asset) => asset.name).join(', ') : 'Tidak ada';
}

/**
 * The result step (027 D21, D22). It never says data is visible unless rows before the workspace clock exist:
 * with every row after the clock, the primary action is Kembali ke Beranda.
 */
export function resultModel(result: ImportCommit | ImportResult, { found, timezone }: { found: boolean; timezone: string }): ResultModel {
  const replayed = found || ('replayed' in result && result.replayed);
  const after = result.rows_after_site_clock ?? 0;
  const added = result.rows_added;
  const landing = landingPeriod(result.period ?? null);
  const allAfter = added > 0 && after === added;
  const visible = added > 0 && !allAfter && landing !== null;
  let clockNotice: ResultModel['clockNotice'] = null;
  if (allAfter) {
    clockNotice = {
      tone: 'attention',
      text: `Semua ${added} baris tersimpan, tetapi berada setelah waktu ruang kerja ini, sehingga belum tampil di Beranda atau Perangkat.`,
    };
  } else if (after > 0) {
    clockNotice = {
      tone: 'attention',
      text: `${after} dari ${added} baris tersimpan berada setelah waktu ruang kerja ini, sehingga belum dihitung pada ringkasan.`,
    };
  }
  return {
    title: replayed ? 'Impor sudah dikonfirmasi sebelumnya' : 'Impor tersimpan',
    note: replayed ? 'Permintaan yang sama ditemukan; data tidak diimpor dua kali.' : null,
    confirmedAt: `Dikonfirmasi layanan ${formatDateTime(result.committed_at, timezone)}`,
    rows: [
      { term: 'Baris disimpan', value: String(added) },
      { term: 'Baris tidak valid dilewati', value: String(result.rows_skipped) },
      { term: 'Duplikat (dihitung sekali)', value: String(result.rows_duplicate) },
      { term: 'Perangkat baru', value: names(result.assets_created) },
      { term: 'Perangkat yang dipakai', value: names(result.assets_mapped) },
      { term: 'Periode data', value: result.period ? formatDateRange(result.period.start_date, result.period.end_date) : 'Tidak ada periode baru' },
    ],
    primary: visible ? 'landing' : 'home',
    landing,
    clockNotice,
    nothingNew: added === 0 ? `Tidak ada baris baru. ${result.rows_duplicate} baris sama dengan data tersimpan dan dihitung sekali.` : null,
    longRange: visible && landing?.clamped ? 'Rentang data lebih dari 366 hari, sehingga Beranda menampilkan 366 hari terakhirnya.' : null,
  };
}

const SESSION_ENDED = new Set(['SESSION_EXPIRED', 'UNAUTHORIZED']);

export type CommitOutcome = {
  kind: 'refused' | 'stale' | 'gone' | 'ended' | 'unknown';
  reason: 'ack' | 'blocked' | 'conflict' | 'other';
};

/**
 * A commit failure, on its code alone (027 Error table). Only a definite refusal drops the intent; anything else,
 * a timeout or a 5xx included, is an unknown result that must be checked before anything is sent again.
 */
export function commitOutcome(error: ApiError): CommitOutcome {
  switch (error.code) {
    case 'IMPORT_ACK_REQUIRED':
      return { kind: 'refused', reason: 'ack' };
    case 'IMPORT_BLOCKED':
      return { kind: 'refused', reason: 'blocked' };
    case 'CONFLICT':
      return { kind: 'refused', reason: 'conflict' };
    case 'VALIDATION_FAILED':
      return { kind: 'refused', reason: 'other' };
    case 'IMPORT_STALE':
      return { kind: 'stale', reason: 'other' };
    case 'NOT_FOUND':
      return { kind: 'gone', reason: 'other' };
    default:
      return { kind: SESSION_ENDED.has(error.code) ? 'ended' : 'unknown', reason: 'other' };
  }
}

export type PreviewItem = { key: string; text: string; target: string };

export type PreviewOutcome = {
  kind: 'refused' | 'assetGone' | 'ended' | 'notFinished';
  items: PreviewItem[];
  canRetry: boolean;
};

const PREVIEW_REFUSALS = new Set(['IMPORT_INVALID', 'IMPORT_TOO_LARGE', 'VALIDATION_FAILED', 'BAD_REQUEST']);

function detailTarget(loc: (string | number)[]): string {
  const minutes = loc.indexOf('interval_minutes');
  return minutes >= 0 && typeof loc[minutes + 1] === 'string' ? `interval:${loc[minutes + 1]}` : 'source';
}

function detailLine(loc: (string | number)[]): number | null {
  return loc.length === 3 && loc[0] === 'file' && loc[1] === 'line' && Number.isInteger(loc[2]) ? (loc[2] as number) : null;
}

/** A preview failure, on its code alone. A lost preview saved nothing, so it may simply be sent again (027 D4). */
export function previewOutcome(error: ApiError): PreviewOutcome {
  const canRetry = error.recovery.retryable === true;
  if (PREVIEW_REFUSALS.has(error.code)) {
    return {
      kind: 'refused',
      canRetry,
      items: error.details.map((detail, index) => {
        const line = detailLine(detail.loc);
        return { key: `detail-${index}`, text: line === null ? detail.msg : `${detail.msg} (baris berkas ${line})`, target: detailTarget(detail.loc) };
      }),
    };
  }
  if (error.code === 'NOT_FOUND') {
    return { kind: 'assetGone', items: [], canRetry };
  }
  return { kind: SESSION_ENDED.has(error.code) ? 'ended' : 'notFinished', items: [], canRetry };
}

/**
 * A client line for a counter that continues a stored one (027 D25). The service's assumption still says its
 * first reading is a starting point; the stored readings make the total right, which this says plainly.
 */
export function counterNotes(preview: ImportPreview): string[] {
  return mappingOf(preview)
    .streams.filter((stream) => stream.kind === 'counter' && stream.source_id !== null)
    .map(
      (stream) =>
        `${stream.asset_name} melanjutkan penghitung yang sudah tersimpan. Energi dihitung dari selisih dengan pembacaan tersimpan; catatan “pembacaan pertama” hanya menggambarkan isi berkas ini.`,
    );
}

const BASIS = { inferred: 'disimpulkan', declared: 'diisi', explicit: 'dari kolom awal dan akhir' };

/** `Lampu Teras: interval 1 jam (disimpulkan)`. */
export function streamRow(stream: ImportStream): string {
  const interval = stream.cadence_seconds ? `interval ${formatCadence(stream.cadence_seconds)}` : 'interval belum diketahui';
  return `${stream.asset_name}: ${interval}${stream.interval_basis ? ` (${BASIS[stream.interval_basis]})` : ''}`;
}

export function streamTarget(stream: ImportStream): string {
  return stream.asset_id ? 'Perangkat tersimpan' : 'Perangkat baru';
}

/** `tempelan.csv · 12 baris data · kolom waktu timestamp · kolom nilai energi_wh (Wh)`. */
export function mappingLine(preview: ImportPreview): string {
  const { columns } = mappingOf(preview);
  const time = columns.timestamp ?? `${columns.interval_start} dan ${columns.interval_end}`;
  const value = columns.value ? `kolom nilai ${columns.value}${columns.unit ? ` (${columns.unit})` : ''}` : 'kolom nilai belum dipilih';
  return `${preview.file_name} · ${preview.total_rows} baris data · kolom waktu ${time} · ${value}`;
}

/** A row message as the service wrote it, then the file line it sent. Never derived from the data row (027 D18). */
export function rowErrorText(error: { message: string; file_line: number }): string {
  return `${error.message} (baris berkas ${error.file_line})`;
}

const WHOLE_MINUTES = /^[0-9]+$/;

/** The typed minutes as a number, `null` while empty, or `'invalid'` for anything but a whole number. */
export function readMinutes(typed: string): number | null | 'invalid' {
  const trimmed = typed.trim();
  if (trimmed === '') {
    return null;
  }
  return WHOLE_MINUTES.test(trimmed) ? Number(trimmed) : 'invalid';
}

export const MINUTES_ERROR = 'Isi panjang interval dalam menit, dengan angka bulat.';
