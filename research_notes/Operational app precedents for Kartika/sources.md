# Bukti penggunaan aplikasi untuk Kartika

**Tanggal peninjauan: 31 Oktober 2026, WIB.** Catatan ini mendukung [laporan utama](../../reports/Operational%20app%20precedents%20for%20Kartika.md). Metode: riset meja atas sumber primer publik. Observasi menunjukkan penggunaan yang dilaporkan instansi atau pembuat sistem; inferensi adaptasi dan hal yang belum terbukti dipisahkan. Tidak dilakukan eksekusi aplikasi, akses sistem internal, wawancara, benchmark, atau validasi pilot.

## Observasi dan batas klaim

### 1. Sprinklr dan Maven — komunikasi bantuan bencana

**Sumber/tanggal:** [U.S. Army, 22 Desember 2025](https://www.army.mil/article/289747/setaf_af_public_affairs_experiment_with_emerging_technology_to_shape_the_information_environment); penggunaan saat Hurricane Helene, 2024.

**Temuan:** Artikel resmi menyebut kantor public affairs XVIII Airborne Corps menggunakan Maven untuk memvisualisasikan sentimen media sosial dari Sprinklr selama krisis Helene. Kesaksian personel menyebut informasi bagi komando tersedia dalam hitungan menit. Ini contoh penggunaan respons bencana dengan instansi pengguna jelas.

**Batas:** Tidak tersedia ukuran akurasi atau dampak kausal. Eksperimen SETAF-AF dalam artikel yang sama bukan bukti deployment operasional penuh.

### 2. Staff Sgt. Star — rujukan bagi perekrut

**Sumber/tanggal:** [U.S. Army, 16 Juli 2026](https://www.army.mil/article/293913).

**Temuan:** Chatbot di Accessions Information Environment melayani pertanyaan kebijakan, regulasi, dan prosedur perekrutan dari repositori terkurasi. Artikel menyebut perekrut sudah menggunakannya dan sekitar 12.000 pengguna berizin dilayani. Referensi usang dapat dikeluarkan dari sistem.

**Batas:** Angka tersebut bukan pengguna aktif bulanan. Proyeksi 28.000 pengguna bukan realisasi; pengisian formulir otomatis masih rencana pengembangan.

### 3. QuakeMap/Ushahidi — kebutuhan penyintas

**Sumber/tanggal:** [Ushahidi, studi kasus Nepalese Army](https://www.ushahidi.com/in-action/nepalese-army-and-disaster-management/); kejadian April 2015, tanggal publikasi tidak dicantumkan.

**Temuan:** Kathmandu Living Labs mengumpulkan dan memverifikasi laporan warga sebelum Nepalese Army memprosesnya untuk respons gempa. Bukti mencakup lokasi, kebutuhan bantuan, urgensi, dan status verifikasi. Halaman mencatat sekitar 2.200 permintaan, termasuk 650 permintaan dukungan udara.

**Batas:** Angka permintaan bukan penyelamatan berhasil. Ini penggunaan operasional historis, bukan bukti QuakeMap masih aktif sekarang.

### 4. WebEOC — permintaan dan penugasan bantuan

**Sumber/tanggal:** [National Guard, 23 Oktober 2018](https://www.nationalguard.mil/News/Overseas-Operations/Article/1668966/florida-infantry-soldiers-provide-security-after-hurricane/); Hurricane Michael.

**Temuan:** Pejabat kota mengajukan kebutuhan sumber daya melalui WebEOC. Bay County Emergency Operations Center menyalurkan tugas kepada organisasi yang sesuai; Florida National Guard menerima tugas dari pusat tersebut dan membagikannya ke unit. Konteksnya respons bantuan pascabadai nyata.

**Batas:** Artikel tidak mengukur penghematan waktu, algoritme alokasi, analisis sentimen, atau SNA.

### 5. Interactive Customer Evaluation — umpan balik layanan

**Sumber/tanggal:** [Joint Base San Antonio, 30 Januari 2025](https://www.jbsa.mil/News/News/Article/4048110/jbsa-welcomes-new-ice-director/).

**Temuan:** JBSA memiliki pengelola ICE untuk sistem kartu komentar daring tentang layanan di instalasi militer. Pengelola layanan dan pimpinan memantau kepuasan melalui komentar serta laporan, termasuk perbandingan dengan layanan sejenis. Ini proses umpan balik institusional yang sudah dijalankan.

**Batas:** Sumber tidak membuktikan klasifikasi AI, pendeteksian keluhan berulang, atau bahwa penutupan kasus sama dengan penyelesaian terkonfirmasi.

### 6. NATO Lessons Learned Portal — pelacakan perbaikan

**Sumber/tanggal:** [ACT](https://www.act.nato.int/activities/nato-lessons-learned-portal/) dan [JALLC](https://www.jallc.nato.int/activities/lessons-learned), halaman tanpa tanggal publikasi; portal menggantikan database sebelumnya pada 2013.

**Temuan:** JALLC mengelola portal untuk menghimpun, mencari, membagikan, dan melacak observasi serta pelajaran NATO/mitra. Proses resminya mencatat keputusan, penugasan badan pelaksana, rencana tindakan, implementasi, dan validasi sebelum suatu temuan menjadi pelajaran yang telah diterapkan.

**Batas:** Penggunaan institusional tidak membuktikan SNA, analitik AI, tingkat adopsi aktif, atau ROI terukur.

### 7. InAWARE — situasi dan koordinasi kebencanaan

**Sumber/tanggal:** [Studi kasus PDC](https://www.pdc.org/inaware-program-case-study/), kejadian Oktober 2021; [ringkasan resmi BNPB](https://inaware.bnpb.go.id/inaware/public/inaware_about/index.html), tanpa tanggal publikasi.

**Temuan:** PDC mendokumentasikan penggunaan BNPB/BPBD saat banjir Luwu dan gempa Bali. Sistem menggabungkan informasi ancaman serta mendukung pertukaran data. BNPB mengonfirmasi sistem pendukung keputusan nasional/provinsi dikelolanya dengan akses terlindungi yang memerlukan registrasi dan persetujuan.

**Batas:** Tidak terbukti semua unit TNI menggunakannya. Data internal bukan korpus publik; manfaat kuantitatif belum diaudit dalam riset ini.

### 8. PetaBencana/Peta Gotong Royong — pembanding Indonesia

**Sumber/tanggal:** [FAQ resmi PetaBencana](https://info.petabencana.id/faq), tanpa tanggal publikasi; ditinjau 31 Oktober 2026.

**Temuan:** FAQ menyebut Peta Gotong Royong terintegrasi untuk menyampaikan kebutuhan makanan, air, obat, dan menghubungkan warga dengan pihak pemberi bantuan. FAQ juga menjelaskan arsip/Open API dan pembagian laporan kepada instansi seperti BNPB dan BMKG.

**Batas:** Kelengkapan API, hasil pencocokan bantuan, dan penyelesaian permintaan belum diuji. Ide menambah kebutuhan di atas peta laporan sudah bertumpang tindih secara lokal.

## Inferensi dan celah validasi

Preseden mendukung adaptasi proses: rujukan perekrutan bersumber, penugasan bantuan, umpan balik layanan, atau pelacakan perbaikan. Pemilihan satu proses untuk TNI tetap memerlukan pengguna mitra, data berizin, dan pembandingan dengan cara kerja saat ini. Belum ada bukti bahwa produk usulan lebih unggul, pertama di Indonesia, atau akan diterima penyelenggara Kartika; aturan lengkap serta kebutuhan pengguna perlu diperiksa tersendiri.
