import type { ComponentRef, Ref } from 'react';
import { StyleSheet, View, type TextInstance } from 'react-native';

import type { ImportPreview, ImportRowError } from '@/api/client';
import { HDButton } from '@/components/hd/HDButton';
import { HDChoiceGroup } from '@/components/hd/HDChoiceGroup';
import { HDDisclosure } from '@/components/hd/HDDisclosure';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDText } from '@/components/hd/HDText';
import { tokens } from '@/design/tokens.generated';
import { rowErrorText } from '@/features/imports/import-model';
import { formatDateRange } from '@/lib/format';

type Counts = Pick<ImportPreview, 'total_rows' | 'accepted_rows' | 'invalid_rows' | 'duplicate_rows' | 'conflict_rows' | 'pending_rows'>;

type HDImportPreviewProps = {
  fileName: string;
  period: ImportPreview['period'];
  /** The service's counts, shown as sent. Nothing here adds, subtracts or divides them. */
  counts: Counts;
  blockReasons: string[];
  needsAcknowledgment: boolean;
  acknowledged: boolean;
  onAcknowledge: (acknowledged: boolean) => void;
  ackError: string | null;
  /** While a commit is pending, unknown or being checked, the payload must not change under its key. */
  ackLocked: boolean;
  assumptions: string[];
  notes: string[];
  /** Lines describing the column mapping, inside a disclosure. */
  mapping: string[];
  errors: ImportRowError[];
  onMoreErrors?: () => void;
  loadingMore: boolean;
  /** Focus targets for an error summary's links. */
  rowTarget?: (key: string) => Ref<ComponentRef<typeof View>>;
  ackTarget?: Ref<ComponentRef<typeof View>>;
  listTarget?: Ref<TextInstance>;
};

export const ROW_CONVENTION =
  'Nomor baris data tidak menghitung header dan baris kosong. Baris berkas adalah nomor baris pada berkas, termasuk header.';

export function rowKey(error: ImportRowError): string {
  return `row-${error.data_row}-${error.field}`;
}

const ACK_VALUE = 'ack';
// Two counts share a row on a phone, and each still fits alone in a 128 px column (160 px at 200% text).
const COUNT_BASIS = 120;
// Web only: an error summary's link can focus a row without adding it to the tab order.
const FOCUSABLE_BY_SCRIPT = { tabIndex: -1 } as object;

/**
 * A stored preview: counts, period, the service's reasons and assumptions, row errors with the service's file
 * lines, and the acknowledgment. Confirm, status and summary stay with the screen, which owns the footer.
 */
export function HDImportPreview({
  fileName,
  period,
  counts,
  blockReasons,
  needsAcknowledgment,
  acknowledged,
  onAcknowledge,
  ackError,
  ackLocked,
  assumptions,
  notes,
  mapping,
  errors,
  onMoreErrors,
  loadingMore,
  rowTarget,
  ackTarget,
  listTarget,
}: HDImportPreviewProps) {
  const rows: [string, number][] = [
    ['Baris data', counts.total_rows],
    ['Diterima', counts.accepted_rows],
    ['Tidak valid', counts.invalid_rows],
    ['Duplikat (dihitung sekali)', counts.duplicate_rows],
    ['Nilai berbeda', counts.conflict_rows],
    ...(counts.pending_rows > 0 ? [['Menunggu pemetaan', counts.pending_rows] as [string, number]] : []),
  ];
  const blocked = blockReasons.length > 0;

  return (
    <View style={styles.block}>
      <View style={styles.tight}>
        <HDText variant="section">{fileName}</HDText>
        <HDText>
          {period
            ? `Periode data: ${formatDateRange(period.start_date, period.end_date)} · ${period.timezone}`
            : 'Periode data: belum ada baris yang diterima'}
        </HDText>
      </View>
      <View style={styles.counts}>
        {rows.map(([label, value]) => (
          <View key={label} accessible accessibilityLabel={`${label}: ${value}`} style={styles.count}>
            <HDText variant="label" tone="secondary">
              {label}
            </HDText>
            <HDText variant="bodyStrong">{String(value)}</HDText>
          </View>
        ))}
      </View>
      {blocked ? (
        <HDNotice tone="error" title="Impor diblokir">
          <View style={styles.tight}>
            {blockReasons.map((reason) => (
              <HDText key={reason}>{reason}</HDText>
            ))}
          </View>
        </HDNotice>
      ) : (
        <HDText variant="bodyStrong">
          {counts.accepted_rows > 0
            ? `${counts.accepted_rows} baris akan disimpan.`
            : `Tidak ada baris baru; ${counts.duplicate_rows} baris sama dengan data tersimpan.`}
        </HDText>
      )}
      {needsAcknowledgment ? (
        <HDChoiceGroup
          type="checkbox"
          legend="Baris tidak valid"
          required
          error={ackError}
          disabled={ackLocked}
          options={[{
            value: ACK_VALUE,
            label: `Saya setuju ${counts.invalid_rows} baris tidak valid dilewati dan tidak diimpor.`,
            ref: ackTarget,
          }]}
          value={acknowledged ? [ACK_VALUE] : []}
          onChange={(value) => onAcknowledge(value.includes(ACK_VALUE))}
        />
      ) : null}
      {assumptions.length || notes.length ? (
        <View style={styles.tight}>
          {assumptions.map((assumption) => (
            <HDText key={assumption}>{assumption}</HDText>
          ))}
          {notes.map((note) => (
            <HDText key={note}>{note}</HDText>
          ))}
        </View>
      ) : null}
      {mapping.length ? (
        <HDDisclosure summary="Lihat pemetaan kolom">
          {mapping.map((line) => (
            <HDText key={line}>{line}</HDText>
          ))}
        </HDDisclosure>
      ) : null}
      {errors.length ? (
        <View style={styles.tight}>
          <HDText ref={listTarget} variant="section" role="heading" aria-level={2} {...FOCUSABLE_BY_SCRIPT}>
            Baris bermasalah
          </HDText>
          <HDText variant="label">{ROW_CONVENTION}</HDText>
          <View role="list" style={styles.tight}>
            {errors.map((error) => (
              <View key={rowKey(error)} ref={rowTarget?.(rowKey(error))} role="listitem" style={styles.row} {...FOCUSABLE_BY_SCRIPT}>
                <HDText>{rowErrorText(error)}</HDText>
              </View>
            ))}
          </View>
          {onMoreErrors ? (
            <HDButton variant="text" onPress={onMoreErrors} loading={loadingMore} loadingLabel="Memuat baris…">
              Muat 50 baris berikutnya
            </HDButton>
          ) : null}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  block: { gap: tokens.space.stack },
  tight: { gap: tokens.space.stackTight },
  counts: { flexDirection: 'row', flexWrap: 'wrap', gap: tokens.space.stackTight },
  count: {
    flexBasis: COUNT_BASIS,
    flexGrow: 1,
    flexShrink: 1,
    padding: tokens.space['12'],
    borderRadius: tokens.radius.control,
    backgroundColor: tokens.color.backgroundSubtle,
    gap: tokens.space['4'],
  },
  row: { paddingVertical: tokens.space['4'] },
});
