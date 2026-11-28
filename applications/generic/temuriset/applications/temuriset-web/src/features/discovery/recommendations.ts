import type { Dimension, DimensionId } from '@/features/discovery/breakdown';
import { score } from '@/features/discovery/model';
import { t } from '@/features/i18n/t';
import { range } from '@/features/money';
import { labelOf, STAGES } from '@/features/portfolio/model';

export type RecommendationKind =
  | 'requirement'
  | 'topic'
  | 'tkt_below'
  | 'tkt_missing'
  | 'stage'
  | 'money_missing'
  | 'money_gap'
  | 'form'
  | 'evidence'
  | 'sector'
  | 'availability'
  | 'no_need';

export type Estimate = {
  label: string;
  fit: { lower: string; upper: string; coverage: string };
  gain: string;
};

export type Recommendation = {
  kind: RecommendationKind;
  blocking: boolean;
  dimension: DimensionId | null;
  target: Record<string, unknown>;
  values: Record<string, unknown>;
  estimate: Estimate | null;
};

const FORM_LABELS: Record<string, string> = {
  PROJECT: 'Proyek',
  LICENSE: 'Lisensi',
  EQUITY: 'Ekuitas',
};

function str(value: unknown): string | null {
  return typeof value === 'string' && value.trim() ? value : null;
}

function strList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && item.length > 0) : [];
}

function num(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function moneyRange(value: unknown): string {
  if (!value || typeof value !== 'object') return t('Belum ditentukan');
  const raw = value as { low?: string | null; high?: string | null; currency?: string | null };
  return range(raw.currency, raw.low, raw.high);
}

function withReturn(base: string, returnTo?: string, hash?: string): string {
  const suffix = hash ? `#${hash}` : '';
  if (!returnTo) return `${base}${suffix}`;
  const sep = base.includes('?') ? '&' : '?';
  return `${base}${sep}return=${encodeURIComponent(returnTo)}${suffix}`;
}

export type RecommendationCopy = { title: string; body: string };

/** Turns a raw API Recommendation into honest, conditional Indonesian/English copy. */
export function recommendationCopy(rec: Recommendation): RecommendationCopy {
  const v = rec.values ?? {};
  switch (rec.kind) {
    case 'no_need':
      return {
        title: t('Buat kebutuhan dukungan'),
        body: t('Buat kebutuhan dukungan untuk produk ini agar dana dan bentuk kerja sama bisa dinilai.'),
      };
    case 'requirement': {
      const label = str(v.label) ?? t('Syarat wajib');
      const reason = str(v.reason);
      return {
        title: t('Syarat “{label}”', { label }),
        body: reason ? t(reason) : t('Lengkapi syarat wajib ini agar pengajuan dapat dilanjutkan.'),
      };
    }
    case 'topic': {
      const missing = strList(v.missing);
      return {
        title: t('Perjelas topik yang dicari investor'),
        body: t('Investor ini mencari: {missing}. Bila sesuai dengan produk Anda, tambahkan sebagai kata kunci atau jelaskan di ringkasan.', {
          missing: missing.join(', '),
        }),
      };
    }
    case 'tkt_below': {
      const minTkt = num(v.min_tkt) ?? 1;
      const tkt = num(v.tkt) ?? 1;
      return {
        title: t('Perbarui TKT bila pengujian sudah maju'),
        body: t('Mandat mencari TKT {min} ke atas; produk Anda TKT {tkt}. Bila uji terbaru sudah mencapai tingkat itu, perbarui TKT dan lampirkan buktinya.', {
          min: minTkt,
          tkt,
        }),
      };
    }
    case 'tkt_missing': {
      const minTkt = num(v.min_tkt) ?? 1;
      return {
        title: t('Nyatakan TKT produk Anda'),
        body: t('Nyatakan TKT produk Anda. Investor ini mencari TKT {min} ke atas.', { min: minTkt }),
      };
    }
    case 'stage': {
      const accepted = strList(v.accepted_stages).map((code) => t(labelOf(STAGES, code))).join(', ');
      const stage = t(labelOf(STAGES, str(v.stage) ?? ''));
      return {
        title: t('Tahap produk belum sesuai mandat ini'),
        body: t('Mandat menerima tahap {accepted}; produk Anda {stage}. Perbarui tahap hanya bila produk sudah maju; jika belum, lihat investor lain.', {
          accepted,
          stage,
        }),
      };
    }
    case 'money_missing':
      return {
        title: t('Lengkapi kisaran biaya'),
        body: t('Lengkapi kisaran biaya kebutuhan ini agar investor dapat membandingkan.'),
      };
    case 'money_gap':
      return {
        title: t('Sesuaikan cakupan atau kisaran biaya'),
        body: t('Kisaran Anda ({source}) tidak beririsan dengan {target}. Pertimbangkan menerima dukungan sebagian atau menyesuaikan cakupan bila sesuai.', {
          source: moneyRange(v.source),
          target: moneyRange(v.target),
        }),
      };
    case 'form': {
      const targets = strList(v.target).map((code) => t(FORM_LABELS[code] ?? code)).join(', ');
      const source = t(FORM_LABELS[str(v.source) ?? ''] ?? str(v.source) ?? '');
      return {
        title: t('Periksa bentuk kerja sama'),
        body: t('Mandat menerima {target}; kebutuhan Anda {source}. Ubah hanya bila bentuk itu sesuai dengan rencana Anda.', {
          target: targets,
          source,
        }),
      };
    }
    case 'evidence': {
      const items = strList(v.items);
      return {
        title: t('Lampirkan berkas bukti'),
        body: t('Lampirkan bukti untuk: {items}.', { items: items.join(', ') }),
      };
    }
    case 'sector': {
      const targets = strList(v.target).map((item) => t(item)).join(', ');
      const source = t(str(v.source) ?? '');
      return {
        title: t('Bidang mandat berbeda dengan produk Anda'),
        body: t('Mandat ini untuk bidang {target}; produk Anda {source}. Bila produk juga melayani bidang itu, jelaskan di ringkasan; jika tidak, lihat investor lain.', {
          target: targets,
          source,
        }),
      };
    }
    case 'availability':
      return {
        title: t('Penerimaan sedang tidak dibuka'),
        body: t('Investor ini sedang tidak menerima pitching. Simpan atau ikuti investor ini untuk kabar berikutnya.'),
      };
  }
}

export type RecommendationAction = { href: string; label: string };

/** Maps a recommendation to its deep-link contract address (docs/roadmap/revamp-2-demo-feedback.md §3). */
export function recommendationAction(rec: Recommendation, returnTo?: string): RecommendationAction | null {
  const target = rec.target ?? {};
  const inventionId = str(target.invention_id);
  const needId = str(target.need_id);
  const sourceType = str(target.source_type);
  const field = str(target.field);

  if (rec.kind === 'no_need' && inventionId) {
    return {
      href: withReturn(`/support-requests?invention=${encodeURIComponent(inventionId)}`, returnTo, 'baru'),
      label: t('Buat kebutuhan dukungan'),
    };
  }
  if (rec.kind === 'stage' || rec.kind === 'sector') {
    if (inventionId) {
      return {
        href: `/discover?type=partners&produk=${encodeURIComponent(inventionId)}`,
        label: t('Lihat investor lain untuk produk ini'),
      };
    }
    return { href: '/discover?type=partners', label: t('Lihat investor lain untuk produk ini') };
  }
  if (rec.kind === 'availability') return null;

  if (field === 'keywords' && inventionId) {
    return { href: withReturn(`/inventions/${inventionId}/edit?step=1`, returnTo, 'kata-kunci'), label: t('Perbarui kata kunci') };
  }
  if (field === 'tkt' && inventionId) {
    return { href: withReturn(`/inventions/${inventionId}/edit?step=2`, returnTo, 'tkt'), label: t('Perbarui TKT') };
  }
  if (field === 'documents' && inventionId) {
    return { href: withReturn(`/inventions/${inventionId}/edit?step=2`, returnTo, 'dokumen'), label: t('Lampirkan berkas') };
  }
  if ((field === 'facts' || field === 'authority') && inventionId) {
    return {
      href: withReturn(`/inventions/${inventionId}/edit?step=2`, returnTo, 'fakta'),
      label: field === 'authority' ? t('Perbarui wewenang') : t('Perbarui fakta'),
    };
  }
  if (field === 'budget' && needId) {
    return { href: withReturn(`/support-requests/${needId}`, returnTo, 'kisaran'), label: t('Lengkapi kisaran') };
  }
  if (field === 'contribution' && needId) {
    return { href: withReturn(`/funding-requests/${needId}/edit`, returnTo), label: t('Lengkapi kisaran') };
  }
  if (field === 'form' && needId) {
    const path = sourceType === 'FUNDING_REQUEST' ? `/funding-requests/${needId}/edit` : `/support-requests/${needId}`;
    return { href: withReturn(path, returnTo, sourceType === 'FUNDING_REQUEST' ? undefined : 'bentuk'), label: t('Ubah bentuk kerja sama') };
  }
  return null;
}

export function estimateText(estimate: Estimate): string {
  return t('Perkiraan bila benar untuk produk Anda: {label} ({lower}–{upper})', {
    label: t(estimate.label),
    lower: score(estimate.fit.lower, 'lower'),
    upper: score(estimate.fit.upper, 'upper'),
  });
}

export type TopStep = {
  key: string;
  recommendation: Recommendation;
  totalGain: number;
  partners: string[];
};

/** P2: up to three recommendations with the largest total estimated gain across recommended results. */
export function topImpactSteps(results: { partner: string; recommendations?: Recommendation[] }[]): TopStep[] {
  const byKey = new Map<string, TopStep>();
  for (const result of results) {
    for (const rec of result.recommendations ?? []) {
      if (!rec.estimate) continue;
      const gain = Number(rec.estimate.gain);
      if (!Number.isFinite(gain) || gain <= 0) continue;
      const field = str(rec.target?.field) ?? rec.kind;
      const key = `${rec.kind}:${field}`;
      const existing = byKey.get(key);
      if (existing) {
        existing.totalGain += gain;
        if (!existing.partners.includes(result.partner)) existing.partners.push(result.partner);
      } else {
        byKey.set(key, { key, recommendation: rec, totalGain: gain, partners: [result.partner] });
      }
    }
  }
  return [...byKey.values()].sort((a, b) => b.totalGain - a.totalGain).slice(0, 3);
}

export type SavedScores = Record<string, Partial<Record<DimensionId, number | null>>>;

export function scoresOf(results: { opportunity_id: string; breakdown?: Dimension[] }[]): SavedScores {
  const map: SavedScores = {};
  for (const item of results) {
    const dims: Partial<Record<DimensionId, number | null>> = {};
    for (const dim of item.breakdown ?? []) dims[dim.id] = dim.score;
    map[item.opportunity_id] = dims;
  }
  return map;
}

export function deltasFor(
  previous: SavedScores | null,
  opportunityId: string,
  breakdown: Dimension[],
): Partial<Record<DimensionId, { before: number | null; after: number | null }>> {
  const prev = previous?.[opportunityId];
  if (!prev) return {};
  const out: Partial<Record<DimensionId, { before: number | null; after: number | null }>> = {};
  for (const dim of breakdown) {
    const before = prev[dim.id];
    if (before !== undefined && before !== null && dim.score !== null && before !== dim.score) {
      out[dim.id] = { before, after: dim.score };
    }
  }
  return out;
}
