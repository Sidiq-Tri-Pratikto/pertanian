import { Status } from '@/components/tr/Status';

export const TIMING_LABEL: Record<string, string> = { CURRENT: 'Saat ini', PLANNED: 'Direncanakan', REQUESTED: 'Diminta' };
export const SOURCE_LABEL: Record<string, string> = {
  SOURCE_REPORTED: 'Dilaporkan sumber',
  SELF_DECLARED: 'Dinyatakan sendiri',
  PROVIDED: 'Disediakan, belum diperiksa',
  REVIEWED: 'Diperiksa untuk kriteria ini',
  UNKNOWN: 'Belum diketahui',
};

/** Port of TR.FactSource: a value, whether it exists now or is planned, and who says so. Only REVIEWED gets a check. */
export function FactSource({ value, timing, provenance }: { value?: string; timing?: string; provenance?: string }) {
  const reviewed = provenance === 'REVIEWED';
  return (
    <span className="tr-fact">
      {value ? <strong className="tr-fact__value">{value}</strong> : null}
      {timing ? <span className={`tr-tag tr-sys-type-support tr-tag--${timing.toLowerCase()}`}>{TIMING_LABEL[timing]}</span> : null}
      {provenance ? (
        reviewed ? (
          <Status tone="success" label={SOURCE_LABEL.REVIEWED} />
        ) : (
          <span className="tr-tag tr-sys-type-support">{SOURCE_LABEL[provenance]}</span>
        )
      ) : null}
    </span>
  );
}
