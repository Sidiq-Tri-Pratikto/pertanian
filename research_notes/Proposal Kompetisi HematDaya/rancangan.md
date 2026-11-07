# Rancangan Proposal Teknis HematDaya

## Apa yang membuat proposal proyek mudah dinilai?

### Takeaway

Mulai dari keputusan konkret yang perlu diambil pengguna. Hubungkan masalah, bukti kebutuhan, cara kerja, pembeda, hasil yang sudah diperoleh, dan hasil berikutnya yang bisa diperiksa. Format UNS mengendalikan susunan akhir.

### Cited Findings

- UNS menilai kejelasan masalah, basis kebutuhan pengguna, kesesuaian tim, dan kesiapan hilirisasi. Fokus ST-03 mencakup pemantauan dan rekomendasi penghematan energi UMKM, serta pengukuran pada fasilitas kota. Proposal awal dibatasi tiga halaman A4, dengan bukti purwarupa sebagai dokumen terpisah dalam daftar persiapan. [Panduan UNS 2026, hlm. 5–8](https://drive.google.com/file/d/1an0TbEhoR4sODzk2psstv6Iux2m98DTS/view) · [Portal UNS](https://hackathonuns.id/)
- Buku ASN Digital AI Hackathon BKN memberi contoh urutan masalah, metode solusi, pengguna, keunggulan, dampak/skala, dan pelaksanaan. Penilaian proposal mencakup relevansi, inovasi, penerapan teknologi, dan dampak. Rubrik ini merupakan pembanding editorial. [Buku BKN](https://hackathon.bkn.go.id/download-panduan)
- Panduan PKM-Karsa Cipta 2026 meminta perbandingan karya sejenis, uraian cara pembuatan dari desain sampai prototipe, dan hubungan tahap dengan luaran. Bobot kriteria substansi utamanya mencakup orisinalitas/manfaat (20), kemutakhiran teknologi (20), kesesuaian tahap (15), dan kontribusi produk terhadap masalah (25). [Panduan PKM-KC 2026, bagian sistematika dan Lampiran 7](https://lldikti16.kemdiktisaintek.go.id/wp-content/uploads/2026/03/PKM-KC_Karsa_Cipta_2026.pdf#page=25)
- Badan Bahasa menguraikan kelugasan, ketepatan, kejelasan, kehematan, dan kesejajaran sebagai ciri kalimat efektif. DJKN menambahkan sudut pandang pembaca, kalimat persuasif yang ringkas, keluaran terukur, dan waktu pencapaian. [Badan Bahasa, Kalimat](https://badanbahasa.kemendikdasmen.go.id/resource/doc/files/Buku_Penyuluhan_Kalimat.pdf#page=60) · [DJKN, Penulisan Proposal](https://www.djkn.kemenkeu.go.id/kpknl-lhokseumawe/baca-berita/32428/Penulisan-Proposal-yang-Baik-dan-Berkualitas-dalam-Forum-Sanger-Kanwil-DJKN-Aceh.html)
- Pitch TemuRiset memisahkan keadaan saat ini, sasaran, dan kebutuhan uji, serta memberi penanda pada contoh ilustratif. HematDaya UMY memisahkan cara kerja, kondisi dan target, peta jalan, risiko data, serta pemilik tugas. Usulan UMY mengikuti tema kesehatan dan format acaranya sendiri. [Pitch TemuRiset, slide 2–9](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/temuriset/pitch/TemuRiset_Pitch.pptx) · [Proposal HematDaya UMY](/home/ahmad-widardi/Projects/random/pertanian/docs/umy-2026-hematdaya/submission/proposal/Proposal-HematDaya-UMY.md)

### Inferences

- Pada awal naskah, sebut pengguna sebagai pemilik atau pengelola UMKM dan penanggung jawab sarana fasilitas kota. Jelaskan keputusan operasionalnya, misalnya perangkat atau sirkuit mana yang perlu diperiksa lebih dulu dan jam mana yang perlu ditinjau.
- Jika sampul dan identitas tetap terpisah, prioritaskan satu contoh angka, tiga sasaran uji, dan tiga tahap pada substansi. Jika kebutuhan rincian menuntut dua halaman substansi, pertahankan elemen resmi dengan menggabungkan sampul dan identitas secara rapi pada halaman pertama dan ungkapkan penyesuaian tata letak. Bukti tangkapan layar dapat tetap terpisah.
- Hindari istilah kabur seperti “algoritme cerdas meningkatkan efisiensi”. Contoh kalimat konkret: “Sistem menolak total gabungan ketika cakupan meter utama dan submeter bertumpang tindih, lalu menunjukkan rincian dari cakupan yang dipilih.” Satu paragraf menjawab satu pertanyaan juri.

### Gaps

- Tidak ditemukan petunjuk publik yang secara eksplisit mengecualikan sampul atau lembar identitas dari batas tiga halaman UNS. Jangan mengandalkan format acara lain untuk pengecualian.

## Bukti dan pembeda apa yang bisa dimasukkan tanpa klaim berlebihan?

### Takeaway

Gunakan data publik untuk konteks, data simulasi dan pemeriksaan otomatis untuk membuktikan cara kerja, serta sasaran uji untuk rencana. Jangan menggabungkan ketiganya dalam satu klaim dampak.

### Cited Findings

- Studi Fisika Teknik UGM tahun 2023 mengaudit Gedung Dinas Perpustakaan dan Kearsipan Surakarta. Tata udara menyumbang sekitar 79,1% konsumsi listrik gedung, penerangan 8,9%, dan penunjang operasi 12%. Ini contoh lokal nilai penguraian beban pada satu fasilitas kota. [Abstrak penelitian UGM](https://etd.repository.ugm.ac.id/penelitian/detail/230573)
- BPSDM ESDM melaporkan bahwa audit 12 gedung Pemda DKI mengidentifikasi potensi penghematan 3,73 juta kWh per tahun. Angka tersebut berasal dari audit gedung yang dilaporkan dan menggambarkan potensi, bukan penghematan terealisasi. [BPSDM ESDM](https://bpsdm.esdm.go.id/index.php/posts/2025/09/18/jakarta-menuju-gedung-hemat-energi-ppsdm-kebtke-dan-pemprov-dki-perkuat-manajemen-energi/4044)
- Home Assistant juga mendukung hierarki meter agar beban yang sama tidak dihitung dua kali. HematDaya generik mensyaratkan cakupan eksplisit, penolakan penjumlahan yang belum terbukti terpisah, pelabelan data hilang, dan perbandingan terhadap median rentang hari dan jam yang sama dengan cakupan data bersama. [Dokumentasi Home Assistant](https://www.home-assistant.io/docs/energy/individual-devices/#upstream-devices-and-hierarchies) · [PRD HematDaya Generik 1.2, §§5.2, 11.3, 11.6 dan 12](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)
- Catatan verifikasi memuat 36 dari 36 pemeriksaan otomatis pada logika prototipe peramban, termasuk meter induk 10 kWh dan submeter 1 kWh, impor ulang tanpa menduplikasi pembacaan, celah data, dan skenario kompresor sintetis 3 kWh dibanding median 0 kWh. Pemeriksaan diulang pada 7 November 2026 melalui `node tests/domain.test.js` (Node 25.2.1) dan kembali lulus 36 dari 36. [Catatan verifikasi prototipe](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/prototype/ACCEPTANCE.md) · [Skrip pemeriksaan](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/prototype/tests/domain.test.js)
- Riwayat sumber aplikasi meliputi inti perhitungan energi, perbandingan, bukti, layar demo, ringkasan, rincian aset, pengolahan CSV dan API komit impor. PRD membedakan gerbang layanan tersimpan, kegunaan, dan uji meter langsung. Hasil simulasi tetap terpisah dari tahap verifikasi aplikasi dan lapangan. [Peta jalan aplikasi](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/roadmap/README.md) · [PRD, §21](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)

### Inferences

- Rumusan yang hemat tempat: “Pada simulasi, pembacaan 10 kWh dari meter utama sudah mencakup 1 kWh dari submeter. HematDaya menampilkan total 10 kWh dan tetap menyediakan rincian 1 kWh. Saat data tidak lengkap, aplikasi menampilkan cakupan yang tersedia sebelum memberi saran.” Hubungkan angka dengan keputusan pengguna.
- Jelaskan pembeda sebagai alur gabungan yang akan diuji pada UMKM dan fasilitas kota, yakni impor CSV, pemeriksaan mutu/cakupan, riwayat sebanding, dan penelusuran alasan saran dalam bahasa Indonesia. Pembanding mendukung klaim perbandingan yang spesifik, bukan klaim semua fitur belum pernah ada.
- Laporkan “TKT 3 berdasarkan penilaian tim” dan “progres pengembangan 80% menurut estimasi tim” secara terpisah. Tambahkan satu kalimat yang menyebut 36 pemeriksaan lulus dan ruang lingkupnya.
- Gunakan contoh kompresor sebagai ilustrasi keputusan. Pemakaian 3 kWh pada jam di luar jadwal memicu pemeriksaan konteks operasi, seperti jadwal pekerjaan yang berubah. Penentu tindakan adalah pengelola, dan sistem hanya memantau serta memberi saran.

### Gaps

- Belum ada data wawancara langsung, lokasi uji, persetujuan mitra, pengukuran penghematan, atau kesediaan membayar yang terverifikasi untuk pengajuan UNS. Studi Surakarta tidak menjadikan instansi yang diteliti sebagai mitra HematDaya.

## Bagaimana mengubah peta jalan menjadi rencana uji dan hilirisasi?

### Takeaway

Setiap tahap punya keluaran yang bisa diperiksa. Pisahkan uji hitung, uji kegunaan, uji lapangan, dan uji pasar supaya penilai memahami risiko yang dijawab masing-masing.

### Cited Findings

- PRD menargetkan sedikitnya 4 dari 5 pengguna baru mampu menemukan kontributor terukur terbesar dalam 30 detik dan sedikitnya 4 dari 5 mampu menafsirkan tugas inti tanpa bantuan. Catat waktu, bantuan, salah langkah, dan salah tafsir cakupan/kualitas. Evaluasi konteks rumah tangga dan usaha/industri secara terpisah; uji UNS pada sasaran awal hanya mendukung konteks peserta uji. [PRD, §§3 dan 20.1](/home/ahmad-widardi/Projects/random/pertanian/applications/generic/hematdaya/docs/product/PRD-ID.md)
- FEMP menetapkan penentuan acuan dan batas pengukuran sebelum tindakan. Verifikasi membandingkan periode setelah tindakan dengan acuan dan memperhitungkan faktor yang berubah, seperti volume produksi dan jam operasi. [U.S. DOE FEMP M&V Guidelines v5.0, §§2.1–2.2](https://www.energy.gov/sites/default/files/2024-10/mv_guide_5_0.pdf#page=18)
- Buku UNS menjadwalkan pelatihan dan klinik kebutuhan pada November, hackathon pada Desember, dan fase inkubasi setelahnya. [Panduan UNS, hlm. 8–9](https://drive.google.com/file/d/1an0TbEhoR4sODzk2psstv6Iux2m98DTS/view)

### Inferences

- Nov–Des 2026: jika mengikuti klinik, wawancarai pengelola untuk memastikan keputusan, data, dan batas kendali. Selesaikan alur impor pada antarmuka. Keluaran berupa catatan kebutuhan, skenario demo, serta hasil uji acuan angka dan pengulangan impor.
- Jan–Feb 2027: validasi komponen dalam lingkungan terkendali menuju target TKT 4. Uji kepada lima pengelola pada konteks yang dilaporkan. Keluaran berupa laporan lulus/gagal pemeriksaan dan catatan tugas pengguna.
- Mar–Mei 2027: jajaki uji terbatas satu lokasi dengan izin akses dan cakupan meter yang disepakati. Bandingkan kWh sebelum dan sesudah tindakan pada kondisi sebanding, catat jam operasi, volume produksi bila relevan, serta celah data. Hipotesis komersialnya adalah langganan per lokasi untuk ringkasan berkala. Uji minat, kesediaan membayar, dan waktu penyiapan dengan pengelola. Bedakan niat dari pembelian.
- Pembagian kerja dapat mencantumkan dua pengembang berbagi tanggung jawab rekayasa perangkat lunak dan AI, dengan tambahan penanggung jawab bisnis/validasi serta UI. Konsultan AI menilai metode pembanding, interpretasi data, dan hasil uji. Posisi ketua resmi harus mengikuti keputusan tim dan syarat UNS.

### Gaps

- Ambang penghematan, harga langganan, dan komitmen mitra belum ditetapkan dari data. Tandai sebagai hal yang akan diuji; data yang belum ada tidak perlu diisi dengan persentase perkiraan.
