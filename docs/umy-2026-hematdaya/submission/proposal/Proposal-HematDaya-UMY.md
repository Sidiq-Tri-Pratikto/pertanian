# 1. Judul Proposal

**HematDaya: Pemantauan Listrik dan Saran Berbasis Bukti untuk Berbagai Kebutuhan**

## 2. Tema Fokus Inovasi

**Bidang strategis:** Kesehatan - Smart and Sustainable Health Ecosystem for Human Well-being. **Klaster:** 08, Sustainable and Green Healthcare. **Tim:** Petani Digital.

## 3. Executive Summary

Tagihan bulanan menunjukkan berapa listrik yang dibayar, tetapi belum menjelaskan pemakaian tiap perangkat. Di rumah sakit dan klinik, kebutuhan ini juga disebut dalam problem statement UMY: konsumsi energi tinggi dan belum terpantau secara terukur [1].

HematDaya membantu pengguna membaca konsumsi listrik, membandingkan periode yang setara, dan menentukan hal yang perlu diperiksa. Data berasal dari impor CSV atau meter yang kelak diverifikasi. Aplikasi menampilkan energi, kontribusi perangkat atau sirkuit, estimasi biaya bila tarif tersedia, serta saran dengan bukti dan keterbatasannya. Jadwal dan ukuran energi per satuan keluaran bersifat opsional. Data hilang tidak dianggap nol; meter utama dan perangkat di bawahnya tidak dijumlahkan dua kali.

Produk dasarnya dapat dipakai rumah tangga, usaha, dan industri. Untuk UMY, calon pengguna awalnya ialah pengelola sarana dan teknisi fasilitas kesehatan. Beban yang harus terus beroperasi tetap dipantau tanpa saran penghentian. HematDaya tidak mengendalikan perangkat dan tidak memerlukan data pasien.

PRD generik telah tersedia; desain demo sedang dikerjakan. Estimasi TKT awal 2 dan target TKT 4 pada April 2027 akan dikonfirmasi bersama mentor berdasarkan bukti pengujian. Pekerjaan meliputi alur CSV, analitik yang dapat ditelusuri, uji kegunaan, dan validasi terintegrasi. Potensi pendapatannya berupa layanan pemasangan, penerapan aplikasi, dan dukungan berkala; harga serta manfaat ekonominya masih perlu diuji.

## 4. Deskripsi Inovasi

**Masalah, pengguna, dan kebutuhan.** Usulan mengikuti masalah energi pada Klaster 08 [1], dengan fokus awal pengelola sarana dan teknisi rumah sakit atau klinik. Tagihan membantu melihat total biaya, sedangkan pemeriksaan operasional memerlukan informasi yang lebih rinci: beban mana yang berubah, kapan perubahan terjadi, dan apakah datanya cukup. Kebutuhan pada lokasi tertentu belum divalidasi melalui wawancara atau pilot; validasi itu menjadi pekerjaan awal program.

**Solusi dan pembeda yang akan diuji.** Pemantauan per perangkat dan hierarki meter telah tersedia, misalnya pada Home Assistant [2]. HematDaya mengembangkan pengalaman berbahasa Indonesia yang dapat dimulai dari CSV, tanpa membeli meter terlebih dahulu. Pembeda yang diuji ialah kemudahan memahami cakupan pengukuran, kualitas data, dan alasan suatu saran. Pengguna dapat membuka bukti dari tiga tab: Beranda, Perangkat, dan Saran. Jadwal layanan tidak menjadi asumsi untuk semua beban; kulkas obat yang harus menyala terus tidak ditandai boros hanya karena bekerja malam hari.

<!-- page -->

## 4. Deskripsi Inovasi (lanjutan)

**Teknologi dan penggunaan kembali.** PRD menetapkan monolit modular: backend FastAPI/Python, PostgreSQL, dan target klien React Native/Expo untuk seluler serta web [3]. Inti bersama menangani satuan, interval, cakupan, kualitas data, dan bukti. Biaya, jadwal, serta intensitas menjadi modul opsional; koneksi meter menjadi adapter. Penyesuaian klien memakai konfigurasi atau perluasan modul dari rilis sumber bersama, termasuk untuk kebutuhan UMY.

Analisis awal memakai perhitungan deterministik dan median periode terdahulu yang setara. Impor memeriksa satuan, waktu, duplikasi, serta konflik sumber sebelum disimpan. Perbandingan otomatis ditahan bila cakupan atau riwayat tidak cukup. Pemakaian di luar jadwal dilaporkan sebagai pengamatan, bukan bukti pemborosan. Pembelajaran mesin baru dipertimbangkan bila tersedia data dan evaluasi yang menunjukkan manfaat dibanding baseline sederhana; bukan prasyarat prototipe.

**Kondisi awal dan target.** Estimasi TKT 2 didasarkan pada PRD dan rancangan; desain demo masih berlangsung. Validasi backend, integrasi meter, dan uji fasilitas untuk versi generik belum dibuktikan. Target TKT 4 memerlukan validasi modul terintegrasi dalam lingkungan terkontrol dan evaluasi mentor/asesor. Target rekayasa: seluruh acuan hitung PRD lulus, tanpa penghitungan ganda atau data hilang yang berubah menjadi nol. Target kegunaan: sedikitnya 4 dari 5 pengelola dapat membaca konsumsi, menemukan kontributor terbesar, dan memahami bukti tanpa bantuan. Angka tersebut merupakan target usulan, bukan hasil uji atau janji penghematan.

**Peta jalan 12 bulan.** Tanggal kegiatan onsite mengikuti konfirmasi panitia karena jadwal uji terbatas di dalam pedoman belum seragam [1].

| Waktu | Kegiatan dan keluaran yang dituju |
|---|---|
| Okt-Nov 2026 | Wawancara kebutuhan dengan 5 pengelola/teknisi; pilih beban dan tugas uji bersama pendamping. Bangun alur CSV dan bukti perhitungan dengan data sintetis. |
| Des 2026-Jan 2027 | Integrasikan penyimpanan, hak akses, impor yang aman saat diulang, dan pemulihan kegagalan. Catat hasil uji serta revisi kebutuhan. |
| Feb-Apr 2027 | Uji kegunaan dan fungsi terintegrasi; ulangi perbaikan yang menghambat tugas. Siapkan laporan menuju TKT 4. Uji rumah tangga dan industri dilaporkan terpisah sesuai PRD. |
| Mei-Okt 2027 | Jika izin dan mitra tersedia, pilot satu fasilitas dengan data listrik nyata; evaluasi adapter meter, dukungan operasional, dan kesediaan membayar. |

**Keselamatan, etik, dan data.** Uji awal memakai data sintetis dan lingkungan terkontrol. Aplikasi hanya memantau; tidak memutus listrik, mengatur alat medis, menilai mutu vaksin, atau memberi keputusan klinis. Data listrik nyata memerlukan izin fasilitas, batas akses, dan kesepakatan penyimpanan. Tidak ada kebutuhan data pasien. Pelibatan pasien atau data klinis memerlukan penilaian etik dan izin resmi sebelum kegiatan. Komunikasi terenkripsi, pemeriksaan kepemilikan di server, serta uji pencadangan/pemulihan menjadi syarat sebelum pilot.

**Tim, mitra, dan hilirisasi.** Tim terdiri atas dua profesional serta satu mahasiswa dan satu dosen UGM. Konteks layanan ditinjau bersama pendamping dan petugas fasilitas; tim belum memiliki tenaga kesehatan. Belum ada surat dukungan, akses fasilitas, atau komitmen pilot. Jejaring program menjadi jalur penjajakan. Layanan penerapan dan dukungan berkala akan diuji setelah validasi.

<!-- page -->

## 5. Pembagian Tugas dan Tanggung Jawab Tim Pelaksana

| Anggota dan peran | Tanggung jawab dan keluaran |
|---|---|
| **Ahmad Widardi** - Ketua; profesional; Koordinator Bisnis dan Hilirisasi | Memimpin pengembangan full stack bersama Sidiq, arsitektur, komunikasi program, validasi kebutuhan dan model bisnis; menyiapkan rencana pilot, kepemilikan karya, dan dokumentasi keputusan. |
| **Sidiq Tri Pratikto** - Profesional; Koordinator Teknis | Mengembangkan antarmuka, API, impor dan analitik bersama Ahmad; menyiapkan penyimpanan, keamanan, pengujian perhitungan, serta catatan versi dan penerapan. |
| **Akmal Rafli Fauzan** - Mahasiswa UGM; Koordinator Klinis dan Validasi Pengguna | Mengatur interaksi dengan problem owner dan pendamping, mencatat kebutuhan serta batas operasi beban, menjalankan uji kegunaan dan dokumentasi izin. Penilaian klinis tetap pada petugas yang berwenang. |
| **Erwin Eko Wahyudi, S.Kom., M.Cs.** - Dosen UGM; Mentor Analitik Data | Meninjau baseline, mutu data, rancangan evaluasi, dan bukti capaian; membimbing mahasiswa serta memberi masukan terhadap pilihan metode. |

Pemantauan dilakukan melalui daftar tugas mingguan dengan penanggung jawab, kriteria penerimaan, dan bukti hasil. Ahmad meninjau kemajuan serta hambatan; Erwin meninjau metode dan hasil pada akhir setiap iterasi. Perubahan kode ditelaah anggota lain. Kegagalan uji dan perubahan lingkup dicatat, termasuk dampaknya pada jadwal. Pengujian memisahkan kebenaran perhitungan, akurasi meter, dan kegunaan; ketiganya tidak saling menggantikan. Hasil rumah tangga, industri, dan fasilitas kesehatan dilaporkan menurut konteks masing-masing.

## 6. Daftar Pustaka

[1] Direktorat Inovasi dan Hilirisasi UMY. *Buku Pedoman Peserta UMY Hackathon DeepTech 2026*, revisi. Bagian 3, 6, 7.8, dan Lampiran. [Dokumen resmi](https://drive.google.com/file/d/1Zzk80Mf3XR-poQPG4i49x48cByk3GVod/view). Diakses 24 Oktober 2026.

[2] Home Assistant. *Integrating individual device energy usage*, bagian Upstream devices and hierarchies. [Dokumentasi](https://www.home-assistant.io/docs/energy/individual-devices/). Diakses 24 Oktober 2026.

[3] Tim Petani Digital. *PRD HematDaya Generik*, versi 1.2, 21 Oktober 2026. Bagian 5, 11, 15, dan 20. Dokumen teknis pendamping; salinan Indonesia dan Inggris disertakan dalam folder PRD.

## 7. Lampiran

Sampul dan lembar identitas disiapkan dalam berkas administrasi terpisah. CV, portofolio, serta pakta integritas bertanda tangan akan diunggah melalui sistem panitia. Bukti kemitraan dilampirkan bila telah diperoleh. Tautan dan bukti demo menyusul setelah desain selesai.
