import type { FeedbackAction, FeedbackResult } from '@/api/client';
import { formatDateTime } from '@/lib/format';

export const ACTION_LABELS: Record<FeedbackAction, string> = {
  useful: 'Berguna',
  not_relevant: 'Kurang relevan',
  snooze: 'Tunda hingga besok',
  hide: 'Sembunyikan',
  restore: 'Pulihkan',
};

/** What the service confirmed, in words. Never shown before acknowledgment. */
export function confirmedText(result: FeedbackResult, timezone: string): string {
  switch (result.action) {
    case 'snooze':
      return `Ditunda hingga ${formatDateTime(result.until!, timezone)} menurut jam lokasi. Setelah itu saran ini tampil lagi.`;
    case 'hide':
      return 'Saran ini disembunyikan. Anda dapat memulihkannya dari Saran tersembunyi.';
    case 'restore':
      return 'Saran ini ditampilkan lagi.';
    default:
      return `Umpan balik tersimpan: ${ACTION_LABELS[result.action]}.`;
  }
}
