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
| `APP-ASSET-CYCLE` | `INVALID_RELATION` | 400 | Hubungan aset ini membuat aset mencakup dirinya sendiri. Pilih aset induk yang lain. | Self-reference or containment cycle | false | - | - |
| `APP-BINDING-OVERLAP` | `CONFLICT` | 409 | Aset ini sudah memiliki sumber acuan pada waktu tersebut. Akhiri sumber yang lama lalu coba lagi. | Overlapping authoritative bindings, refused by the database | false | - | - |
| `APP-DEMO-CAPACITY` | `RATE_LIMITED` | 429 | Demo sedang ramai digunakan. Tunggu sebentar lalu coba lagi. | Active demo cap or per-minute creation budget reached | true | 60 | 3 |
| `APP-SESSION-EXPIRED` | `SESSION_EXPIRED` | 401 | Sesi demo sudah berakhir. Mulai sesi demo baru untuk melanjutkan. | Known demo token past its expiry, before purge | false | - | - |
| `APP-SCENARIO-UNKNOWN` | `NOT_FOUND` | 404 | Skenario demo tidak ditemukan. Pilih skenario dari daftar yang tersedia. | Scenario outside the catalog | false | - | - |
| `APP-DEMO-REPLAY-PROOF-MISMATCH` | `NOT_FOUND` | 404 | Data yang diminta tidak ditemukan. Periksa alamatnya lalu coba lagi. | Known operation repeated without its replay proof; deliberately generic | false | - | - |
| `APP-DEMO-REPLAY-CONFLICT` | `CONFLICT` | 409 | Permintaan demo ini sudah dipakai untuk sesi lain atau sudah kedaluwarsa. Mulai sesi demo baru. | Proven replay with a changed payload, after its window, or for an ended session | false | - | - |
| `APP-AUTH-REQUIRED` | `UNAUTHORIZED` | 401 | Anda perlu masuk terlebih dahulu. Masuk lalu coba lagi. | No credential a resolver accepts; sends `WWW-Authenticate: Bearer` | false | - | - |

Framework failures use the status map in `public.py`: `UNAUTHORIZED` 401, `FORBIDDEN` 403, `METHOD_NOT_ALLOWED` 405, `VALIDATION_FAILED` 422, `RATE_LIMITED` 429.
