# Protokol cek kebaruan

Tujuan: memastikan solusi yang direkomendasikan **belum diimplementasikan di wilayah yang diriset**. Kesimpulan "belum ada" hanya berarti "tidak ditemukan lewat pencarian publik", jadi catat apa yang dicari supaya bisa diperiksa ulang.

## Aturan umum

- Cek **setiap ide**, bukan hanya yang favorit.
- Minimal **3 kanal berbeda** per ide. Catat `kanal`, `query` persis yang dipakai, dan `hasil` singkat (termasuk "tidak ada hasil relevan").
- Jalankan beberapa query independen **paralel** dalam satu giliran.
- Cari dengan nama wilayah **dan** padanannya (kota/kabupaten, nama resmi pemda, singkatan), serta kata kunci fungsi, bukan hanya nama produk yang kamu bayangkan.
- Cek juga **hasil yang sudah mati**: aplikasi yang pernah ada lalu ditinggalkan, karena pelajarannya berharga.
- **Baca pengumuman rekrutmen, juknis, SOP, dan syarat program pemerintah.** Sistem internal sering hanya disebut di sana (mis. "petugas wajib melapor lewat aplikasi digital") tanpa nama aplikasi atau rilis publik, sehingga pencarian nama produk tidak menemukannya. Pada uji coba, satu kalimat di berita rekrutmen menggugurkan ide aplikasi pelaporan petugas.
- **Pilot kampus dan proyek pengabdian masyarakat** (mis. sensor TPS oleh perguruan tinggi) tetap dihitung sebagai sistem yang ada bila aktif di wilayah itu dan fungsi intinya sama, meski baru di beberapa lokasi.
- Jangan memakai nama aplikasi yang hanya muncul di satu ringkasan pencarian. Buka sumbernya atau buang klaimnya.

## Kanal pencarian (Indonesia)

| Kanal | Contoh query |
|-------|--------------|
| Google Play dan App Store | `site:play.google.com <fungsi> <wilayah>`, `<fungsi> aplikasi <wilayah>` |
| Aplikasi pemda/dinas | `aplikasi <layanan> pemkot <wilayah>`, `<dinas> <wilayah> aplikasi`, `<wilayah> smart city aplikasi` |
| Inovasi daerah | Indeks Inovasi Daerah (Kemendagri), KIPP/Top Inovasi Pelayanan Publik (KemenPAN-RB), Jaga/SPBE dan portal inovasi pemda |
| Startup dan komunitas lokal | DailySocial, Tech in Asia, e27, KrASIA; komunitas dev dan inkubator kampus di wilayah |
| Berita | `<fungsi> digitalisasi <wilayah> 2025 2026`, `peluncuran aplikasi <fungsi> <wilayah>` |
| GitHub dan kompetisi | `<fungsi> <wilayah>` di GitHub, hasil hackathon dan lomba inovasi daerah |
| Program desa/kota | Desa digital, smart city, program CSR yang sudah membangun sistem serupa |
| Media sosial dan WhatsApp | Bot atau kanal resmi pemda/dinas yang menjalankan fungsi serupa |

## Kanal pencarian (wilayah luar Indonesia)
App store setempat, portal pemerintah kota/negara, Crunchbase dan Product Hunt, GitHub, berita lokal, direktori civic-tech (mis. Code for All), serta proyek smart city kota tersebut.

## Tambahan untuk solusi dengan perangkat keras

Untuk solusi yang memakai kamera, CCTV, Raspberry Pi, sensor, atau perangkat edge (lihat `perangkat-keras.md`), aplikasi saja tidak cukup dicek: **produk perangkat keras yang dijual dan dipasang di wilayah** juga bisa menggugurkan ide. Minimal 3 kanal, dan **minimal 1 kanal harus khusus perangkat keras**.

| Kanal | Contoh query |
|-------|--------------|
| Marketplace dan toko daring | `<fungsi> sensor <wilayah>`, `<fungsi> kamera AI`, `<fungsi> IoT paket` di marketplace besar; lihat apakah ada produk jadi dengan fungsi pelaporan, bukan hanya komponen |
| E-katalog dan pengadaan pemerintah | `<fungsi>` di e-katalog LKPP dan LPSE pemda; tender atau pengadaan sistem serupa |
| Vendor CCTV, IoT, dan video analytics | Situs vendor yang menjual atau memasang di Indonesia (CCTV dengan analitik bawaan seperti hitung orang atau plat nomor, penyedia IoT dan telekomunikasi); cari studi kasus dan klien di wilayah |
| Proyek kampus dan pilot | `<fungsi> prototipe sensor <wilayah>`, repositori kampus, hasil lomba inovasi, program pengabdian masyarakat |
| GitHub dan komunitas | Proyek sumber terbuka berfungsi serupa (mis. NVR atau deteksi objek di Raspberry Pi) dan komunitas maker lokal; ini rujukan teknis, bukan otomatis berarti "sudah ada" |

Aturan tambahan:
- Produk **dijual secara umum di Indonesia** dan fungsi intinya sama dengan solusi, bila **ada bukti dipasang atau dipakai di wilayah itu** (studi kasus, berita, pengadaan, klien), dihitung sebagai sudah ada. Produk yang dijual daring tetapi tidak ada bukti pemasangan di wilayah bukan otomatis gugur; catat sebagai kompetitor dan jelaskan pembedanya.
- **Fitur bawaan** CCTV atau meter pintar yang sudah dipasang pemerintah atau penyedia di wilayah itu bisa menggugurkan ide yang sekadar mengulang fungsinya. Cek apakah datanya bisa diakses; bila ya, integrasi bisa jadi pembeda.
- **Proposal, brosur, dan rencana vendor** tanpa pemasangan nyata belum dihitung sebagai sudah ada; catat di log pencarian.
- Harga dan spesifikasi produk yang ditemukan saat cek kebaruan harus bersumber dan bertanggal bila dipakai di BOM.

## Aturan "sudah ada"

Sebuah sistem dianggap **sudah ada di wilayah** bila ketiganya terpenuhi:
1. **Aktif**: masih dipelihara dan dipakai (ada pembaruan/ulasan/berita dalam sekitar 18 bulan terakhir).
2. **Melayani wilayah itu**: termasuk aplikasi nasional atau milik kota lain yang benar-benar dipakai warga/petugas di wilayah itu.
3. **Fungsi inti sama**: menyelesaikan masalah yang sama untuk pengguna yang sama. Kemiripan fitur sampingan tidak cukup.

Jika hanya sebagian fungsinya yang tumpang tindih, ide masih boleh lolos, tetapi **pembeda** harus ditulis jelas (fitur, segmen, kanal, model bisnis).

## Verdict

| Verdict | Arti | Perlakuan |
|---------|------|-----------|
| `BELUM_ADA` | Tidak ditemukan sistem serupa di wilayah | Lolos |
| `ADA_DI_WILAYAH_LAIN` | Ada di daerah/negara lain, belum di wilayah ini | Lolos. Wajib isi `referensi_serupa` (nama, lokasi, URL, catatan adaptasi) |
| `PERNAH_ADA_TIDAK_AKTIF` | Pernah dicoba di wilayah ini, kini mati | Lolos. Wajib isi `referensi_serupa` dengan penyebab kegagalan dan apa yang harus berbeda |
| `SUDAH_ADA_DI_WILAYAH` | Aktif dan melayani wilayah dengan fungsi inti sama | **Gugur.** Masuk `ide_gugur` dengan nama dan URL sistem yang ditemukan |

`SUDAH_ADA_DI_WILAYAH` tidak boleh muncul di `solusi`; validator menolaknya.

## Bila ide gugur

1. Catat di `ide_gugur`: `nama`, `masalah_id`, `alasan`, `ditemukan {nama, url}`.
2. Ganti dengan ide baru yang lebih spesifik, dan cek ulang dari awal. Maksimal 2 putaran per masalah.
3. Jika semua ide untuk satu masalah gugur: ubah `status` masalah menjadi `terlayani`, isi `solusi_existing` dengan sistem yang ditemukan, dan tulis celah (atau tegaskan bahwa tidak ada celah berarti).
4. Jangan melonggarkan aturan "sudah ada" supaya ide tetap lolos.

## Kalimat yang jujur untuk laporan

- Benar: "Tidak ditemukan aplikasi X yang aktif di Kota Y lewat pencarian di Play Store, situs Dinas Z, dan berita 2025-2026 (lihat log)."
- Salah: "Belum ada aplikasi X di Kota Y." (klaim absolut yang tidak bisa dibuktikan)
