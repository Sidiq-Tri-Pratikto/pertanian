import NextLink from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { ContextBar } from '@/features/ContextBar';
import { formatDateTime } from '@/features/organizations';
import { readPersona } from '@/features/persona';
import { PITCH_STATUS, SOURCE_KIND, type PitchSummary } from '@/features/pitches/model';
import { TURN_LABEL, turnOf, type ListFilters } from '@/features/pitches/workspace';
import { FeatureList, PROVENANCE } from '@/views/parts';
import type { Capabilities } from '@/features/registry';

type Box = 'outgoing' | 'masuk' | 'diskusi';

const COPY: Record<Box, { title: string; subtitle: string; nav: string; empty: string; body: string; features: string[] }> = {
  outgoing: {
    title: 'Pitching dan Diskusi',
    subtitle: 'Pitching yang Anda kirim dan statusnya.',
    nav: 'pitching',
    empty: 'Belum ada pitching',
    body: 'Pitching dikirim dari halaman kecocokan, setelah Anda memeriksa semuanya.',
    features: ['keputusan-revisi', 'diskusi', 'jadwal', 'kerja-sama'],
  },
  masuk: {
    title: 'Pitching Masuk',
    subtitle: 'Pitching yang dikirim kepada Anda.',
    nav: 'masuk',
    empty: 'Belum ada pitching masuk',
    body: 'Pitching muncul di sini setelah inovator mengirimnya ke mandat Anda.',
    features: ['keputusan-revisi'],
  },
  diskusi: {
    title: 'Diskusi dan Jadwal',
    subtitle: 'Pitching yang sudah disetujui untuk diskusi.',
    nav: 'diskusi',
    empty: 'Belum ada diskusi',
    body: 'Diskusi dimulai setelah Anda menyetujui sebuah pitching untuk diskusi.',
    features: ['diskusi', 'jadwal', 'kerja-sama', 'kalender'],
  },
};

const BOX_PARAM: Record<Box, string | null> = { outgoing: null, masuk: 'masuk', diskusi: 'diskusi' };

type Props = { me: Me; box: Box; pitches: PitchSummary[]; total: number; filters: ListFilters; capabilities: Capabilities };

/** S12 lists: sent pitches for inventors, incoming and discussion boxes for partners, each saying whose turn it is. */
export function PitchesView({ me, box, pitches, total, filters, capabilities }: Props) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  const copy = COPY[box];
  const incoming = box !== 'outgoing';
  const filtered = Boolean(filters.status || filters.giliran);
  const param = BOX_PARAM[box];
  const clearHref = param ? `/pitches?box=${param}` : '/pitches';
  return (
    <Screen persona={persona} current={copy.nav} title={copy.title} subtitle={copy.subtitle} provenance={PROVENANCE} context={<ContextBar me={me} />}>
      {total ? (
        <form method="get" action="/pitches" className="tr-panel tr-stack" aria-label="Saring pitching">
          {param ? <input type="hidden" name="box" value={param} /> : null}
          <div className="tr-field">
            <label htmlFor="filter-turn" className="tr-sys-type-label">
              Giliran
            </label>
            <select id="filter-turn" name="giliran" className="tr-input tr-select" defaultValue={filters.giliran ?? ''}>
              <option value="">Semua</option>
              <option value="anda">{TURN_LABEL.you}</option>
              <option value="lain">{TURN_LABEL.other}</option>
            </select>
          </div>
          <div className="tr-field">
            <label htmlFor="filter-status" className="tr-sys-type-label">
              Status
            </label>
            <select id="filter-status" name="status" className="tr-input tr-select" defaultValue={filters.status ?? ''}>
              <option value="">Semua status</option>
              {Object.entries(PITCH_STATUS)
                .filter(([value]) => value !== 'DRAFT')
                .map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
            </select>
          </div>
          <div className="tr-row">
            <button type="submit" className="tr-btn tr-btn--secondary">
              Terapkan
            </button>
            {filtered ? (
              <NextLink className="tr-link" href={clearHref}>
                Hapus semua filter
              </NextLink>
            ) : null}
          </div>
        </form>
      ) : null}
      {pitches.length ? (
        <ul className="tr-stack">
          {pitches.map((pitch) => {
            const turn = turnOf(pitch, me.active_party_id);
            return (
              <li key={pitch.id} className="tr-panel tr-stack">
                <p className="tr-muted tr-sys-type-support">{`${SOURCE_KIND[pitch.subject_type]} · ${incoming ? `dari ${pitch.requester_name}` : `kepada ${pitch.recipient_name}`}`}</p>
                <h2 className="tr-sys-type-heading-sm">{`${pitch.subject_title} → ${pitch.opportunity_title}`}</h2>
                <p className="tr-row">
                  <Status tone="neutral" label={PITCH_STATUS[pitch.status] ?? pitch.status} />
                  {turn ? <Status tone={turn === 'you' ? 'action' : 'neutral'} icon={turn === 'you' ? 'right' : 'clock'} label={TURN_LABEL[turn]} /> : null}
                </p>
                <p className="tr-muted tr-sys-type-support">{`Diperbarui ${formatDateTime(pitch.updated_at, me.account.time_zone)}`}</p>
                <p>
                  <NextLink className="tr-link" href={`/pitches/${pitch.id}`}>
                    Buka pitching <span className="tr-sr">{`${pitch.subject_title} → ${pitch.opportunity_title}`}</span>
                  </NextLink>
                </p>
              </li>
            );
          })}
        </ul>
      ) : filtered ? (
        <EmptyState icon="search" title="Tidak ada pitching dengan filter ini">
          Ubah atau hapus filter untuk melihat pitching lainnya.
        </EmptyState>
      ) : (
        <EmptyState icon={incoming ? 'inbox' : 'chat'} title={copy.empty}>
          {copy.body}
        </EmptyState>
      )}
      <FeatureList ids={copy.features} capabilities={capabilities} />
    </Screen>
  );
}
