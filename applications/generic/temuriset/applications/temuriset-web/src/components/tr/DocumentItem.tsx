import type { ReactNode } from 'react';

import { Icon, type IconName } from '@/components/tr/Icon';
import { Status, type Tone } from '@/components/tr/Status';

type Axis = [label: string, tone: Tone, icon: IconName];

export const FILE: Record<string, Axis> = {
  CREATED: ['Belum diunggah', 'neutral', 'file'],
  UPLOADING: ['Sedang diunggah', 'neutral', 'upload'],
  QUARANTINED: ['Sedang diperiksa keamanannya', 'warning', 'shield'],
  AVAILABLE: ['Aman dan tersedia', 'success', 'check'],
  REJECTED: ['Ditolak saat pemeriksaan keamanan', 'danger', 'cross'],
};
export const EXTRACT: Record<string, Axis> = {
  NOT_REQUESTED: ['Tidak diminta', 'neutral', 'minus'],
  PENDING: ['Menunggu giliran', 'neutral', 'clock'],
  RUNNING: ['Sedang dibaca', 'neutral', 'clock'],
  SUCCEEDED: ['Teks berhasil dibaca', 'success', 'check'],
  FAILED: ['Gagal dibaca', 'danger', 'cross'],
  NEEDS_MANUAL_INPUT: ['Perlu diisi manual', 'warning', 'edit'],
};
export const REVIEW: Record<string, Axis> = {
  PROVIDED_UNREVIEWED: ['Disediakan, belum diperiksa', 'neutral', 'clock'],
  REVIEWED_SUPPORTED: ['Diperiksa, mendukung kriteria', 'success', 'check'],
  REVIEWED_UNSUPPORTED: ['Diperiksa, tidak mendukung kriteria', 'danger', 'cross'],
  NEEDS_CLARIFICATION: ['Perlu klarifikasi', 'warning', 'question'],
  EXPIRED: ['Sudah kedaluwarsa', 'warning', 'clock'],
  SUPERSEDED: ['Diganti versi baru', 'neutral', 'minus'],
};

export type DocumentGrant = { recipient: string; version?: number; revoked?: boolean };

type DocumentItemProps = {
  title?: string;
  version?: number;
  file?: string;
  extraction?: string;
  review?: string;
  grants?: DocumentGrant[];
  denied?: boolean;
  action?: ReactNode;
};

function axis(label: string, [text, tone, icon]: Axis) {
  return (
    <div className="tr-doc__axis">
      <dt className="tr-sys-type-support">{label}</dt>
      <dd>
        <Status tone={tone} icon={icon} label={text} />
      </dd>
    </div>
  );
}

/**
 * Port of TR.DocumentItem: file security, text reading and evidence review as three independent axes (UX-10). Takes a
 * list of grants where the design system takes one, so an owner sees every recipient.
 */
export function DocumentItem({ title, version, file = 'CREATED', extraction = 'NOT_REQUESTED', review = 'PROVIDED_UNREVIEWED', grants = [], denied, action }: DocumentItemProps) {
  if (denied) {
    return (
      <article className="tr-doc">
        <div className="tr-doc__head">
          <Icon name="lock" />
          <h4 className="tr-sys-type-label">Dokumen terbatas</h4>
        </div>
        <p>Anda tidak memiliki akses ke dokumen ini.</p>
        {action ? <div className="tr-row">{action}</div> : null}
      </article>
    );
  }
  return (
    <article className="tr-doc">
      <div className="tr-doc__head">
        <Icon name="file" />
        <h4 className="tr-sys-type-label">{title}</h4>
        {version ? <span className="tr-muted tr-sys-type-support">{`Versi ${version}`}</span> : null}
      </div>
      <dl className="tr-doc__axes">
        {axis('Berkas', FILE[file] ?? FILE.CREATED)}
        {axis('Pembacaan teks', EXTRACT[extraction] ?? EXTRACT.NOT_REQUESTED)}
        {axis('Pemeriksaan bukti', REVIEW[review] ?? REVIEW.PROVIDED_UNREVIEWED)}
      </dl>
      {grants.map((grant, index) => (
        <p key={index} className="tr-sys-type-support">
          {grant.revoked
            ? `Akses ${grant.recipient} dicabut. Unduhan baru diblokir, tetapi salinan yang sudah diunduh tidak dapat ditarik.`
            : `Dibagikan hanya kepada ${grant.recipient}, hanya versi ${grant.version ?? version}.`}
        </p>
      ))}
      {grants.length ? null : <p className="tr-muted tr-sys-type-support">Privat. Belum dibagikan kepada siapa pun.</p>}
      {file === 'QUARANTINED' ? (
        <p className="tr-sys-type-support">Jawaban lain tetap tersimpan. Berkas ini belum dapat dipakai sampai pemeriksaan selesai.</p>
      ) : null}
      {file === 'REJECTED' ? <p className="tr-sys-type-support">Berkas ini tidak dapat dipakai. Unggah berkas lain.</p> : null}
      {action ? <div className="tr-row">{action}</div> : null}
    </article>
  );
}
