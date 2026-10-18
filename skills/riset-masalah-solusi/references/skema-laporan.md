# Skema `laporan.json`

Contoh lengkap dan valid: `templates/contoh-laporan.json` (isinya fiktif). Validator (`render.py --check`) menolak laporan yang melanggar aturan di bawah dan menunjuk jalur field yang salah.

Tipe: **teks** = string tidak kosong; **daftar teks** = array string; **sitasi** = array id sumber (angka) yang ada di `sumber`.

## Akar

| Field | Tipe | Keterangan |
|-------|------|------------|
| `meta` | objek | `judul`, `topik`, `wilayah`, `tanggal` (semua teks wajib); `penyusun` opsional; `mode` opsional: `lengkap` (default) atau `ringkas` (lihat bawah) |
| `ringkasan_eksekutif` | teks | 2-4 paragraf (pisah dengan baris kosong). Boleh memakai sitasi `[1, 2]` |
| `metodologi` | objek | `pendekatan` (teks, wajib); `langkah` (daftar teks), `keterbatasan` (daftar teks) opsional |
| `profil_wilayah` | objek | `ringkasan` (teks), `kondisi_digital` (teks), `indikator` (daftar objek) |
| `masalah` | array | minimal 1; minimal 1 berstatus `prioritas` |
| `solusi` | array | minimal 1 |
| `ide_gugur` | array | opsional, tapi wajib diisi bila ada ide yang gugur |
| `prototipe` | objek | opsional; diisi bila user meminta prototipe dari salah satu solusi (lihat di bawah) |
| `sumber` | array | minimal 2 |

`profil_wilayah.indikator[]`: `nama`, `nilai`, `tahun` (teks), `sumber` (sitasi). Peringatan bila kosong.

## `sumber[]`

| Field | Aturan |
|-------|--------|
| `id` | angka bulat unik (1, 2, 3, ...) |
| `judul`, `penerbit`, `tanggal` | teks; `tanggal` sebaiknya memuat tahun (mis. `Maret 2025`) |
| `url` | harus diawali `http://` atau `https://`. Spasi, `[ ]`, `( )`, dan karakter lain yang memutus link otomatis di-encode oleh `render.py` (mis. spasi menjadi `%20`); `%` yang sudah ada dibiarkan |
| `jenis` | `data` / `resmi` / `berita` / `jurnal` / `lainnya` |

Sumber yang tidak pernah dikutip memicu peringatan.

## `masalah[]`

| Field | Aturan |
|-------|--------|
| `id` | unik, mis. `M1` |
| `judul`, `deskripsi` | teks |
| `status` | `prioritas` / `terlayani` / `tidak_prioritas` |
| `skor` | objek: `dampak`, `urgensi`, `bukti`, `kelayakan_digital`, masing-masing bilangan bulat 1-5. Total maks 20 |
| `bukti` | minimal 1 objek `{fakta, sumber}` |
| `pihak_terdampak` | teks, wajib untuk `prioritas` |
| `akar_masalah` | daftar teks, wajib untuk `prioritas` |
| `solusi_existing` | daftar `{nama, celah, url?}`; **wajib** untuk `terlayani`, disarankan untuk lainnya |
| `catatan_non_software` | teks opsional: bagian masalah yang tidak bisa diselesaikan software |

Aturan khusus `prioritas`: bukti harus mengutip **minimal 2 sumber berbeda**, dan **minimal 1 berjenis `data` atau `resmi`**.

## `solusi[]`

| Field | Aturan |
|-------|--------|
| `id` | unik, mis. `S1` |
| `masalah_id` | harus ada di `masalah` (sebaiknya berstatus `prioritas`) |
| `nama`, `tagline`, `ringkasan` | teks; `ringkasan` boleh beberapa paragraf |
| `target_pengguna` | minimal 1 objek `{persona, kebutuhan}` |
| `value_proposition` | teks |
| `fitur_mvp` | daftar teks, minimal 3 |
| `fitur_lanjutan` | daftar teks, minimal 1 |
| `platform` | teks |
| `jenis_solusi` | opsional: `software` (default bila tidak diisi) atau `software_hardware`. Lihat bagian `perangkat_keras` di bawah |
| `perangkat_keras` | objek; **wajib** bila `jenis_solusi` = `software_hardware`, **dilarang** untuk `software` |
| `tech_stack` | minimal 3 objek `{lapisan, teknologi}` |
| `arsitektur` | teks |
| `integrasi_data` | daftar teks, minimal 1 |
| `kebaruan` | lihat di bawah |
| `kompetitor` | daftar `{nama, kekuatan, kelemahan}`; peringatan bila kosong |
| `model_bisnis` | teks |
| `mitra`, `regulasi` | daftar teks, minimal 1 |
| `risiko` | minimal 2 objek `{risiko, mitigasi}` |
| `roadmap` | minimal 3 objek `{fase, durasi, target}` |
| `metrik` | daftar teks, minimal 2 |
| `penilaian` | objek: `dampak` (1-5), `kompleksitas` (1-5), `waktu_mvp` (teks). Dipakai untuk Matriks Rekomendasi |
| `sumber` | sitasi, minimal 1 |

### `solusi[].perangkat_keras`

Hanya untuk `jenis_solusi: "software_hardware"` (webcam, CCTV/kamera IP, Raspberry Pi atau komputer mini, mikrokontroler, sensor, edge AI). Panduan isinya ada di `perangkat-keras.md`.

| Field | Aturan |
|-------|--------|
| `ringkasan` | teks: peran perangkat keras dalam solusi dan di mana dipasang |
| `data_sensor` | teks: data apa yang ditangkap (gambar, suhu, arus, berat, dsb.) dan seberapa sering |
| `perangkat` | minimal 1 objek (daftar komponen / BOM): `nama`, `fungsi`, `spesifikasi`, `perkiraan_biaya` (teks, semua wajib); opsional `jumlah` (teks, mis. "1 per titik"), `sumber` (sitasi harga/spesifikasi), `url` (halaman produk, harus http(s)). Peringatan bila `sumber` tidak diisi |
| `pemrosesan` | `edge` / `cloud` / `hibrida` |
| `pemrosesan_keterangan` | teks: apa yang dihitung di mana, model yang dipakai, data apa yang dikirim |
| `konektivitas_daya` | teks: jaringan, mode offline, sumber daya, pemulihan setelah mati listrik |
| `instalasi_pemeliharaan` | teks: pemasangan, lingkungan, perawatan rutin, pengganti |
| `biaya` | teks: biaya per titik dan biaya berulang (data, listrik, perawatan), dengan dasar perhitungan |
| `pengadaan` | teks: sumber komponen lokal, waktu tunggu, alternatif, syarat pengadaan (e-katalog, TKDN) |
| `privasi_keselamatan` | daftar teks, minimal 1: privasi (UU PDP), pemberitahuan, sertifikasi perangkat, keselamatan kelistrikan, keamanan siber |

Bila ada solusi `software_hardware`, laporan menambah kolom "Jenis" di tabel ringkasan dan Matriks Rekomendasi, mengubah judul bagian 6 menjadi "Solusi Software dan Perangkat Keras", menambah subbagian "Perangkat keras dan integrasi" serta "Privasi dan keselamatan perangkat" di tiap kartu solusi, dan menambah catatan metodologi. Laporan tanpa solusi berperangkat keras tidak berubah.

### `solusi[].kebaruan`

| Field | Aturan |
|-------|--------|
| `verdict` | `BELUM_ADA` / `ADA_DI_WILAYAH_LAIN` / `PERNAH_ADA_TIDAK_AKTIF`. `SUDAH_ADA_DI_WILAYAH` **ditolak** |
| `ringkasan` | teks, kesimpulan cek kebaruan |
| `pembeda` | teks, apa yang membuat solusi ini berbeda dari yang ada |
| `log_pencarian` | minimal 3 objek `{kanal, query, hasil}` |
| `referensi_serupa` | wajib (minimal 1) untuk `ADA_DI_WILAYAH_LAIN` dan `PERNAH_ADA_TIDAK_AKTIF`: `{nama, lokasi, catatan, url?}` |

Untuk solusi `software_hardware`, `log_pencarian` minimal memuat satu kanal khusus perangkat keras (marketplace, e-katalog, vendor CCTV/IoT, atau proyek kampus); lihat `cek-kebaruan.md`.

## `ide_gugur[]`
`nama`, `alasan` (teks), `ditemukan` (`{nama, url}` sistem yang sudah ada; `url` wajib diawali `http://` atau `https://`), `masalah_id` opsional (harus ada bila diisi).

Aturan `url` yang sama berlaku untuk field `url` opsional di `solusi_existing` dan `referensi_serupa`: bila diisi, harus diawali `http://` atau `https://`.

## `prototipe` (opsional)
Muncul sebagai bagian "Prototipe" sebelum Matriks Rekomendasi.

| Field | Aturan |
|-------|--------|
| `solusi_id` | harus ada di `solusi` |
| `url` | tautan prototipe, diawali `http://` atau `https://` |
| `ringkasan` | teks, apa yang dibangun dan mode kerjanya |
| `skenario` | daftar teks, minimal 1: skenario proses yang didemokan |
| `cara_mencoba` | daftar teks, minimal 1 |
| `batasan` | daftar teks opsional: apa yang tidak didemokan atau belum diuji. Tulis jujur, termasuk bagian yang belum diuji di lingkungan sebenarnya |

## Mode ringkas (`meta.mode: "ringkas"`)
Menghasilkan laporan sekitar 15 halaman (kira-kira 3.500 kata). Perbedaan:
- Validator tidak mewajibkan `solusi[].arsitektur`, `target_pengguna`, `fitur_lanjutan`, `integrasi_data`, `mitra` (bila diisi tetap divalidasi) dan tidak memberi peringatan `kompetitor` kosong.
- Laporan menyembunyikan: langkah metodologi dan penjelasan skor, Detail Masalah untuk masalah `tidak_prioritas` (tetap ada di tabel prioritas), subbagian Fitur lanjutan, Arsitektur, Integrasi, Kompetitor, dan Mitra di kartu solusi. `target_pengguna` yang diisi menjadi satu kalimat "Pengguna". Log pencarian disajikan satu tabel gabungan.
- Tetap ditampilkan: ringkasan eksekutif, profil, tabel prioritas, bukti, akar masalah, solusi yang sudah ada, kartu solusi inti (ringkasan, value proposition, fitur MVP, tech stack, blok perangkat keras, kebaruan, model bisnis, regulasi, risiko, roadmap, metrik), prototipe, matriks, ide gugur, log, dan daftar pustaka.
- `render.py` mencetak perkiraan jumlah kata dan halaman; peringatan bila melebihi sekitar 3.800 kata.
- Opsi CLI `--ringkas` dan `--lengkap` menimpa `meta.mode` tanpa mengubah JSON.

## Format teks
Dalam string: `**tebal**`, `` `kode` ``, `[teks](https://url)`, URL polos, sitasi `[1]` / `[1, 3]`. Paragraf dipisah baris kosong. Hindari emoji dan heading. Link tidak ditampilkan di judul dan heading (otomatis jadi teks biasa).

## Isi laporan yang dihasilkan
Sampul, Daftar Isi, 1 Ringkasan Eksekutif (dengan tabel masalah → solusi), 2 Metodologi, 3 Profil Wilayah, 4 Peta dan Prioritas Masalah, 5 Detail Masalah, 6 Solusi Software (satu kartu lengkap per solusi), 7 Prototipe (bila `prototipe` diisi; tanpa itu Matriks menjadi bagian 7), 8 Matriks Rekomendasi, Lampiran A Ide yang Gugur, B Log Pencarian Kebaruan, C Daftar Pustaka.
