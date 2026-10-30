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

Framework failures use the status map in `public.py`: `UNAUTHORIZED` 401, `FORBIDDEN` 403, `METHOD_NOT_ALLOWED` 405, `VALIDATION_FAILED` 422, `RATE_LIMITED` 429.
