---
name: riset-masalah-solusi
description: Menerima topik/tema dan wilayah (kota, kabupaten, provinsi, desa, atau negara), lalu meriset permasalahan nyata di wilayah itu dengan data dan sumber bertanggal, memprioritaskannya, dan mengusulkan solusi software/aplikasi, termasuk software yang terintegrasi perangkat keras (webcam, CCTV/kamera IP, Raspberry Pi, ESP32, sensor IoT, edge AI), yang BELUM diimplementasikan di wilayah tersebut (lengkap dengan cek kebaruan, tech stack, daftar komponen dan biaya perangkat bila ada, fitur MVP, model bisnis, risiko, roadmap). Hasil berupa laporan Markdown dan PDF (LaTeX). Gunakan saat user minta "cari masalah di daerah X soal Y", "apa masalah <topik> di <kota>", "ide aplikasi untuk menyelesaikan masalah <tema> di <wilayah>", "riset masalah dan solusi teknologi", "problem discovery", "peluang startup/civic-tech di <wilayah>", atau "solusi digital yang belum ada untuk <topik>", "solusi IoT/sensor/kamera untuk <masalah> di <wilayah>", atau "computer vision di CCTV untuk <topik>".
argument-hint: "<topik> di <wilayah>"
---

# Riset Masalah dan Solusi Software

Alur: **topik + wilayah → masalah berbukti → prioritas → ide solusi (software, atau software terintegrasi perangkat keras) → cek kebaruan di wilayah → laporan MD + PDF.**

Lokasi skill: `~/.claude/skills/riset-masalah-solusi/`

| File | Dibaca kapan |
|------|--------------|
| `references/sumber-data.md` | Langkah 2-3, untuk memilih sumber data Indonesia atau global |
| `references/cek-kebaruan.md` | Langkah 7, sebelum mengecek kebaruan ide |
| `references/perangkat-keras.md` | Langkah 2, 6, dan 8 bila solusi memakai webcam, CCTV, Raspberry Pi, sensor, atau perangkat edge; juga untuk prototipe berperangkat keras |
| `references/skema-laporan.md` | Langkah 9, sebelum menulis `laporan.json` |
| `templates/contoh-laporan.json` | Langkah 9, sebagai bentuk acuan (isinya fiktif, jangan disalin sebagai fakta) |
| `scripts/render.py` | Langkah 9, mengubah JSON menjadi `.md`, `.tex`, `.pdf` |

Prasyarat: `python3` dan `tectonic` (`brew install tectonic`). Tanpa tectonic, `.md` dan `.tex` tetap jadi; beri tahu user cara memasangnya.

## Aturan yang tidak boleh dilanggar

1. **Jangan mengarang data, angka, sumber, atau nama aplikasi.** Setiap angka dan klaim faktual harus punya sumber di daftar `sumber` (judul, penerbit, tanggal, URL yang benar-benar kamu buka atau temukan). Jika data tidak ditemukan, tulis itu apa adanya dan turunkan skor bukti; jangan menebak.
   **Ringkasan hasil WebSearch bukan sumber.** Ia bisa memuat angka atau nama aplikasi yang tidak ada di artikel aslinya (pada uji coba, tiga klaim tidak terkonfirmasi setelah artikelnya dibuka). Buka sumbernya dengan WebFetch sebelum mengutip. Klaim yang tidak terkonfirmasi dibuang dan dicatat di `metodologi.keterbatasan`. Jika situs menolak akses (HTTP 403), cari sumber alternatif atau tulis bahwa angkanya dikutip dari media.
2. **Solusi yang sudah ada di wilayah itu tidak boleh direkomendasikan.** Ide yang gugur masuk `ide_gugur`, bukan `solusi`.
3. **Jangan menulis `.tex` atau `.md` laporan langsung.** Tulis `laporan.json`, lalu jalankan `render.py`. Ini yang menjaga MD dan PDF konsisten dan karakter khusus LaTeX aman.
4. Hanya gunakan informasi publik. Jangan menargetkan individu tertentu sebagai "masalah".
5. **Harga, spesifikasi, dan ketersediaan perangkat keras harus bersumber dan bertanggal** (halaman produk, datasheet, e-katalog), ditulis sebagai rentang, dan ditandai "estimasi" bila tidak ada sumbernya. Jangan menyatakan akurasi atau ketahanan perangkat di lapangan tanpa pengujian lapangan; bedakan hasil di dataset atau simulasi dengan hasil lapangan. Perangkat keras adalah sarana, bukan tujuan: ide berperangkat keras dipilih hanya bila ponsel, formulir, atau bot tidak cukup (lihat `references/perangkat-keras.md`).

## Langkah

### 1. Tangkap input
Ambil **topik/tema** dan **wilayah** dari argumen. Jika salah satunya tidak ada atau terlalu lebar (mis. hanya "Indonesia"), tanyakan dengan AskUserQuestion. Tentukan:
- jumlah masalah prioritas (default 3-5),
- **lingkup solusi**: `software` saja, `software_hardware` (ada solusi yang memakai perangkat keras seperti webcam, CCTV, Raspberry Pi, sensor), atau bebas (pilih yang paling cocok per masalah). Bila argumen atau permintaan user sudah menyebut perangkat (webcam, CCTV, kamera, Raspberry Pi, IoT, sensor, edge), anggap `software_hardware` tanpa bertanya. Bila belum jelas, tanyakan dengan AskUserQuestion, rekomendasi pertama "bebas". Pada lingkup `software_hardware`, minimal satu solusi berperangkat keras, kecuali tidak ada masalah yang layak; jelaskan alasannya bila demikian,
- **mode laporan**: `ringkas` (default, target maksimal 15 halaman) atau `lengkap` (hanya bila user meminta laporan lengkap atau mendalam). Aturan penulisan ringkas ada di bagian "Mode ringkas" di bawah,
- folder keluaran, default `./riset-<slug-topik>-<slug-wilayah>/` di folder kerja (buat bila belum ada).

Satu riset penuh butuh puluhan pencarian dan pembukaan artikel; beri tahu user bahwa ini memakan waktu. Jika wilayahnya sudah ramai ditangani pemerintah, jumlah masalah prioritas yang tersisa bisa kurang dari 3: itu hasil yang sah, jangan memaksakan masalah atau solusi demi memenuhi jumlah.

### 2. Profil wilayah
Kumpulkan: jumlah penduduk dan kepadatan, struktur ekonomi, pendapatan/kemiskinan bila relevan, dan **kondisi digital** (penetrasi internet dan smartphone, sinyal, literasi digital, bahasa daerah, QRIS/e-wallet, aplikasi pemerintah daerah yang sudah dipakai). Kondisi digital menentukan bentuk solusi di langkah 6, jadi jangan dilewati. Bila perangkat keras mungkin dipakai, catat juga kondisi lapangan yang relevan: keandalan listrik dan sinyal di titik pasang, cuaca dan debu, risiko pencurian, izin pemasangan, ketersediaan teknisi, dan ketersediaan perangkat secara lokal (lihat `references/perangkat-keras.md` bagian 4).

### 3. Temukan 5-8 kandidat masalah
Gunakan beberapa jalur, bukan hanya berita: statistik resmi, dokumen perencanaan daerah, berita 24 bulan terakhir, jurnal, dan keluhan warga. Daftar sumber ada di `references/sumber-data.md`.
- WebSearch mode `standard` dulu; pakai `extended` untuk data lokal yang sulit dicari atau fakta yang sangat spesifik wilayah. Kirim beberapa pencarian independen dalam satu giliran (paralel).
- Gunakan WebFetch untuk membuka dokumen resmi dan memastikan angka, jangan hanya mengutip cuplikan hasil pencarian. PDF terkompresi sering tidak terbaca dan beberapa situs pemerintah menolak akses otomatis (HTTP 403); cari halaman HTML atau berita yang mengutipnya, dan catat keterbatasannya.
- **Tenggat, kebijakan, harga, dan status produk bisa berubah dalam hitungan hari.** Untuk hal seperti itu cari berita 7 hari terakhir dan jangan bersandar pada satu artikel. Pada uji coba, tenggat wajib halal diperpanjang dua tahun seminggu setelah pernyataan resmi "tidak ada penundaan"; judul artikel terkait di sebuah halaman berita yang membongkarnya.
- Setiap kandidat butuh **minimal 2 sumber berbeda, satu di antaranya berjenis `data` atau `resmi`**. Kandidat yang tidak memenuhi ini dibuang atau dicatat sebagai keterbatasan.

### 4. Skor dan prioritas
Nilai 1-5 pada: `dampak`, `urgensi`, `bukti`, `kelayakan_digital` (seberapa besar porsi masalah yang bisa dibantu software, termasuk software yang terintegrasi perangkat keras). Pilih 3-5 teratas sebagai `prioritas`. Bagian masalah yang bukan urusan software (infrastruktur fisik, anggaran, regulasi) dicatat jujur di `catatan_non_software`; jangan memaksakan solusi app untuk masalah yang pada dasarnya bukan masalah software.

### 5. Akar masalah
Untuk tiap masalah prioritas: pihak terdampak, akar penyebab, dan **solusi/program yang sudah ada beserta celahnya**.

### 6. Ide solusi
Buat 2-3 ide per masalah prioritas, disesuaikan dengan kondisi digital wilayah. Pertimbangkan: offline-first, bot WhatsApp/Telegram tanpa instal, USSD/SMS untuk sinyal lemah, antarmuka bahasa daerah, aplikasi ringan untuk ponsel entry-level, integrasi dengan sistem yang sudah dipakai pemerintah daerah. Ide harus spesifik (siapa pengguna, apa yang berubah), bukan "aplikasi pelaporan umum".

Bila lingkupnya mengizinkan perangkat keras, baca `references/perangkat-keras.md` dan pertimbangkan ide yang memakai webcam, kamera IP atau CCTV yang sudah terpasang, Raspberry Pi atau komputer mini, ESP32 dengan sensor, atau meter pintar. Uji tiap ide dengan pertanyaan: *apakah data ini bisa didapat dari ponsel atau input manual?* Bila bisa, pilih software saja. Untuk ide berperangkat keras utamakan **edge-first** (proses di perangkat, kirim hasil, bukan video), **komponen murah yang mudah dibeli lokal**, **tanpa menyimpan video mentah**, dan biaya total per titik yang wajar. Tandai ide itu `jenis_solusi: software_hardware`.

### 7. Cek kebaruan (wajib untuk setiap ide)
Baca `references/cek-kebaruan.md`, lalu cek tiap ide: toko aplikasi, situs pemda/dinas, inovasi daerah, startup lokal, berita, GitHub. Minimal 3 kanal berbeda per ide, dan **catat query serta hasilnya** (masuk `log_pencarian`). Untuk ide berperangkat keras, cek juga **produk perangkat keras yang dijual dan dipasang di wilayah** (marketplace, e-katalog, vendor CCTV dan IoT, proyek kampus); minimal satu kanal harus khusus perangkat keras, dan aturannya ada di bagian "Tambahan untuk solusi dengan perangkat keras" di `references/cek-kebaruan.md`.
- `SUDAH_ADA_DI_WILAYAH` → ide gugur. Ganti dengan ide baru yang dicek ulang (maksimal 2 putaran per masalah).
- Jika semua ide untuk satu masalah gugur → ubah status masalah menjadi `terlayani` dan catat aplikasi yang ditemukan di `solusi_existing`.
- Lolos dengan label `BELUM_ADA`, `ADA_DI_WILAYAH_LAIN` (catat referensi dan cara adaptasi), atau `PERNAH_ADA_TIDAK_AKTIF` (catat pelajarannya).

### 8. Detailkan solusi yang lolos
Pada mode `lengkap`, per solusi isi semua bagian (mode `ringkas`: lihat batasan di bawah, bagian yang tidak ditampilkan boleh dikosongkan): ringkasan, target pengguna dan persona, value proposition, fitur MVP dan lanjutan, platform, tech stack per lapisan, arsitektur singkat, integrasi dan sumber data, hasil cek kebaruan dan pembeda, kompetitor/alternatif, model bisnis dan pendanaan (B2G, B2B, freemium, CSR/EPR, hibah), mitra, regulasi dan kepatuhan (mis. UU PDP 27/2022, SPBE untuk sistem pemerintah, izin pembayaran), risiko dan mitigasi, roadmap (MVP → pilot → skala), metrik keberhasilan, dan penilaian dampak/kompleksitas/waktu MVP. Pilih tech stack yang masuk akal untuk tim kecil dan kondisi wilayah, bukan sekadar yang populer.

Untuk solusi `software_hardware`, isi juga objek `perangkat_keras` (lihat `references/skema-laporan.md`): peran perangkat, data yang ditangkap, **daftar komponen (BOM) dengan perkiraan biaya bersumber dan bertanggal**, tempat pemrosesan (edge, cloud, hibrida), konektivitas dan daya, pemasangan dan perawatan, biaya per titik dan berulang, pengadaan, serta privasi dan keselamatan (UU PDP untuk kamera, sertifikasi perangkat radio, keselamatan kelistrikan, keamanan siber). Cantumkan risiko khas perangkat keras (pencurian, cuaca, listrik padam, akurasi di lapangan) di `risiko`.

### 9. Tulis laporan
1. Baca `references/skema-laporan.md` dan `templates/contoh-laporan.json`.
2. Tulis `<folder>/laporan.json`.
3. Validasi dulu bila perlu: `python3 ~/.claude/skills/riset-masalah-solusi/scripts/render.py <folder>/laporan.json --check`
4. Render:

```bash
python3 ~/.claude/skills/riset-masalah-solusi/scripts/render.py <folder>/laporan.json
```

Hasil: `laporan.md`, `laporan.tex`, `laporan.pdf` di folder yang sama. Pertama kali dijalankan, tectonic mengunduh paket LaTeX (butuh internet, beberapa menit); berikutnya cepat.
- Validator menolak laporan yang tidak lengkap dan menampilkan jalur field yang salah (mis. `solusi[0].kebaruan.log_pencarian`). Perbaiki JSON, jalankan lagi.
- Jika kompilasi PDF gagal, baca potongan log yang ditampilkan, perbaiki JSON (biasanya URL atau karakter aneh), ulangi. Jangan menyunting `.tex` secara manual.
- Periksa PDF hasil: buka halaman-halaman utamanya dan pastikan tabel, link, dan kartu solusi tampil benar sebelum melapor selesai.

### Mode ringkas (default)

Laporan lengkap bisa mencapai 30 sampai 40 halaman dan sulit dibaca. Mode ringkas menargetkan **maksimal sekitar 15 halaman (kira-kira 3.500 kata)**. Panjang laporan ditentukan terutama oleh jumlah masalah dan solusi serta panjang teksnya, bukan oleh render, jadi tulis ringkas dari awal. Isi `"mode": "ringkas"` di `meta` pada `laporan.json`; `render.py` menyembunyikan bagian sekunder dan menampilkan perkiraan panjang (peringatan bila lebih dari anggaran).

Batas penulisan:
- **Masalah prioritas 3 (maksimal 4).** Masalah lain cukup baris di tabel (`tidak_prioritas`: deskripsi satu kalimat dan satu bukti; tidak ditampilkan di Detail Masalah).
- **Satu solusi per masalah prioritas, maksimal 3 solusi.** Pilih yang terkuat setelah cek kebaruan; ide lain yang lolos cukup disebut di `ringkasan_eksekutif`.
- Ringkasan eksekutif 2 paragraf (maks 180 kata). `deskripsi` masalah maks 60 kata; `bukti` 2 sampai 3 butir (maks 30 kata); `akar_masalah` 2 sampai 3 butir.
- `solusi.ringkasan` satu paragraf (maks 80 kata); `fitur_mvp` 3 sampai 5 butir singkat; `tech_stack` 3 sampai 4 baris; `risiko` 2; `roadmap` 3; `metrik` 2; `kebaruan.ringkasan` 1 sampai 2 kalimat.
- `log_pencarian` tetap minimal 3 kanal per ide (aturan 1 dan langkah 7 tidak dilonggarkan), `sumber` hanya yang benar-benar dikutip (kira-kira 12 sampai 18).
- Boleh dikosongkan (tidak ditampilkan di mode ringkas): `fitur_lanjutan`, `arsitektur`, `integrasi_data`, `mitra`, `kompetitor`, `metodologi.langkah`; `target_pengguna` bila diisi menjadi satu kalimat.
- **Tidak boleh dipangkas**: bukti dan sumber, cek kebaruan dan log pencarian, regulasi, risiko, dan untuk solusi berperangkat keras blok `perangkat_keras` (BOM, privasi, keselamatan). Ringkas berarti lebih sedikit dan lebih padat, bukan lebih lemah buktinya.

Setelah render, baca baris `INFO` atau `PERINGATAN mode ringkas` dari `render.py`. Bila melebihi anggaran, persingkat teks atau kurangi solusi dan render ulang. `render.py laporan.json --lengkap` merender mode lengkap dari JSON yang sama bila isinya cukup.

### Opsional: prototipe
Bila user meminta prototipe (mis. agen percakapan yang mendemonstrasikan satu skenario proses), jangan memilih solusinya sendiri: tanyakan solusi mana lewat AskUserQuestion setelah laporan selesai, dengan rekomendasi di opsi pertama. Lalu:
- Bangun satu halaman mandiri dan publikasikan sebagai Artifact. Untuk agen yang memahami bahasa bebas, pakai kemampuan `sample` dengan `tools` (fungsi di halaman): **aturan bisnis dan validasi ada di kode halaman**, Claude hanya memilih fungsi dan menyusun bahasa. Sediakan mode skrip berbasis tombol sebagai cadangan bila `sample` tidak tersedia, ditolak, atau kena batas.
- Uji di browser lokal sebelum publikasi: skenario penuh, aturan peran dan validasi (kasus yang harus ditolak), lebar ponsel 375 px, dan tema gelap. Fragmen halaman tidak punya meta viewport sampai kerangka publikasi menambahkannya, jadi uji lebar ponsel pada salinan sementara yang menambahkan meta itu, lalu hapus salinannya.
- Jalur Claude yang sesungguhnya butuh persetujuan penonton di claude.ai dan tidak bisa diuji dari sesi ini. Uji dengan penyedia jawaban simulasi yang memanggil fungsi sungguhan, dan katakan terus terang bagian mana yang belum teruji.
- Solusi berperangkat keras: Artifact tidak bisa memakai kamera atau mikrofon dan tidak bisa menjangkau perangkat fisik. Bangun halaman simulasi yang menerima foto atau video contoh, atau skrip lokal yang bisa dijalankan (mis. Python dengan OpenCV) pada berkas video atau webcam laptop, dan uji sebelum melapor. Cantumkan di `batasan` bahwa pengujian lapangan (cahaya, cuaca, uptime, pemasangan) belum dilakukan. Lihat `references/perangkat-keras.md` bagian 8.
- Isi field `prototipe` di `laporan.json` (lihat `references/skema-laporan.md`), termasuk `batasan`, lalu render ulang laporan.

### 10. Ringkas di chat
Berikan:
- tabel singkat **masalah → solusi → label kebaruan**,
- 2-3 kalimat temuan paling penting (angka kunci beserta sumbernya),
- path file `.md`, `.tex`, `.pdf` sebagai link,
- masalah yang `terlayani` atau ide yang gugur, bila ada (user sering ingin tahu apa yang sudah ada),
- untuk solusi berperangkat keras: perangkat utama, perkiraan biaya per titik beserta sumber dan tanggalnya, dan bagian yang belum teruji di lapangan,
- catatan penutup: cek kebaruan berbasis pencarian publik pada tanggal riset, bukan jaminan 100%; solusi perlu divalidasi dengan calon pengguna dan pemerintah daerah sebelum dibangun.

## Format teks di dalam `laporan.json`

Semua string mendukung: `**tebal**`, `` `kode` ``, `[teks](https://url)`, URL polos, dan sitasi `[1]` atau `[1, 3]` (nomor dari daftar `sumber`, menjadi link ke Daftar Pustaka). Pisahkan paragraf dengan baris kosong (`\n\n`). Jangan pakai emoji, tabel Markdown, atau heading di dalam string. Karakter `% & _ # $ { }` boleh ditulis apa adanya; script yang meng-escape.

## Jika wilayah di luar Indonesia
Pakai sumber internasional dan portal pemerintah lokal (lihat bagian global di `references/sumber-data.md`), tulis laporan dalam bahasa user, dan sesuaikan regulasi (mis. GDPR, aturan fintech setempat) serta metode pembayaran lokal. Untuk solusi berperangkat keras, sesuaikan juga sertifikasi perangkat radio, standar kelistrikan (voltase dan colokan), dan aturan privasi kamera setempat.
