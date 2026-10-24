# 1. Judul Proposal

**HematDaya: Pemantauan Listrik dan Saran Berbasis Bukti untuk Berbagai Kebutuhan**

## 2. Tema Fokus Inovasi

**Bidang strategis:** Kesehatan - Smart and Sustainable Health Ecosystem for Human Well-being. **Klaster:** 08, Sustainable and Green Healthcare. **Tim:** Petani Digital.

## 3. Executive Summary

Tagihan listrik belum menjelaskan perangkat mana yang perlu diperiksa. Pedoman UMY juga mengangkat persoalan konsumsi energi rumah sakit dan klinik yang belum terpantau secara terukur [1]. HematDaya membantu pengelola membaca pemakaian listrik dan menelusuri perubahannya.

Pengguna dapat memulai dari berkas tabel berformat CSV, tanpa membeli meter baru. Koneksi meter dapat ditambahkan setelah diverifikasi. Aplikasi memperlihatkan pemakaian perangkat, perbandingan antarperiode, serta alasan di balik setiap saran. Biaya ditampilkan jika tarif tersedia. Data yang hilang tetap ditandai, dan pembacaan meter utama tidak dijumlahkan lagi dengan perangkat di bawahnya.

HematDaya dirancang untuk rumah tangga, usaha, dan industri. Untuk UMY, kami berfokus pada pengelola sarana dan teknisi fasilitas kesehatan. Aplikasi tidak mengendalikan perangkat maupun membutuhkan data pasien.

Dokumen kebutuhan produk (PRD) dan prototipe dengan data simulasi sudah tersedia. Tim menilai tingkat kesiapan teknologi (TKT) awal berada di level 3. Kami menargetkan TKT 4 pada April 2027. Peluang pendapatan dari pemasangan, penerapan aplikasi, dan dukungan berkala akan diuji; harga serta manfaat ekonominya belum terbukti.

## 4. Deskripsi Inovasi

**Masalah yang ingin kami jawab.** Saat pemakaian listrik meningkat, pengelola perlu tahu perangkat mana yang berubah, kapan, dan apakah datanya cukup. Kami akan menggali kebutuhan tiap lokasi melalui wawancara sebelum menyiapkan uji coba lapangan (pilot).

**Apa yang ditawarkan HematDaya.** Pemantauan perangkat dan hubungan antarmeter sudah tersedia, misalnya pada Home Assistant [2]. HematDaya menekankan kemudahan memulai dari CSV dan penjelasan berbahasa Indonesia. Halaman Beranda, Perangkat, dan Saran menjelaskan apa yang diukur, kelengkapan data, dan alasan saran. Kulkas obat yang harus menyala terus, misalnya, tidak akan disarankan untuk dimatikan atau dianggap boros hanya karena bekerja malam hari.

<!-- page -->

## 4. Deskripsi Inovasi (lanjutan)

**Cara aplikasi membaca data.** Komponen aplikasi dipakai bersama untuk beragam pengguna. Fitur biaya, jadwal, dan energi per satuan keluaran diaktifkan sesuai kebutuhan, mengikuti PRD [3]. Perhitungan mengikuti aturan tetap, dengan nilai tengah periode sebanding sebagai acuan. Saat CSV diunggah, aplikasi memeriksa satuan, waktu, data berulang, dan nilai yang bertentangan. Perbandingan ditunda jika data atau riwayatnya belum cukup. Pemakaian di luar jadwal juga belum tentu boros. Pembelajaran mesin baru dipertimbangkan bila data dan manfaatnya mendukung.

**Yang sudah tersedia dan yang akan diuji.** Prototipe dapat dibuka di peramban; 36 uji acuan perhitungannya tercatat lulus. Ini mendasari penilaian TKT 3 tim. Proses server masih disimulasikan, sedangkan server nyata, koneksi meter, dan penggunaan di fasilitas belum divalidasi. Menuju TKT 4, fungsi terpadu akan diuji dalam lingkungan terkontrol dan dievaluasi mentor atau asesor. Targetnya: seluruh acuan hitung PRD lulus, dan sedikitnya 4 dari 5 pengelola mampu membaca konsumsi, menemukan penyumbang terbesar, serta memahami data pendukung tanpa bantuan. Ini target pengujian, bukan janji penghematan.

**Rencana 12 bulan.** Jadwal tatap muka akan dikonfirmasi kepada panitia karena waktu uji terbatas dalam pedoman belum seragam [1].

| Waktu | Kegiatan dan hasil yang dituju |
|---|---|
| Okt-Nov 2026 | Wawancara dengan 5 pengelola atau teknisi; pilih perangkat dan tugas bersama pendamping; bangun alur CSV dan uji hitung memakai data sintetis. |
| Des 2026-Jan 2027 | Hubungkan penyimpanan dan hak akses; pastikan data impor berulang dihitung sekali; uji pemulihan, catat hasil, dan perbarui kebutuhan. |
| Feb-Apr 2027 | Uji kemudahan penggunaan dan fungsi terpadu menuju TKT 4. Laporkan hasil rumah tangga dan industri secara terpisah. |
| Mei-Okt 2027 | Jika izin dan mitra tersedia, uji satu fasilitas dengan data listrik nyata. Evaluasi koneksi meter, dukungan operasional, dan kesediaan membayar. |

**Menjaga keselamatan dan data.** Pengujian awal memakai data sintetis dalam lingkungan terkontrol. Aplikasi tidak memutus listrik, mengatur alat medis, menilai mutu vaksin, atau memberi keputusan klinis. Data nyata memerlukan izin fasilitas, pembatasan akses, dan kesepakatan penyimpanan. Pelibatan pasien atau data klinis memerlukan penilaian etik dan izin resmi terlebih dahulu. Sebelum pilot, tim akan mengenkripsi komunikasi, memeriksa kepemilikan data di server, serta menguji pencadangan dan pemulihan.

**Kesiapan tim dan mitra.** Tim terdiri atas dua profesional, satu mahasiswa, dan satu dosen UGM. Kebutuhan akan ditinjau bersama pendamping dan petugas fasilitas. Tim belum memiliki tenaga kesehatan, surat dukungan, akses fasilitas, atau komitmen pilot. Kami menjajaki mitra melalui jejaring program. Layanan penerapan dan dukungan baru diuji setelah validasi.

<!-- page -->

## 5. Pembagian Tugas dan Tanggung Jawab Tim Pelaksana

| Anggota dan peran | Tanggung jawab |
|---|---|
| **Ahmad Widardi** - Ketua; profesional; Koordinator Bisnis dan Hilirisasi | Memimpin pengembangan dan arsitektur bersama Sidiq. Mengurus komunikasi program, kebutuhan pengguna, bisnis, pilot, kepemilikan karya, dan catatan keputusan. |
| **Sidiq Tri Pratikto** - Profesional; Koordinator Teknis | Membangun tampilan, layanan data, impor, dan perhitungan bersama Ahmad. Menangani penyimpanan, keamanan, pengujian, serta catatan versi dan penerapan. |
| **Akmal Rafli Fauzan** - Mahasiswa UGM; Koordinator Klinis dan Validasi Pengguna | Menghubungkan tim dengan pengelola dan pendamping; mencatat kebutuhan, batas operasi, dan izin; menguji kegunaan. Penilaian klinis tetap pada petugas berwenang. |
| **Erwin Eko Wahyudi, S.Kom., M.Cs.** - Dosen UGM; Mentor Analitik Data | Membimbing mahasiswa; meninjau metode perbandingan, mutu data, evaluasi, dan bukti capaian. |

Tiap tugas mingguan memiliki penanggung jawab, ukuran keberhasilan, dan bukti. Ahmad memantau hambatan dan kemajuan; Erwin meninjau metode serta hasil tiap putaran pengembangan; anggota lain menelaah kode. Kegagalan, perubahan lingkup, dan dampak jadwal dicatat. Perhitungan, akurasi meter, dan kegunaan diuji terpisah, lalu dilaporkan per konteks.

## 6. Daftar Pustaka

[1] Direktorat Inovasi dan Hilirisasi UMY. *Buku Pedoman Peserta UMY Hackathon DeepTech 2026*, revisi. Bagian 3, 6, 7.8, dan Lampiran. [Dokumen resmi](https://drive.google.com/file/d/1Zzk80Mf3XR-poQPG4i49x48cByk3GVod/view). Diakses 24 Oktober 2026.

[2] Home Assistant. *Integrating individual device energy usage*, bagian Upstream devices and hierarchies. [Dokumentasi](https://www.home-assistant.io/docs/energy/individual-devices/). Diakses 24 Oktober 2026.

[3] Tim Petani Digital. *PRD HematDaya Generik*, versi 1.2, 21 Oktober 2026. Bagian 5, 11, 15, dan 20. Dokumen teknis pendamping; salinan Indonesia dan Inggris disertakan dalam folder PRD.

## 7. Lampiran

Sampul dan identitas ada di berkas administrasi terpisah. CV, portofolio, dan pakta integritas diunggah melalui sistem panitia. Bukti kemitraan menyusul jika diperoleh.

![Beranda: energi, biaya, dan kualitas data](assets/prototipe/01-beranda.png) ![Kontributor terbesar dan pengamatan](assets/prototipe/02-kontributor-pengamatan.png) ![Dasar saran dengan bukti](assets/prototipe/03-dasar-saran.png) ![Pratinjau impor CSV](assets/prototipe/04-impor-pratinjau.png)

**Gambar 1.** Prototipe, data simulasi: (a) Beranda; (b) kontributor; (c) dasar saran; (d) impor CSV.
