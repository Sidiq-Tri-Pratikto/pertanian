import type { components } from '@/api/schema.generated';
import { t } from '@/features/i18n/t';

export type DocumentView = components['schemas']['DocumentResponse'];
export type UploadIntent = components['schemas']['UploadIntentResponse'];

const MB = 1024 * 1024;

/** The limits the service enforces, announced before anything is sent (FR-003). */
export const ACCEPTED: Record<string, { limit: number; text: string }> = {
  'application/pdf': { limit: 20 * MB, text: '20 MB untuk PDF dan DOCX' },
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': { limit: 20 * MB, text: '20 MB untuk PDF dan DOCX' },
  'image/png': { limit: 5 * MB, text: '5 MB untuk gambar' },
  'image/jpeg': { limit: 5 * MB, text: '5 MB untuk gambar' },
  'image/webp': { limit: 5 * MB, text: '5 MB untuk gambar' },
};

export const ACCEPT_ATTRIBUTE = '.pdf,.docx,.png,.jpg,.jpeg,.webp';

/** Why a chosen file cannot be sent, before any byte moves; null when it may be. */
export function refusal(file: { type: string; size: number }): string | null {
  const accepted = ACCEPTED[file.type];
  if (!accepted) return t('Jenis berkas ini tidak didukung. Pilih PDF, DOCX, PNG, JPEG atau WEBP.');
  if (file.size > accepted.limit) return t('Berkas melebihi batas {limit}. Pilih berkas yang lebih kecil.', { limit: accepted.text });
  return null;
}

/** A version is settled once its scan and text reading can no longer change on their own. */
export function settled(document: DocumentView): boolean {
  const latest = document.versions.at(-1);
  if (!latest) return true;
  if (latest.file_state === 'QUARANTINED') return false;
  return !['PENDING', 'RUNNING'].includes(latest.extraction_state);
}
