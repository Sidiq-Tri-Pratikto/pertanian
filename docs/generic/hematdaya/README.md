# HematDaya — spesifikasi produk

PRD **v1.2, 21 Oktober 2026 (Asia/Jakarta)** menetapkan produk pemantauan listrik dan saran berbasis bukti untuk rumah tangga, usaha, dan industri. Bahasa antarmuka produk adalah Indonesia; PRD lengkap tersedia dalam dua bahasa. Alur design system terlebih dahulu ditambahkan pada **24 Oktober 2026**; handoff aplikasi menjadi v1.2.1 dan tetap memuat snapshot PRD v1.2 yang sama.

| Dokumen | Kegunaan |
|---|---|
| [PRD Bahasa Indonesia](01_PRD_HematDaya_Generic_ID.md) | Persyaratan lengkap, perhitungan, arsitektur, fixture dan penerimaan |
| [English PRD](01_PRD_HematDaya_Generic_EN.md) | Kontrak yang sama untuk pembaca dan pelaksana berbahasa Inggris |
| [Claude Design System handoff — English](04_Claude_Design_System_HematDaya_EN.md) | Tahap 1: fondasi, token, komponen/state, pola domain, workbench, validasi dan serah-terima sistem yang mandiri |
| [Claude Design System prompt — English](05_Prompt_Claude_Design_System_EN.md) | Prompt siap salin untuk membuat sistem dengan file 04 |
| [Claude Design application handoff — English](02_Claude_Design_HematDaya_EN.md) | Tahap 2: prototipe interaktif yang memakai design system; konteks produk dan salinan PRD lengkap disertakan |
| [Claude Design application prompt — English](03_Prompt_Claude_Design_EN.md) | Prompt aplikasi setelah sistem dibuat; mencatat binding/versi yang benar-benar digunakan |
| [Riset UX HematDaya](../../../reports/UX%20HematDaya%20untuk%20desain%20intuitif.md) | Sintesis sumber primer, alasan keputusan UX dan batas bukti |

## Urutan penggunaan di Claude Design

1. **Buat design system:** lampirkan hanya file **04**, lalu gunakan prompt dari **05**. Hasil yang diminta adalah HematDaya Design System, token/manifest, komponen beserta state, empat contoh pola, serta workbench yang dapat diperiksa. Sistem ini belum dibuat di Claude hanya karena dokumennya tersedia di repository.
2. **Simpan identitas hasilnya:** catat nama/versi, artifact atau sumber yang benar-benar tersedia, status pemeriksaan, token dan komponen. Pertahankan artefak privat; jangan menganggapnya otomatis menjadi default organisasi.
3. **Buat prototipe aplikasi:** lampirkan file **02**, pilih/lampirkan/impor sistem hasil tahap pertama sesuai kemampuan sesi, lalu gunakan prompt **03**. Minta prototipe menggunakan token/komponen yang sama dan melaporkan binding serta penyimpangannya. Bila sistem tidak tersedia, handoff menjelaskan fallback draft lokal sebelum layar aplikasi; hasilnya tidak boleh diklaim memakai sistem yang belum diimpor.

Penomoran file lama dipertahankan agar tautan sebelumnya tetap bekerja; urutan kerja adalah **04 + 05 → hasil design system → 02 + 03**. Konteks produk tetap mandiri di file 02; file 04 juga memuat semua konteks yang diperlukan untuk tahap sistem tanpa membutuhkan repository atau chat sebelumnya.

Design-system handoff memuat 12 gerbang penerimaan, struktur token primitif/semantik/komponen, kontrak komponen `HD.*`, pola grafik dan state data, aturan tema/reuse, serta pencatatan versi. Rasio kontras pasangan warna awal sudah dihitung sebagai pemeriksaan dokumen; itu belum membuktikan kontras antarmuka yang dirender, akses keyboard, hasil native, atau usability pengguna.

HematDaya menjawab energi yang benar-benar tercatat, estimasi biaya ketika tarif tersedia, kontributor dalam cakupan terpilih, perubahan pada periode yang sebanding, serta bukti dan keterbatasan saran. Model bersama adalah **lokasi → objek pantauan → sumber pengukuran**; objek dapat berupa perangkat, mesin, kelompok beban, sirkuit atau seluruh lokasi sesuai sumbernya. Sistem tidak menebak konsumsi per alat dari meter utama dan tidak mengasumsikan semua beban cocok dengan satu meter.

Tiga tab tetap adalah **Beranda, Perangkat, Saran**. Demo dan CSV merupakan jalur awal lengkap tanpa AC, hardware, tarif, jadwal atau data produksi wajib. Jadwal dan energi per unit keluaran hanya digunakan setelah diaktifkan dengan data yang sesuai. Beban kontinu tidak otomatis dianggap boros. Produk hanya memantau dan menyarankan; tidak mengendalikan peralatan.

Arah arsitektur telah diterima: **modular monolith dengan core bersama, modul kemampuan opsional, adapter dan komposisi tervalidasi**. API serta worker opsional memanggil use case yang sama. Rilis sumber bersama menghasilkan build yang dapat direproduksi; deployment klien terisolasi dapat dipilih tanpa fork kode. Site adalah lokasi domain, bukan otomatis tenant. Reuse tidak mensyaratkan SaaS, microservices, provisioning tenant atau platform plugin dinamis.

Kedua PRD memuat **24 bagian bernomor (0–23), 22 kebutuhan fungsional, 20 pemeriksaan UX dan 58 uji penerimaan**. Fixture rumah tangga dan industri masing-masing menetapkan **2.688 baris**, beserta oracle energi, biaya, keluaran opsional dan varian perubahan. Ketelitian semantik, cakupan aman, data hilang sebagai gap dan bukti yang dapat ditelusuri tetap berlaku untuk setiap komposisi produk.

Status dokumen adalah spesifikasi pengembangan dengan arah produk/arsitektur yang disetujui. Seluruh pengujian implementasi dimulai **belum dijalankan**; belum ada klaim aplikasi berjalan, integrasi terverifikasi, studi pengguna, kepatuhan aksesibilitas, akurasi hardware atau penghematan nyata. Pemeriksaan dokumen dan aritmetika fixture tidak menggantikan bukti runtime, lapangan dan usability masing-masing segmen.
