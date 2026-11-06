'use client';

import { useId, type ReactNode } from 'react';

import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';
import { longDate, slotTime, zoneLabel } from '@/features/scheduling/time';

export type Slot = { id: string; start: string; end: string; minutes: number; conflict?: boolean; externalAvailability?: 'busy' | 'free' };

type ScheduleSlotListProps = {
  slots: Slot[];
  zone: string;
  otherZone?: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
  confirmedId?: string | null;
  state: 'open' | 'expired' | 'superseded' | 'cancelled' | 'accepted';
  /** Only the party that did not propose may confirm; the proposer sees the slots read-only. */
  canConfirm: boolean;
  onConfirm: () => void;
  onPropose: () => void;
  busy?: boolean;
  agenda?: string;
  error?: ReactNode;
};

const NOTE: Partial<Record<ScheduleSlotListProps['state'], string>> = {
  expired: 'Usulan waktu ini sudah kedaluwarsa.',
  superseded: 'Usulan ini sudah diganti usulan baru.',
  cancelled: 'Usulan ini dibatalkan.',
};

/** Port of TR.ScheduleSlotList: proposed times in the reader's zone; a selection is not a booking. */
export function ScheduleSlotList(props: ScheduleSlotListProps) {
  const { slots, zone, otherZone, selectedId, onSelect, confirmedId, state, canConfirm, onConfirm, onPropose, busy, agenda, error } = props;
  const auto = useId();
  const closed = state !== 'open';
  const note = NOTE[state];
  return (
    <div className="tr-slots">
      {agenda ? (
        <p>
          <span className="tr-muted">Agenda: </span>
          {agenda}
        </p>
      ) : null}
      {note ? <Status tone="neutral" label={note} /> : null}
      <fieldset className="tr-fieldset">
        <legend className="tr-field__label tr-sys-type-label">Pilih waktu</legend>
        <p className="tr-field__hint tr-sys-type-support">{`Waktu ditampilkan dalam ${zoneLabel(zone)}.`}</p>
        <div className="tr-choices">
          {slots.map((slot) => {
            const selected = selectedId === slot.id;
            const confirmed = confirmedId === slot.id;
            const blocked = closed || !canConfirm || Boolean(slot.conflict);
            const id = `${auto}${slot.id}`;
            return (
              <label key={slot.id} htmlFor={id} className={['tr-choice', selected && 'is-selected', blocked && !confirmed && 'is-disabled'].filter(Boolean).join(' ')}>
                <input type="radio" id={id} name={auto} checked={selected || confirmed} disabled={blocked || Boolean(confirmedId)} onChange={() => onSelect(slot.id)} />
                <span className="tr-choice__body">
                  <span className="tr-sys-type-label">{longDate(slot.start, zone)}</span>
                  <span className="tr-num">{slotTime(slot.start, slot.end, zone)}</span>
                  <span className="tr-choice__hint tr-sys-type-support">
                    {`${slot.minutes} menit${otherZone && otherZone !== zone ? ` · Pihak lain: ${slotTime(slot.start, slot.end, otherZone)}` : ''}`}
                  </span>
                  {slot.externalAvailability ? (
                    <span className="tr-choice__hint tr-sys-type-support">
                      {slot.externalAvailability === 'busy' ? 'Kalender Anda: sibuk' : 'Kalender Anda: kosong'}
                    </span>
                  ) : null}
                  {slot.conflict ? <Status tone="warning" icon="alert" label="Waktu sudah bentrok" /> : null}
                  {selected && !confirmed ? <Status tone="action" icon="clock" label="Dipilih, belum dikonfirmasi" /> : null}
                  {confirmed ? <Status tone="success" label="Waktu dikonfirmasi" /> : null}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>
      {error}
      {!closed && !confirmedId && canConfirm ? (
        <div className="tr-row">
          <Button intent="primary" busy={busy} busyLabel="Mengonfirmasi…" disabledReason={selectedId ? null : 'Pilih satu waktu terlebih dahulu.'} onClick={onConfirm}>
            Konfirmasi waktu
          </Button>
          <Button onClick={onPropose}>Usulkan waktu lain</Button>
        </div>
      ) : null}
    </div>
  );
}
