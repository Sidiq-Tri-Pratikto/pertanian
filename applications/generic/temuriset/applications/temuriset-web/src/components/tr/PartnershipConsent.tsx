'use client';

import { Button } from '@/components/tr/Button';
import { Checkbox } from '@/components/tr/Checkbox';
import { Status } from '@/components/tr/Status';
import { FIELD_LABEL, FIELDS, TYPE_LABEL, type Partnership, type PublicField } from '@/features/relationships/model';

const LABEL: Record<Partnership['current']['status'], string> = {
  PENDING_COUNTERPARTY: 'Menunggu konfirmasi',
  CONFIRMED: 'Dikonfirmasi kedua pihak',
  CHANGES_REQUESTED: 'Perubahan diminta',
  DECLINED: 'Ditolak',
};

type Props = {
  record: Partnership;
  actingPartyId: string;
  selected: PublicField[];
  onToggle: (field: PublicField, checked: boolean) => void;
  onRestrict?: (field: PublicField) => void;
};

/** Port of TR.PartnershipConsent. The service supplies the current status and the effective public fields. */
export function PartnershipConsent({ record, actingPartyId, selected, onToggle, onRestrict }: Props) {
  const { current, effective } = record;
  const mine = current.confirmations.find((confirmation) => confirmation.party_id === actingPartyId);
  const canSelect = record.allowed_actions.includes('confirm') && !mine;
  const fields = FIELDS.filter((field) => current.ceiling.includes(field));
  const effectiveHere = effective.version === current.number ? effective.fields : [];
  return (
    <section className="tr-consent" aria-labelledby="judul-izin">
      <div className="tr-req__head">
        <h2 id="judul-izin" className="tr-sys-type-heading-sm">Ringkasan Kerja Sama · Versi {current.number}</h2>
        <Status label={LABEL[current.status]} tone={current.status === 'CONFIRMED' ? 'success' : 'neutral'} live />
      </div>
      <p className="tr-muted">{TYPE_LABEL[record.type]}</p>
      <h3 className="tr-sys-type-label">Yang boleh tampil di publik</h3>
      <p className="tr-sys-type-support">Hanya data yang diizinkan kedua pihak yang tampil. Data lain tetap privat.</p>
      <ul className="tr-consent__list">
        {fields.map((field) => {
          const visible = effectiveHere.includes(field);
          const restricted = record.restrictions.some((restriction) => restriction.field === field);
          return (
            <li key={field} className="tr-consent__row">
              {canSelect && !restricted ? (
                <Checkbox label={FIELD_LABEL[field]} checked={selected.includes(field)} onChange={(checked) => onToggle(field, checked)} />
              ) : <p className="tr-sys-type-label">{FIELD_LABEL[field]}</p>}
              <p className="tr-consent__parties tr-sys-type-support">
                {record.parties.map((party, index) => {
                  const choice = current.confirmations.find((item) => item.party_id === party.party_id);
                  const permission = choice ? (choice.subset.includes(field) ? 'Diizinkan' : 'Tidak diizinkan') : 'Belum mengonfirmasi';
                  return <span key={party.party_id}>{index ? ' · ' : ''}{party.name}: {permission}</span>;
                })}
              </p>
              <div className="tr-consent__result">
                <Status label={visible ? 'Tampil di publik' : restricted ? 'Disembunyikan' : 'Tetap privat'} tone={visible ? 'success' : 'neutral'} />
                {visible && onRestrict ? <Button onClick={() => onRestrict(field)}>Sembunyikan<span className="tr-sr"> {FIELD_LABEL[field]}</span></Button> : null}
              </div>
            </li>
          );
        })}
      </ul>
      {record.restrictions.length ? <p className="tr-sys-type-support">Data yang disembunyikan langsung hilang dari tampilan publik. Salinan yang sudah diunduh pihak lain tidak dapat ditarik.</p> : null}
    </section>
  );
}
