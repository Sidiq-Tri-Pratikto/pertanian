import type { Tone } from '@/components/tr/Status';
import { t } from '@/features/i18n/t';
import { AVAILABILITY_REASON } from '@/features/intake/model';
import { range } from '@/features/money';
import { labelOf, STAGES } from '@/features/portfolio/model';

export type DimensionId = 'sector' | 'topic' | 'readiness' | 'money' | 'form' | 'requirements' | 'evidence' | 'availability';
export type DimensionStatus = 'MATCH' | 'PARTIAL' | 'MISMATCH' | 'UNKNOWN' | 'NOT_APPLICABLE';

export type Dimension = {
  id: DimensionId;
  score: number | null;
  status: DimensionStatus;
  weight: string | null;
  values: Record<string, unknown>;
};

export const DIMENSION_ORDER: readonly DimensionId[] = [
  'sector',
  'topic',
  'readiness',
  'money',
  'form',
  'requirements',
  'evidence',
  'availability',
];

export const DIMENSION_META: Record<DimensionId, { label: string; help: string }> = {
  sector: {
    label: 'Bidang',
    help: 'Bernilai 100% jika sektor inovasi termasuk sektor yang dicari mandat, 0% jika berbeda, dan belum diketahui jika salah satu belum mengisi.',
  },
  topic: {
    label: 'Topik dan detail produk',
    help: 'Persentase kata kunci mandat yang muncul sebagai kata utuh pada kata kunci, judul, ringkasan, masalah, atau solusi inovasi Anda.',
  },
  readiness: {
    label: 'Tahap dan TKT',
    help: 'Rata-rata kecocokan tahap inovasi dan TKT (Tingkat Kesiapterapan Teknologi) terhadap preferensi mandat. Bagian yang belum diisi tidak dihitung sebagai nol.',
  },
  money: {
    label: 'Dana',
    help: 'Bernilai 100% jika kisaran dana beririsan pada mata uang, periode, dan cakupan yang sama; 50% jika tidak beririsan tetapi dukungan sebagian diterima; 0% jika tidak beririsan.',
  },
  form: {
    label: 'Bentuk kerja sama',
    help: 'Bernilai 100% jika bentuk kerja sama kebutuhan Anda termasuk yang diterima mandat, 0% jika berbeda, dan belum diketahui pada pratinjau tanpa kebutuhan.',
  },
  requirements: {
    label: 'Syarat wajib',
    help: 'Persentase syarat wajib saat pengajuan yang terpenuhi. Jika ada syarat wajib yang gagal, hasil tetap tidak cocok meski aspek lain tinggi.',
  },
  evidence: {
    label: 'Bukti',
    help: 'Persentase syarat yang sudah didukung berkas atau pernyataan yang tersedia maupun diperiksa. Ditampilkan untuk transparansi kepercayaan.',
  },
  availability: {
    label: 'Ketersediaan investor',
    help: 'Bernilai 100% jika mandat sedang aktif menerima pitching saat ini, 0% jika ditutup, dijeda, atau menggunakan jalur eksternal.',
  },
};

export const DIMENSION_STATUS_LABEL: Record<DimensionStatus, string> = {
  MATCH: 'Cocok',
  PARTIAL: 'Sebagian',
  MISMATCH: 'Belum cocok',
  UNKNOWN: 'Belum diketahui',
  NOT_APPLICABLE: 'Tidak berlaku',
};

const FORM_LABELS: Record<string, string> = {
  PROJECT: 'Proyek',
  LICENSE: 'Lisensi',
  EQUITY: 'Ekuitas',
};

export function dimensionTone(status: DimensionStatus): Tone {
  if (status === 'MATCH') return 'success';
  if (status === 'PARTIAL' || status === 'UNKNOWN') return 'warning';
  if (status === 'MISMATCH') return 'danger';
  return 'neutral';
}

function asString(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && item.length > 0) : [];
}

function asNumber(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

type RawMoney = { low?: string | null; high?: string | null; currency?: string | null };

function formatRange(value: unknown): string | null {
  if (!value || typeof value !== 'object') return null;
  const raw = value as RawMoney;
  if (!raw.low || !raw.high || !raw.currency) return null;
  return range(raw.currency, raw.low, raw.high);
}

function formLabel(code: string): string {
  return t(FORM_LABELS[code] ?? code);
}

function stageLabel(code: string): string {
  return t(labelOf(STAGES, code));
}

/** Formats one concise sentence for a breakdown dimension from raw API values. */
export function dimensionSentence(dimension: Dimension): string {
  const values = dimension.values ?? {};
  switch (dimension.id) {
    case 'sector': {
      const source = asString(values.source);
      const targets = asStringList(values.target);
      if (!source || !targets.length) return t('Bidang belum dinyatakan oleh salah satu pihak.');
      if (dimension.status === 'MATCH') return t('Bidang {source} sesuai dengan mandat.', { source: t(source) });
      return t('Mandat mencari bidang {target}; produk Anda di bidang {source}.', {
        target: targets.map((item) => t(item)).join(', '),
        source: t(source),
      });
    }
    case 'topic': {
      const matched = asStringList(values.matched);
      const missing = asStringList(values.missing);
      if (dimension.status === 'UNKNOWN') return t('Mandat tidak mencantumkan kata kunci topik.');
      if (!missing.length) return t('Semua kata kunci mandat ditemukan: {matched}.', { matched: matched.join(', ') });
      if (!matched.length) return t('Belum ada kata kunci mandat yang ditemukan: {missing}.', { missing: missing.join(', ') });
      return t('Ditemukan: {matched}. Belum muncul: {missing}.', { matched: matched.join(', '), missing: missing.join(', ') });
    }
    case 'readiness': {
      const stage = asString(values.stage);
      const accepted = asStringList(values.accepted_stages);
      const tkt = asNumber(values.tkt);
      const minTkt = asNumber(values.min_tkt);
      const parts: string[] = [];
      if (stage && accepted.length) {
        if (accepted.includes(stage)) {
          parts.push(t('Tahap {stage} diterima mandat.', { stage: stageLabel(stage) }));
        } else {
          parts.push(
            t('Mandat menerima tahap {accepted}; produk Anda {stage}.', {
              accepted: accepted.map(stageLabel).join(', '),
              stage: stageLabel(stage),
            }),
          );
        }
      }
      if (minTkt !== null && tkt !== null) {
        if (tkt >= minTkt) {
          parts.push(t('TKT {tkt} memenuhi preferensi TKT {min} ke atas.', { tkt, min: minTkt }));
        } else {
          parts.push(t('Mandat mencari TKT {min} ke atas; produk Anda TKT {tkt}.', { min: minTkt, tkt }));
        }
      } else if (minTkt !== null) {
        parts.push(t('Mandat mencari TKT {min} ke atas; TKT produk belum dinyatakan.', { min: minTkt }));
      } else if (tkt !== null && !parts.length) {
        parts.push(t('Produk Anda menyatakan TKT {tkt}.', { tkt }));
      }
      return parts.length ? parts.join(' ') : t('Tahap dan TKT belum cukup untuk dibandingkan.');
    }
    case 'money': {
      const source = formatRange(values.source);
      const target = formatRange(values.target);
      const reason = asString(values.reason);
      if (dimension.status === 'UNKNOWN') {
        return reason ? t(reason) : t('Kisaran dana belum dapat dibandingkan.');
      }
      if (source && target) {
        if (dimension.score === 100) {
          return t('Kisaran Anda ({source}) beririsan dengan mandat ({target}).', { source, target });
        }
        if (dimension.score === 50) {
          return t('Kisaran Anda ({source}) tidak beririsan dengan {target}, tetapi dukungan sebagian diterima.', { source, target });
        }
        return t('Kisaran Anda ({source}) tidak beririsan dengan {target}.', { source, target });
      }
      return reason ? t(reason) : t('Kisaran dana sudah dibandingkan.');
    }
    case 'form': {
      const source = asString(values.source);
      const targets = asStringList(values.target);
      if (!source || !targets.length) return t('Bentuk kerja sama belum dinyatakan.');
      if (dimension.status === 'MATCH') return t('Bentuk kerja sama {source} diterima mandat.', { source: formLabel(source) });
      return t('Mandat menerima {target}; kebutuhan Anda {source}.', {
        target: targets.map(formLabel).join(', '),
        source: formLabel(source),
      });
    }
    case 'requirements': {
      if (dimension.status === 'NOT_APPLICABLE') return t('Mandat tidak mencantumkan syarat wajib saat pengajuan.');
      const passed = asNumber(values.passed) ?? 0;
      const total = asNumber(values.total) ?? 0;
      const failed = asStringList(values.failed);
      const unknown = asStringList(values.unknown);
      if (failed.length) return t('Syarat wajib belum terpenuhi: {items}.', { items: failed.join(', ') });
      if (unknown.length) return t('Syarat wajib perlu dilengkapi: {items}.', { items: unknown.join(', ') });
      return t('{passed} dari {total} syarat wajib terpenuhi.', { passed, total });
    }
    case 'evidence': {
      if (dimension.status === 'NOT_APPLICABLE') return t('Belum ada daftar syarat untuk dinilai buktinya.');
      const provided = asNumber(values.provided) ?? 0;
      const reviewed = asNumber(values.reviewed) ?? 0;
      const applicable = asNumber(values.applicable) ?? 0;
      return t('{provided} tersedia, {reviewed} sudah diperiksa, dari {applicable} syarat.', { provided, reviewed, applicable });
    }
    case 'availability': {
      if (values.available === true) return t('Mandat sedang menerima pitching.');
      const reason = asString(values.reason);
      if (reason && reason in AVAILABILITY_REASON) return t(AVAILABILITY_REASON[reason as keyof typeof AVAILABILITY_REASON]);
      return t('Mandat sedang tidak menerima pitching.');
    }
  }
}

export function orderedDimensions(dimensions: Dimension[]): Dimension[] {
  const byId = new Map(dimensions.map((item) => [item.id, item]));
  return DIMENSION_ORDER.map((id) => byId.get(id)).filter((item): item is Dimension => Boolean(item));
}
