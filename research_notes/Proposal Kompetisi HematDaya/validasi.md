# Bukti kebutuhan dan rencana uji HematDaya

## 1. Bukti kebutuhan apa yang relevan untuk ST-03

### Takeaway

Gunakan satu konteks lokal untuk mendefinisikan pengguna yang akan direkrut dan satu bukti audit untuk menunjukkan mengapa pemeriksaan energi perlu dilakukan pada tingkat peralatan atau sirkuit. Bedakan lokasi studi, lokasi sasaran, dan pihak yang baru akan diajak bekerja sama.

### Cited Findings

- ST-03 UNS menargetkan efisiensi energi fasilitas kota dan UMKM dengan data serta sensor. Panduan menyebut pemantauan dan rekomendasi penghematan UMKM sebagai salah satu fokus dan menempatkan klinik pemilik masalah sebelum pengembangan purwarupa. Portal menerima pendekatan digital penuh, fisik, atau campuran. [Panduan UNS 2026, hlm. 5 dan 8–9](https://drive.google.com/file/d/1an0TbEhoR4sODzk2psstv6Iux2m98DTS/view) · [Portal UNS, subtema dan kerangka](https://hackathonuns.id/)
- PPID Sukoharjo mencatat sentra mebel rotan di Trangsan, batik di Kedunggudel, dan gamelan di Wirun. Data ini memberi konteks geografis dan sektor untuk perekrutan calon pengguna. [Profil UMKM Kabupaten Sukoharjo, 14 Januari 2025](https://ppid.sukoharjokab.go.id/2025/01/14/profil-perkembangan-koperasi-umkm-dan-perdagangan-kabupaten-sukoharjo/)
- Audit Gedung 3 Fakultas Teknik UNS menemukan pendinginan ruang hingga 18,5 °C pada unit AC dengan kinerja teknis yang dinilai baik. Ini contoh lokal bahwa perilaku operasional dapat memerlukan pemeriksaan kendati peralatan masih berfungsi. Temuan berasal dari gedung yang diaudit. [Abstrak audit energi Gedung 3 FT UNS](https://digilib.uns.ac.id/dokumen/abstrak/1000649/AUDIT-ENERGI-PADA-GEDUNG-3-FAKULTAS-TEKNIK-UNIVERSITAS-SEBELAS-MARET)
- BPSDM ESDM melaporkan **potensi** penghematan 3,73 juta kWh per tahun berdasarkan audit 12 gedung Pemda DKI. Angka berlaku untuk 12 gedung yang diaudit. [BPSDM ESDM, 18 September 2025](https://bpsdm.esdm.go.id/index.php/posts/2025/09/18/jakarta-menuju-gedung-hemat-energi-ppsdm-kebtke-dan-pemprov-dki-perkuat-manajemen-energi/4044)
- Program restrukturisasi mesin Kemenperin menjadikan efisiensi energi salah satu alasan peningkatan peralatan IKM. Data konsumsi per beban dapat membantu pemilik memilih peralatan yang layak diperiksa sebelum mengusulkan perubahan atau investasi. Kalimat kedua adalah inferensi. [Kemenperin, Restrukturisasi Mesin Peralatan](https://ikm.kemenperin.go.id/restrukturisasi-mesin-peralatan)

### Inferences

- Redaksi pendek yang siap dipakai: “Pengelola bengkel atau IKM perlu menentukan mesin yang harus diperiksa ketika pemakaian listrik berubah. Tagihan bulanan hanya menyediakan total lokasi. Sukoharjo memiliki sentra mebel rotan di Trangsan yang dapat dijajaki untuk wawancara pengguna [1]. Di fasilitas publik, audit 12 gedung Pemda DKI menemukan potensi penghematan 3,73 juta kWh per tahun [2]. HematDaya menguji apakah catatan per perangkat atau sirkuit membantu pengelola menentukan prioritas pemeriksaan.” Bila memilih versi lebih lokal, ganti angka DKI dengan satu kalimat tentang audit Gedung 3 FT UNS; jangan simpulkan aplikasi dapat mengukur suhu atau memastikan penyebab.
- Batasi sasaran awal pada **pengelola satu lokasi yang dapat menyediakan pembacaan interval atau berkas CSV**. Fasilitas kota tetap menjadi penerapan yang dapat dijajaki. Sebut kebutuhan wawancara, pemilik data, dan akses satu lokasi pada klinik UNS. Posisi sentra/instansi sebatas calon kanal rekrutmen selama belum ada kesepakatan.

### Gaps

- Belum tersedia hasil wawancara, profil pemakaian beban, persetujuan data, kesepakatan uji coba, atau angka pemborosan dari pengguna sasaran HematDaya.
- Tabel statistik BPS Jawa Tengah yang terindeks mencatat 18.583 unit usaha industri mikro dan kecil Sukoharjo pada 2024. Akses langsung tabel menghasilkan 403, sehingga lebih aman memakai profil PPID. Bila angka dipakai setelah tabel diverifikasi, kategorinya industri mikro dan kecil, sehingga angkanya hanya konteks populasi, tanpa inferensi tentang jumlah pelanggan atau besaran penghematan. [Tabel statistik BPS Jawa Tengah](https://jateng.bps.go.id/id/statistics-table/2/MjY4OCMy/jumlah-perusahaan-tenaga-kerja-dan-nilai-produksi-pada-industri-mikro-dan-kecil-menurut-kabupaten-kota-di-provinsi-jawa-tengah.html)

## 2. Bagaimana membuktikan solusi dan membatasi klaim

### Takeaway

Susun penilaian berlapis untuk akurasi perhitungan, kemampuan pengguna mengambil keputusan, dan perubahan konsumsi setelah tindakan. Setiap lapis memiliki data, prosedur, dan kriteria lulus tersendiri.

### Cited Findings

- PRD Generik 1.2 memakai impor CSV sebagai jalur awal dan model perangkat/sirkuit dengan sumber otoritatif serta cakupan eksplisit. Riwayat setara menggunakan waktu lokal yang sepadan, aset dan jadwal sama, sedikitnya dua dari tiga rentang historis, dan cakupan waktu valid bersama minimal 90%. Median menjadi pembanding. Bila prasyarat gagal, tampilan menjaga total tercatat dan menahan saran perubahan. [PRD, §§ 4–5, 10, 11.6, 12](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)
- Contoh fixture: meter induk 10 kWh yang sudah mencakup cabang 1 kWh tetap berjumlah 10 kWh untuk tampilan induk. Setengah data hilang berarti cakupan 50% dan energi parsial, sehingga saran perubahan setara ditahan. Demo sintetis industri menampilkan kompresor memakai 3,000 kWh di luar jadwal pada 19–25 Oktober 2026, dibanding median 0,000 kWh. Bukti menampilkan selisih +3 kWh tanpa persentase karena pembanding nol. Ini angka simulasi yang bisa diverifikasi dari fixture dan lampiran. [PRD, §§ 19.1, 19.3–19.4](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md) · [Bukti Purwarupa](/home/ahmad-widardi/Projects/random/pertanian/docs/uns-2026-hematdaya/submission/Bukti-Purwarupa-HematDaya-UNS-2026.pdf)
- Riwayat kode hingga commit 42aeebc mencakup Beranda demo, daftar dan rincian aset, Saran dan dasar bukti, serta parser, pratinjau, dan komit CSV pada layanan. Penyelesaian alur impor pengguna, pengaturan tarif, jadwal dan keluaran, penggunaan meter langsung, serta pengujian lapangan memiliki tahap tersendiri. [Peta jalan HematDaya](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/roadmap/README.md) · [PRD, §§ 20–21](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)
- Dokumentasi Home Assistant juga menyediakan relasi meter induk dan perangkat sebagai cara menangani penghitungan ganda. Pembeda yang dapat diusulkan HematDaya adalah alur CSV lebih dulu, cakupan serta kualitas data yang terlihat, dan saran yang merujuk bukti sehingga pengguna awal dapat memeriksa tanpa integrasi meter langsung. Kemudahan alur tersebut masih hipotesis yang harus diuji. [Home Assistant, Integrating individual device energy usage](https://www.home-assistant.io/docs/energy/individual-devices/) · [PRD, §§ 4–5, 12, 20](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)
- PRD menargetkan sedikitnya 4 dari 5 pengguna baru dapat menafsirkan tanpa bantuan dan sedikitnya 4 dari 5 mengidentifikasi kontributor terbesar dalam 30 detik, dengan hasil terpisah untuk kelompok rumah tangga dan usaha/industri. Untuk lomba prioritaskan lima pengelola UMKM; hasilnya mendukung evaluasi formatif di segmen tersebut. Pedoman GOV.UK mendukung tugas netral, mengamati penyelesaian, dan pembelajaran putaran kecil. [PRD, §§ 3 dan 20.1](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md) · [GOV.UK, Moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) · [GOV.UK, Plan user research](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service)
- Pedoman FEMP menghitung penghematan terhadap konsumsi acuan yang disesuaikan, dikurangi konsumsi setelah tindakan. Faktor yang relevan antara lain jam operasi, volume produksi, okupansi, dan cuaca. Untuk pilot satu beban, tetapkan batas alat/sirkuit dan faktor penyesuai sebelum perubahan, kemudian catat cakupan data serta ketidakpastian. [FEMP, Guidance for implementation and follow-up](https://www.energy.gov/femp/articles/guidance-implementation-and-follow-identified-energy-and-water-efficiency-measures) · [DOE AMO eGuide, Monitoring and measurement](https://www1.eere.energy.gov/manufacturing/eguide/iso_step_4_1.html)

### Inferences

- **Uji teknis terkendali.** Tetapkan fixture acuan yang lulus untuk total kWh, periode setara, penolakan cakupan tumpang tindih, pemisahan nol dan data hilang, serta impor ulang. Catat lingkungan, masukan dan hasil yang diharapkan/aktual. Klaim “semua fixture acuan lulus” baru layak jika hasil terdokumentasi. Contoh singkat di proposal cukup 10/1 kWh atau demo kompresor 3/0 kWh.
- **Uji kegunaan.** Minta lima pengelola baru mencari beban terbesar, menyebut apa yang tercakup di total, dan menjelaskan bagian yang belum diketahui pada saran. Laporkan per tugas dan tanpa bantuan. Ukuran 4 dari 5 dalam ≤30 detik berlaku untuk menemukan kontributor; persentase studi kecil berfungsi untuk perbaikan produk.
- **Uji operasional bersyarat.** Setelah izin lokasi dan data, ukur satu sirkuit sebelum dan sesudah satu tindakan pengelola. Samakan batas pengukuran serta rentang, catat jam operasi dan volume yang tersedia, dan ungkap perubahan keadaan yang relevan. Jika belum ada tindakan atau pembanding layak, luaran tetap berupa laporan konsumsi/kualitas data. Penggunaan energi di luar jadwal adalah pemicu pemeriksaan, sedangkan dampak tindakan dinilai terpisah.
- Kalimat kesiapan: “TKT 3 menurut penilaian internal tim. Kemajuan pengembangan diperkirakan 80%. Rilis uji telah memuat demo data sintetis, rincian aset, dan dasar saran. Target berikutnya adalah validasi komponen di lingkungan terkendali menuju TKT 4.” Bila menyebut AI, jelaskan landasan awal berupa aturan statistik deterministik yang menghasilkan bukti, dengan AI sebagai arah evaluasi lanjutan. [Permenristekdikti 42/2016](https://peraturan.bpk.go.id/Details/141280/permen-ristekdikti-no-42-tahun-2016) · [PRD, §§ 12 dan 21](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)

### Gaps

- Belum ada data hasil uji pengguna, akurasi pembacaan meter di instalasi sasaran, penghematan pascatindakan, atau hasil perbandingan kuantitatif dengan aplikasi lain.
- Estimasi 80% berasal dari tim. Catatan kode membuktikan implementasi yang telah digabungkan, sementara penilaian TKT formal, status pengujian setiap komponen, dan persentase kemajuan bergantung pada definisi rilis yang digunakan.

## 3. Bagaimana menguji jalur adopsi selama program

### Takeaway

Ajukan pilot ringan satu lokasi dan uji minat langganan sebagai hipotesis. Proposal lebih mudah dinilai bila menunjukkan pemilik keputusan, masukan yang diperlukan, hasil yang diterima pengguna, dan syarat untuk melanjutkan.

### Cited Findings

- Panduan menempatkan Klinik Pemilik Masalah pada 20 November 2026, pengembangan purwarupa terbimbing pada 28 November, hackathon pada 4–6 Desember, dan inkubasi pada Januari–Mei 2027. Portal menulis Januari–April untuk inkubasi. Hindari mengklaim peserta sudah menerima jadwal pendampingan. [Panduan UNS 2026, hlm. 8–9](https://drive.google.com/file/d/1an0TbEhoR4sODzk2psstv6Iux2m98DTS/view) · [Portal UNS](https://hackathonuns.id/)
- PRD memulai dari satu lokasi dan satu akun pemilik, menempatkan dukungan meter langsung setelah uji pembanding dan pemasangan sesuai instalasi, serta menunda dasbor lintas lokasi dan penagihan SaaS. [PRD, §§ 3, 4.2, 21](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)
- Kementerian ESDM memisahkan peran pemantauan/manajemen energi dari audit energi tersertifikasi. Untuk tahap ini, fungsi produk cocok untuk memprioritaskan pemeriksaan internal. [Permen ESDM 8/2025](https://jdih.esdm.go.id/dokumen/view?id=2558) · [PPSDM Migas, layanan audit profesional](https://bpsdm.esdm.go.id/posts/2026/03/11/ppsdm-migas-hadirkan-layanan-audit-dan-manajemen-energi-profesional/4294)

### Inferences

- **Nov–Des 2026.** Pada klinik, wawancarai pengelola calon lokasi dan mintalah contoh struktur data yang boleh digunakan. Pilih satu keputusan nyata seperti memeriksa jadwal satu beban. Lengkapi alur impor pengguna dan catat hasil fixture teknis.
- **Jan–Feb 2027.** Uji komponen terintegrasi dalam lingkungan terkendali, lakukan uji tugas pada lima pengelola, dan revisi penjelasan berdasarkan salah tafsir. Target TKT 4 tergantung hasil pengujian dan bukti.
- **Mar–Mei 2027.** Jika mendapat izin lokasi dan data, uji satu lokasi, tunjukkan daftar pemeriksaan, cakupan, riwayat, dan hasil sebelum–sesudah yang dapat diulas pengelola. Tanyakan apakah pengelola ingin mengulangi penggunaan dan siapa yang berwenang membayar layanan bulanan per lokasi. Catat jumlah pihak yang bersedia melanjutkan dan alasan penolakan. Minat atau kesediaan melanjutkan adalah sinyal, sementara pendapatan baru dapat diklaim setelah transaksi.
- **Tanggung jawab.** Penanggung jawab bisnis menguji kebutuhan, adopsi, dan kanal rekrutmen; rekayasawan menguji impor, lingkup dan pemulihan; konsultan AI meninjau kaidah pembanding, mutu data, serta batas interpretasi. Cantumkan hanya peran yang sesuai susunan resmi yang dikonfirmasi.

### Gaps

- Belum ada kesepakatan mitra, dukungan biaya atau akses data, kesediaan membayar, harga yang disepakati, atau hasil pengujian dampak. Tempatkan ini sebagai hal yang hendak dipelajari selama program.
