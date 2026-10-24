# 1. Judul Proposal

**HematDaya: Pemantauan Listrik dan Saran Berbasis Bukti untuk Berbagai Kebutuhan**

## 2. Tema Fokus Inovasi

**Bidang strategis:** Kesehatan - Smart and Sustainable Health Ecosystem for Human Well-being. **Klaster:** 08, Sustainable and Green Healthcare. **Tim:** Petani Digital.

## 3. Executive Summary

Tagihan bulanan belum menjelaskan pemakaian tiap perangkat. Pedoman UMY menyebut konsumsi energi tinggi yang belum terpantau secara terukur di rumah sakit dan klinik [1]. HematDaya membantu membaca konsumsi, membandingkan periode setara, dan menentukan hal yang perlu diperiksa.

Pengguna dapat memulai dari berkas data berformat CSV; meter yang terverifikasi dapat ditambahkan kemudian. Aplikasi menampilkan energi, kontribusi perangkat atau sirkuit, estimasi biaya jika tarif tersedia, serta data yang mendasari saran. Jadwal dan energi per satuan keluaran bersifat opsional. Data hilang tidak dianggap nol; meter utama dan perangkat di bawahnya tidak dihitung ganda.

Produk melayani rumah tangga, usaha, dan industri. Untuk UMY, sasaran awalnya pengelola sarana dan teknisi fasilitas kesehatan. Aplikasi tidak mengendalikan perangkat atau memerlukan data pasien.

Dokumen kebutuhan produk (PRD) dan prototipe peramban dengan data simulasi telah tersedia (Gambar 1). Tim menilai tingkat kesiapan teknologi (TKT) awal berada pada level 3. Targetnya TKT 4 pada April 2027 melalui pengujian fungsi terpadu. Layanan pemasangan, penerapan aplikasi, dan dukungan berkala berpotensi menghasilkan pendapatan; harga dan manfaat ekonominya belum diuji.

## 4. Deskripsi Inovasi

**Masalah dan pengguna.** Pengelola sarana dan teknisi perlu mengetahui perangkat mana yang berubah pemakaiannya, kapan perubahan terjadi, dan apakah datanya cukup. Kebutuhan tiap lokasi belum dikonfirmasi. Tim akan memulainya dengan wawancara dan menyiapkan uji coba lapangan (pilot).

**Solusi dan pembeda.** Pemantauan perangkat serta hubungan meter utama dan meter perangkat tersedia pada Home Assistant [2]. HematDaya menawarkan alur berbahasa Indonesia dari CSV tanpa membeli meter. Yang diuji ialah kemudahan memahami perangkat yang diukur, kelengkapan data, dan alasan saran melalui Beranda, Perangkat, serta Saran. Perangkat yang harus menyala terus, seperti kulkas obat, dipantau tanpa anjuran mematikannya atau penilaian boros hanya karena bekerja malam hari.

<!-- page -->

## 4. Deskripsi Inovasi (lanjutan)

**Cara kerja.** Satu sistem dengan komponen bersama melayani beragam pengguna; fitur biaya, jadwal, dan energi per satuan keluaran diaktifkan sesuai kebutuhan. Rincian teknologi mengikuti PRD [3]. Perhitungan memakai aturan tetap dan nilai tengah periode terdahulu yang setara. Saat impor, sistem memeriksa satuan, waktu, duplikasi, dan data yang bertentangan. Perbandingan ditunda jika kelengkapan data atau riwayat pemakaian belum cukup; pemakaian di luar jadwal bukan bukti pemborosan. Pembelajaran mesin baru dipertimbangkan jika tersedia data dan bukti manfaat dibanding perhitungan awal.

**Kondisi dan target.** Penilaian TKT awal 3 didukung prototipe peramban dan 36 uji acuan perhitungan yang tercatat lulus. Proses server masih disimulasikan; layanan server nyata, koneksi meter, dan penggunaan di fasilitas belum divalidasi. Target TKT 4 memerlukan pengujian fungsi terpadu dalam lingkungan terkontrol serta evaluasi mentor atau asesor. Sasarannya seluruh acuan hitung PRD lulus dan sedikitnya 4 dari 5 pengelola dapat membaca konsumsi, menemukan kontributor terbesar, serta memahami bukti tanpa bantuan. Ini target pengujian, bukan hasil studi atau janji penghematan.

**Peta jalan 12 bulan.** Kegiatan tatap muka menunggu konfirmasi panitia karena jadwal uji terbatas dalam pedoman belum seragam [1].

| Waktu | Kegiatan dan keluaran yang dituju |
|---|---|
| Okt-Nov 2026 | Wawancarai 5 pengelola atau teknisi; pilih beban dan tugas bersama pendamping; bangun alur CSV dan uji hitung dengan data sintetis. |
| Des 2026-Jan 2027 | Satukan penyimpanan, hak akses, impor yang aman diulang, dan pemulihan; catat hasil uji serta revisi kebutuhan. |
| Feb-Apr 2027 | Uji kemudahan penggunaan dan fungsi terpadu; perbaiki hambatan menuju TKT 4; pisahkan hasil rumah tangga dan industri. |
| Mei-Okt 2027 | Jika izin dan mitra tersedia, uji satu fasilitas dengan data listrik nyata; evaluasi koneksi meter, dukungan operasional, dan kesediaan membayar. |

**Keselamatan dan data.** Uji awal memakai data sintetis dalam lingkungan terkontrol. Aplikasi tidak memutus listrik, mengatur alat medis, menilai mutu vaksin, atau memberi keputusan klinis. Data nyata memerlukan izin fasilitas, batas akses, dan kesepakatan penyimpanan. Pelibatan pasien atau data klinis memerlukan penilaian etik dan izin resmi sebelum kegiatan. Sebelum pilot, tim wajib mengenkripsi komunikasi, memeriksa kepemilikan data di server, serta menguji pencadangan dan pemulihan.

**Tim dan mitra.** Dua profesional, satu mahasiswa, dan satu dosen UGM akan meninjau kebutuhan layanan bersama pendamping serta petugas fasilitas. Tim belum memiliki tenaga kesehatan, surat dukungan, akses fasilitas, atau komitmen pilot. Mitra dijajaki melalui jejaring program; layanan penerapan dan dukungan diuji setelah validasi.

<!-- page -->

## 5. Pembagian Tugas dan Tanggung Jawab Tim Pelaksana

| Anggota dan peran | Tanggung jawab dan keluaran |
|---|---|
| **Ahmad Widardi** - Ketua; profesional; Koordinator Bisnis dan Hilirisasi | Memimpin pengembangan bersama Sidiq; menangani arsitektur, komunikasi program, kebutuhan pengguna, bisnis, pilot, kepemilikan karya, dan catatan keputusan. |
| **Sidiq Tri Pratikto** - Profesional; Koordinator Teknis | Mengembangkan tampilan, layanan data, impor, dan perhitungan bersama Ahmad; menangani penyimpanan, keamanan, pengujian, serta catatan versi dan penerapan. |
| **Akmal Rafli Fauzan** - Mahasiswa UGM; Koordinator Klinis dan Validasi Pengguna | Menghubungkan tim dengan pengelola dan pendamping; mencatat kebutuhan serta batas operasi, menguji kegunaan, dan mendokumentasikan izin. Penilaian klinis tetap pada petugas berwenang. |
| **Erwin Eko Wahyudi, S.Kom., M.Cs.** - Dosen UGM; Mentor Analitik Data | Meninjau metode perbandingan, mutu data, evaluasi, dan bukti capaian; membimbing mahasiswa. |

Setiap tugas mingguan mencantumkan penanggung jawab, kriteria penerimaan, dan bukti. Ahmad memantau kemajuan serta hambatan; Erwin meninjau metode dan hasil setiap putaran pengembangan; anggota lain menelaah kode. Tim mencatat kegagalan, perubahan lingkup, dan dampak jadwal. Perhitungan, akurasi meter, dan kemudahan penggunaan diuji terpisah; hasil dilaporkan per konteks.

## 6. Daftar Pustaka

[1] Direktorat Inovasi dan Hilirisasi UMY. *Buku Pedoman Peserta UMY Hackathon DeepTech 2026*, revisi. Bagian 3, 6, 7.8, dan Lampiran. [Dokumen resmi](https://drive.google.com/file/d/1Zzk80Mf3XR-poQPG4i49x48cByk3GVod/view). Diakses 24 Oktober 2026.

[2] Home Assistant. *Integrating individual device energy usage*, bagian Upstream devices and hierarchies. [Dokumentasi](https://www.home-assistant.io/docs/energy/individual-devices/). Diakses 24 Oktober 2026.

[3] Tim Petani Digital. *PRD HematDaya Generik*, versi 1.2, 21 Oktober 2026. Bagian 5, 11, 15, dan 20. Dokumen teknis pendamping; salinan Indonesia dan Inggris disertakan dalam folder PRD.

## 7. Lampiran

Sampul dan identitas ada di berkas administrasi terpisah. CV, portofolio, dan pakta integritas diunggah melalui sistem panitia; bukti kemitraan menyusul bila diperoleh.

![Beranda: energi, biaya, dan kualitas data](assets/prototipe/01-beranda.png) ![Kontributor terbesar dan pengamatan](assets/prototipe/02-kontributor-pengamatan.png) ![Dasar saran dengan bukti](assets/prototipe/03-dasar-saran.png) ![Pratinjau impor CSV](assets/prototipe/04-impor-pratinjau.png)

**Gambar 1.** Prototipe, data simulasi: (a) Beranda; (b) kontributor; (c) dasar saran; (d) impor CSV.
