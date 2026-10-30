# Preseden aplikasi yang sudah dipakai untuk Kartika

**Acuan riset: 31 Oktober 2026, WIB.** Pilihan pertama adalah **NarrativeLens untuk analisis komunikasi bantuan bencana**, dengan REKRUT AMAN sebagai alternatif ketika hanya dokumen publik yang tersedia. SUARA SIAGA dengan pemeriksaan serah-terima ala CoverageMap layak dipilih setelah ada mitra dan data tindak lanjut. Penggunaan di luar negeri membuktikan adopsi; manfaat dan akurasi rancangan kita tetap harus dibuktikan.

Laporan ini menajamkan [ide sentimen awal](<Ide sentimen Kartika Cyber Hackathon.md>), [produk sentimen reusable](<Reusable sentiment for national resilience.md>), dan [opsi SNA](<Reusable social network analysis for resilience.md>). Catatan sumber dan batas buktinya tersedia dalam [berkas riset pendukung](<../research_notes/Operational app precedents for Kartika/sources.md>).

## Enam preseden dengan pengguna yang jelas

| Preseden dan pengguna | Penggunaan yang terdokumentasi | Apa yang boleh disimpulkan |
|---|---|---|
| **Sprinklr + Maven; XVIII Airborne Corps, U.S. Army** | Saat Hurricane Helene **2024**, public affairs memakai Maven untuk menampilkan sentimen dari Sprinklr; artikel Army **22 Desember 2025** menyebut insight tersedia dalam hitungan menit. [Sumber](https://www.army.mil/article/289747/setaf_af_public_affairs_experiment_with_emerging_technology_to_shape_the_information_environment). | Pemakaian nyata dalam bencana. Pengembangan SETAF-AF pada artikel yang sama masih mencakup eksperimen; tidak tersedia benchmark akurasi. |
| **Staff Sgt. Star; U.S. Army AIE** | Artikel **16 Juli 2026** menyebut recruiter menggunakan chatbot berbasis referensi rekrutmen terkurasi, melayani sekitar **12.000 pengguna berizin**. [Sumber](https://www.army.mil/article/293913/ai_powered_chatbot_helps_streamline_army_recruiting). | Adopsi layanan informasi; angka tersebut bukan pengguna aktif bulanan. Proyeksi 28.000 pengguna tidak dihitung sebagai capaian. |
| **QuakeMap/crowdsourcing KLL; Nepalese Army** | Arsip Ushahidi tentang gempa Nepal **2015** menjelaskan verifikasi awal oleh Kathmandu Living Labs dan pemakaian data untuk perencanaan bantuan; hampir **2.200 permintaan/laporan**, termasuk 650 permintaan dukungan udara. [Sumber](https://www.ushahidi.com/in-action/nepalese-army-and-disaster-management/). | Preseden historis penggunaan. Jumlah permintaan bukan jumlah penyelamatan atau bantuan berhasil; tanggal publikasi halaman tidak tercantum. |
| **WebEOC; Bay County EOC dan Florida National Guard** | Artikel **23 Oktober 2018** tentang Hurricane Michael menjelaskan permintaan sumber daya melalui WebEOC, penugasan ke organisasi, lalu pembagian tugas oleh unit. [Sumber](https://www.nationalguard.mil/News/Overseas-Operations/Article/1668966/florida-infantry-soldiers-provide-security-after-hurricane/). | Alur penugasan antarlembaga dipakai dalam respons nyata tahun 2018; tidak membuktikan efektivitas versi sekarang. |
| **ICE; Joint Base San Antonio/DoD** | Publikasi **30 Januari 2025** menyebut pengelola ICE di JBSA, kartu komentar daring, laporan kepuasan dan tanggung jawab organisasi penyedia layanan. [Sumber](https://www.jbsa.mil/News/News/Article/4048110/jbsa-welcomes-new-ice-director/). | Sistem feedback dengan pengelola nyata, terdokumentasi aktif pada 2025. Tidak membuktikan adanya klasifikasi sentimen AI atau deteksi keluhan berulang. |
| **NATO Lessons Learned Portal; NATO/JALLC** | Halaman institusi menjelaskan pengumpulan observasi, pengelolaan dan berbagi lessons, serta perannya dalam proses perbaikan. Halaman tanpa tanggal publikasi ini diakses **31 Oktober 2026**. [ACT](https://www.act.nato.int/activities/nato-lessons-learned-portal/), [JALLC](https://www.jallc.nato.int/activities/lessons-learned). | Preseden kelembagaan untuk siklus observasi–analisis–tindakan–validasi. Keberadaan portal tidak membuktikan model AI tertentu atau dampak kuantitatif. |

Istilah **sudah dipakai** mengacu pada bukti pengguna dan proses. Artikel institusi dan studi kasus penyedia belum merupakan audit independen atas efektivitas.

## Produk Indonesia sudah mencakup pemetaan kebutuhan

FAQ PetaBencana yang diakses pada tanggal acuan menyebut **Peta Gotong Royong** untuk menyampaikan kebutuhan darurat dan menghubungkan pemohon dengan pemberi bantuan. Bagian 24 juga menyebut Open API. Dengan demikian, menambahkan kategori makanan, air atau obat ke peta tidak cukup untuk mendukung klaim kebaruan SUARA SIAGA. Cakupan endpoint, arsip, izin dan kualitas teks tetap perlu diperiksa langsung sebelum memilihnya sebagai sumber demo. [FAQ, bagian 24 dan 29](https://info.petabencana.id/faq).

**InAWARE** juga merupakan konteks lokal yang harus diperhitungkan: PDC mendokumentasikan penggunaan BNPB/provinsi saat kejadian Oktober 2021, sedangkan halaman BNPB menjelaskan sistem pendukung keputusan dengan akses melalui pendaftaran dan persetujuan. Data internalnya tidak dapat diasumsikan tersedia. [Studi kasus PDC](https://www.pdc.org/inaware-program-case-study/), [BNPB](https://inaware.bnpb.go.id/inaware/public/inaware_about/index.html). Pembeda yang perlu diuji ialah bukti komunikasi, verifikasi hasil dan serah-terima tugas; belum terbukti bahwa fitur setara tidak dimiliki produk yang ada.

## Tiga pilihan dan syarat melanjutkan

### 1. NarrativeLens: meja analisis komunikasi bantuan

**Pengguna:** petugas penerangan atau komunikasi posko bantuan TNI AD. **Keputusan:** pertanyaan atau kekhawatiran mana yang perlu diperiksa dan dijawab. Preseden Sprinklr–Maven mendukung pekerjaan analisis komunikasi saat bencana, bukan membuktikan metode NarrativeLens.

MVP: satu kejadian, empat aspek; impor korpus berizin; deduplikasi; konfirmasi kejadian/target; bandingkan sumber; buka kutipan; ekspor brief. Pisahkan sentimen terhadap petugas dan layanan; tentukan kebutuhan/urgensi melalui bukti eksplisit.

Mulai dengan berita/dokumen resmi yang hak penggunaannya diperiksa dan pertanyaan sukarela. Uji pencocokan kejadian, dukungan kutipan, kesalahan aspek, serta waktu menyusun brief dibanding pencarian manual. Lanjutkan jika calon pengguna mengonfirmasi keputusan tersebut dan korpus cukup mewakili sumber yang dibandingkan. Jangan mengklaim sampelnya sebagai opini nasional.

### 2. REKRUT AMAN: informasi resmi dan antrean klarifikasi

**Pengguna:** panitia dan calon peserta. **Keputusan:** informasi apa yang berlaku untuk kategori/periode tertentu, dan pertanyaan mana memerlukan petugas. Staff Sgt. Star membuktikan penggunaan asisten referensi rekrutmen; pemeriksaan indikasi pungutan dan dashboard kebingungan adalah adaptasi usulan.

MVP: satu periode, 30–50 butir informasi resmi bertanggal, pencarian dengan kutipan, jawaban belum cukup, dan pengelompokan pertanyaan sukarela. Tampilkan versi sumber, redaksi identitas dan jalur konfirmasi. Ukur relevansi rujukan, kecocokan periode, jawaban tanpa dukungan dan waktu pencarian. Pilihan ini menjadi fallback ketika korpus komunikasi bencana tidak memadai; data pertanyaan nyata tetap diperlukan untuk menguji kebutuhan pengguna.

### 3. SUARA SIAGA + CoverageMap: verifikasi kebutuhan sampai serah-terima

**Pengguna:** satu posko dan mitra bantuan. **Keputusan:** kebutuhan mana telah diverifikasi, diterima penanggung jawab dan dikonfirmasi hasilnya. QuakeMap dan WebEOC mendukung pengumpulan/verifikasi serta penugasan, bukan membuktikan paket fitur gabungan ini.

MVP: satu wilayah, daftar organisasi peserta, kebutuhan berbukti, status verifikasi, penugasan, penerimaan dan hasil. Gunakan ekspor berizin dari mitra; data sintetis diberi label dan hanya menguji alur. SNA berguna jika ada serah-terima lintas organisasi yang tercatat; tabel cukup untuk satu pengirim. Ukur ketepatan penggabungan kebutuhan, kelengkapan bukti dan waktu menemukan tugas belum diterima. Tanpa mitra dan catatan tindak lanjut, tunda pilihan ini.

## Arah sekunder dan pekerjaan validasi

**ResponseCheck** dapat mengadaptasi pola feedback ICE untuk memeriksa keluhan yang kembali setelah respons. **Portal pembelajaran kegiatan** dapat mengadaptasi proses NLLP dengan temuan, penanggung jawab, tindakan dan validasi. Keduanya memerlukan data longitudinal serta pengguna yang bersedia mengonfirmasi penyelesaian, sehingga bukan prioritas awal tanpa mitra.

Sebelum pengembangan, lakukan replay keputusan bersama pengguna, periksa izin data, lalu sepakati baseline dan biaya kesalahan. Riset ini belum menjalankan API/model, menguji aplikasi berautentikasi, mewawancarai pengguna atau mengukur keunggulan produk.

Rekomendasi merupakan interpretasi peneliti. Rubrik resmi menyebut kesesuaian dengan kebutuhan **pengamanan IT/OT TNI AD**; penempatan pada Siber Sosial/Dukungan Teknologi perlu menunjukkan hubungan tersebut. Konteks bantuan bencana saja tidak menjamin kelayakan submission atau adopsi. [Situs lomba](https://kartikacyberhackathon.id/).
