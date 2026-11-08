import { currentCopy } from '@/features/localization/messages';
import type { FeedbackAction, FeedbackResult } from '@/api/client';
import { formatDateTime } from '@/lib/format';

export function actionLabel(action: FeedbackAction): string {
  return {
    useful: currentCopy('Berguna', 'Helpful'),
    not_relevant: currentCopy('Kurang relevan', 'Not relevant'),
    snooze: currentCopy('Tunda hingga besok', 'Snooze until tomorrow'),
    hide: currentCopy('Sembunyikan', 'Hide'),
    restore: currentCopy('Pulihkan', 'Restore'),
  }[action];
}

/** What the service confirmed, in words. Never shown before acknowledgment. */
export function confirmedText(result: FeedbackResult, timezone: string): string {
  switch (result.action) {
    case 'snooze':
      return currentCopy(`Ditunda hingga ${formatDateTime(result.until!, timezone)} menurut jam lokasi. Setelah itu saran ini tampil lagi.`, `Snoozed until ${formatDateTime(result.until!, timezone)} in the site’s time zone. The insight will return then.`);
    case 'hide':
      return currentCopy("Saran ini disembunyikan. Anda dapat memulihkannya dari Saran tersembunyi.", "You can restore this insight from Hidden insights.");
    case 'restore':
      return currentCopy("Saran ini ditampilkan lagi.", "This insight is visible again.");
    default:
      return currentCopy(`Umpan balik tersimpan: ${actionLabel(result.action)}.`, `Feedback saved: ${actionLabel(result.action)}.`);
  }
}
