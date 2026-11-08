import type { Locale } from '@/features/localization/locale';
import type { components } from '@/api/schema.generated';

type ErrorBody = components['schemas']['ErrorBody'];
export type Recovery = components['schemas']['ErrorRecovery'];
export type ErrorDetail = components['schemas']['ErrorFieldDetail'];
export const DEFAULT_MAX_ATTEMPTS = 3;

const UNREACHABLE_MESSAGE = 'Layanan belum dapat dihubungi. Periksa koneksi Anda lalu coba lagi.';
const UNEXPECTED_MESSAGE = 'Layanan mengirim jawaban yang tidak dikenali. Coba lagi nanti.';

/** One client-side failure. Branch on `code`; show `message` and `requestId`. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly language: Locale;
  readonly requestId: string | null;
  readonly recovery: Recovery;
  /** The specifics a refusal carries, such as each problem in a file. Shown as sent, never parsed. */
  readonly details: ErrorDetail[];

  constructor(
    code: string, message: string, recovery: Recovery, requestId: string | null = null, details: ErrorDetail[] = [],
    status: number | null = null, language: Locale = 'id',
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.language = language;
    this.recovery = recovery;
    this.requestId = requestId;
    this.details = details;
  }

  static offline(): ApiError {
    return new ApiError('OFFLINE_UNSENT', 'Permintaan belum dikirim. Sambungkan perangkat lalu coba lagi.', { retryable: false });
  }

  static revoked(): ApiError {
    return new ApiError('WORKSPACE_CHANGED', 'Ruang kerja telah berubah. Buka ruang kerja aktif lalu coba lagi.', { retryable: false });
  }

  static storage(): ApiError {
    return new ApiError('LOCAL_STORAGE', 'Penyimpanan perangkat belum dapat diperbarui. Periksa penyimpanan lalu coba lagi.', { retryable: false });
  }

  static expired(): ApiError {
    return new ApiError('SESSION_EXPIRED', 'Sesi demo sudah berakhir. Buka ruang kerja baru untuk melanjutkan.', { retryable: false });
  }

  static unreachable(): ApiError {
    return new ApiError('NETWORK_UNREACHABLE', UNREACHABLE_MESSAGE, {
      retryable: true,
      max_attempts: DEFAULT_MAX_ATTEMPTS,
    });
  }

  static unexpected(): ApiError {
    return new ApiError('UNEXPECTED_RESPONSE', UNEXPECTED_MESSAGE, { retryable: false });
  }

  /** Normalize anything caught at a call site. */
  static from(error: unknown): ApiError {
    return error instanceof ApiError ? error : ApiError.unexpected();
  }
}

function isErrorBody(value: unknown): value is ErrorBody {
  const body = value as Partial<ErrorBody> | null;
  const recovery = body?.recovery;
  return (
    typeof body?.code === 'string' && body.code.length > 0 &&
    typeof body.message === 'string' && body.message.length > 0 &&
    typeof body.request_id === 'string' && body.request_id.length > 0 &&
    typeof recovery?.retryable === 'boolean' &&
    (recovery.max_attempts == null || (Number.isInteger(recovery.max_attempts) && recovery.max_attempts >= 1)) &&
    (recovery.retry_after_seconds == null ||
      (Number.isFinite(recovery.retry_after_seconds) && recovery.retry_after_seconds >= 0))
  );
}

function isErrorDetail(value: unknown): value is ErrorDetail {
  const detail = value as Partial<ErrorDetail> | null;
  return Array.isArray(detail?.loc) &&
    detail.loc.every((part: unknown) => typeof part === 'string' || Number.isInteger(part)) &&
    typeof detail.msg === 'string' && typeof detail.type === 'string';
}

/** Keep only details of the documented shape; anything else is dropped rather than shown. */
function readDetails(value: unknown): ErrorDetail[] {
  return Array.isArray(value) ? value.filter(isErrorDetail) : [];
}

/** Read the service's failure envelope. A body that is not the envelope never leaks to the user. */
export async function readFailure(response: Response): Promise<ApiError> {
  const payload: unknown = await response.json().catch(() => null);
  const body = (payload as { error?: unknown } | null)?.error;
  if (!isErrorBody(body)) {
    return ApiError.unexpected();
  }
  const language = response.headers.get('Content-Language') === 'en' ? 'en' : 'id';
  return new ApiError(body.code, body.message, body.recovery, body.request_id,
    readDetails(body.details), response.status, language);
}
