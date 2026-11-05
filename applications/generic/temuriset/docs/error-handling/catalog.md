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
| `APP-FORBIDDEN` | `FORBIDDEN` | 403 | Anda tidak memiliki akses untuk permintaan ini. Hubungi pemilik data bila perlu akses. | A cookie-bearing unsafe request from another origin; from 007, a visible resource without the capability | false | - | - |
| `APP-CODE-INVALID` | `CODE_INVALID` | 422 | Kode verifikasi tidak cocok. Periksa kode di email Anda lalu coba lagi. | Wrong sign-in code; the envelope adds `attempts_left` | false | - | - |
| `APP-CODE-EXPIRED` | `CODE_EXPIRED` | 422 | Kode verifikasi sudah tidak berlaku. Minta kode baru lalu masukkan kode tersebut. | No open code, older than 10 minutes, or five wrong guesses | false | - | - |
| `APP-RATE-LIMITED` | `RATE_LIMITED` | 429 | Terlalu banyak permintaan kode. Tunggu sebentar lalu coba lagi. | Over 5 code requests per email or 20 per address in an hour; `retry_after_seconds` says when the window frees up | true | per request | 3 |
| `APP-STALE-CONTEXT` | `STALE_CONTEXT` | 409 | Anda kini bertindak sebagai pihak lain di tab berbeda. Muat ulang halaman lalu ulangi tindakan Anda. | `acting_party_id` differs from the session's active party | false | - | - |
| `APP-INVITATION-EXPIRED` | `INVITATION_EXPIRED` | 410 | Undangan ini sudah tidak berlaku. Minta undangan baru kepada pengelola organisasi. | Invitation older than seven days, revoked, or already accepted | false | - | - |
| `APP-PUBLICATION-INVALID` | `VALIDATION_FAILED` | 422 | Draf belum siap diterbitkan. Lengkapi isian yang ditandai lalu terbitkan lagi. | Publishing a draft that breaks a PRD publication rule; `details` names each field in Indonesian | false | - | - |

A missing `Idempotency-Key` on a consequential POST is `BAD_REQUEST` with `details` naming the header.

Framework failures use the status map in `public.py`: `UNAUTHORIZED` 401, `FORBIDDEN` 403, `METHOD_NOT_ALLOWED` 405, `VALIDATION_FAILED` 422, `RATE_LIMITED` 429.
