# Error Catalog

One row per error. Keep in sync with `app/core/errors/codes.py` and `public.py`. Consumers branch on the public code, never on message text. User messages are Indonesian; everything else stays English.

| Internal code | Public code | HTTP | Default message | Trigger | retryable | retry_after_seconds | max_attempts |
|---|---|---|---|---|---|---|---|
| `APP-UNKNOWN` | `INTERNAL_ERROR` | 500 | Permintaan belum dapat diselesaikan. Hubungi dukungan dan sebutkan ID referensi yang ditampilkan. | Any unrecognized failure | false | - | - |
| `APP-REQUEST-INVALID` | `BAD_REQUEST` | 400 | Permintaan belum dapat diproses. Periksa isian Anda lalu coba lagi. | Request violates a business rule | false | - | - |
| `APP-NOT-FOUND` | `NOT_FOUND` | 404 | Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi. | Resource does not exist | false | - | - |
| `APP-CONFLICT` | `CONFLICT` | 409 | Permintaan bertentangan dengan kondisi saat ini. Tinjau datanya lalu coba lagi. | State conflict | false | - | - |
| `APP-DB-ERROR` | `DATA_ERROR` | 500 | Permintaan gagal karena kesalahan data. Hubungi dukungan dan sebutkan ID referensi. | Database failure | false | - | - |
| `APP-DB-UNAVAILABLE` | `DATABASE_UNAVAILABLE` | 503 | Layanan data sedang tidak tersedia. Coba lagi beberapa menit lagi. | Connection, pool, or operational failure | true | 30 | 3 |
| `APP-CAPABILITY-UNAVAILABLE` | `CAPABILITY_UNAVAILABLE` | 403 | Fitur ini tidak tersedia pada layanan ini. Hubungi pengelola layanan bila Anda memerlukannya. | Route guarded by `require_capability` for a capability this deployment does not select | false | - | - |
| `APP-UNAUTHENTICATED` | `UNAUTHENTICATED` | 401 | Anda perlu masuk terlebih dahulu. Masuk lalu coba lagi. | No trusted acting party (until 007: the development-only `X-Party-Id` header is missing, or the service is not in development) | false | - | - |
| `APP-STALE-VERSION` | `STALE_VERSION` | 409 | Data ini sudah diubah sejak Anda membukanya. Muat ulang versi terbaru lalu ulangi perubahan Anda. | `expected_version` differs from the stored version; the envelope adds `current_version` | false | - | - |
| `APP-IDEMPOTENCY-CONFLICT` | `IDEMPOTENCY_CONFLICT` | 409 | Kunci permintaan ini sudah dipakai untuk isi berbeda. Gunakan kunci baru untuk permintaan baru. | `Idempotency-Key` reused by the same actor and operation with a different body | false | - | - |

A missing `Idempotency-Key` on a consequential POST is `BAD_REQUEST` with `details` naming the header.

Framework failures use the status map in `public.py`: `UNAUTHORIZED` 401, `FORBIDDEN` 403, `METHOD_NOT_ALLOWED` 405, `VALIDATION_FAILED` 422, `RATE_LIMITED` 429.
