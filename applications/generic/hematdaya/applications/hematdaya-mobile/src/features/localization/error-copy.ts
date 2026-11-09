import { ApiError } from '@/api/errors';
import { getLocale } from '@/features/localization/locale';
import { currentCopy } from '@/features/localization/messages';

const LOCAL_MESSAGES: Record<string, readonly [string, string]> = {
  OFFLINE_UNSENT: ['Belum dikirim. Sambungkan perangkat lalu coba lagi.', 'Request not sent. Reconnect and try again.'],
  WORKSPACE_CHANGED: ['Ruang kerja berubah. Buka ruang kerja aktif dan coba lagi.', 'The workspace changed. Open the active workspace and try again.'],
  LOCAL_STORAGE: ['Periksa penyimpanan perangkat lalu coba lagi.', 'Check your device storage and try again.'],
  PILOT_ACCESS_EXPIRED: ['Kode akses sudah kedaluwarsa. Minta kode baru dari pengelola uji coba.', 'The access code expired. Ask the pilot operator for a new one.'],
  SESSION_EXPIRED: ['Sesi demo sudah berakhir. Mulai sesi baru.', 'The demo has ended. Start a new session.'],
  NETWORK_UNREACHABLE: ['Periksa koneksi Anda lalu coba lagi.', 'Check your connection and try again.'],
  UNEXPECTED_RESPONSE: ['Jawaban layanan tidak dikenali. Coba lagi nanti.', 'We received an unexpected response. Try again later.'],
  SCOPE_CONFLICT: ['Tinjau cakupan dan sumber, lalu buat pratinjau baru.', 'Review the scope and sources, then preview again.'],
  IMPORT_BLOCKED: ['Periksa masalah di pratinjau impor.', 'Review the problems in the import preview.'],
  IMPORT_STALE: ['Buat pratinjau impor baru.', 'Create a new import preview.'],
  NOT_FOUND: ['Data tidak ditemukan.', 'Data not found.'],
};

/** A cached failure stays recoverable when its service copy is in the previous language. */
export function errorMessage(value: unknown): string | undefined {
  if (value == null) return undefined;
  const error = ApiError.from(value);
  if (error.language === getLocale()) return error.message;
  return currentCopy(...(LOCAL_MESSAGES[error.code] ?? [
    'Permintaan belum berhasil. Periksa rincian di layar.',
    'The request did not complete. Review the details on this screen.',
  ]));
}
