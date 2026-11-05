# TemuRiset — Kebutuhan produk generik

Versi 1.1 · 31 Oktober 2026 · Asia/Jakarta

Status: arah produk dan arsitektur telah disetujui pengguna; rincian awal implementasi tetap merupakan usulan pada bagian yang menyatakannya. Perilaku aplikasi dan design system belum diimplementasikan atau diverifikasi berdasarkan dokumen ini.

Pembaca utama: tim produk, desain, engineering, quality assurance dan delivery.

Bahasa dokumen: Indonesia, sebagai edisi lengkap dengan arah yang sama seperti dokumen Inggris. Dokumen Inggris menjadi acuan kanonis untuk kontrak teknis yang harus persis. Bahasa antarmuka awal: Indonesia, dengan lokalisasi yang dapat dikonfigurasi.

## 0. Acuan dan cara membaca

Dokumen ini menetapkan dasar produk TemuRiset yang dapat digunakan kembali. Addendum klien mencatat perbedaan yang disengaja menggunakan [template ekstensi](CLIENT_EXTENSION_TEMPLATE.md). Perilaku yang tidak disebutkan dalam addendum mengikuti dokumen dasar. Addendum tidak boleh diam-diam melemahkan otorisasi, label bukti, makna nominal keuangan, integritas transaksi atau persetujuan. Perubahan aturan dasar tersebut memerlukan peninjauan versi dasar dan rencana migrasi.

Pengguna telah menyetujui modular monolith dengan core bersama yang terus dipelihara, konfigurasi tervalidasi, capability yang diuji, adapter konkret dan rilis sumber bersama, serta pilihan deployment klien yang terisolasi. Ini merupakan arah desain yang disetujui, bukan bukti implementasi. Pilihan stack/provider tertentu, model, kebijakan angka dan rincian performa yang belum diukur masih merupakan usulan awal. Kedua bahasa mempertahankan kebutuhan yang sama; jika terdapat perbedaan terjemahan teknis, gunakan kontrak Inggris kanonis lalu perbaiki teks Indonesia, bukan mengubah perilaku tanpa penjelasan.

Kebutuhan bertanda **R1** termasuk rilis kerja lengkap pertama. **R2** memperkuat produk untuk pilot operasional yang lebih luas. **L** adalah pengembangan berikutnya yang membutuhkan alasan tersendiri. Penanda ini menunjukkan prioritas pengerjaan, bukan pekerjaan yang telah selesai. Seluruh skenario penerimaan pada bagian 23 dimulai dengan status **NOT RUN** atau belum dijalankan. Batas angka, bobot, ambang dan sasaran performa merupakan usulan awal yang harus diukur dan diperbarui; bukan hasil penelitian atau jaminan tingkat layanan.

Dalam produk ini, inovasi merujuk pada solusi terapan atau proyek pengembangan, bukan sertifikasi kebaruan, kelayakan paten, kepemilikan atau nilai komersial. “Investor” menyatakan minat dan kriteria dukungan yang dinyatakan pihak tersebut, bukan rekomendasi platform. “Dikonfirmasi” berarti pihak terkait menyetujui ringkasan yang dicatat di aplikasi, bukan verifikasi independen atau pelaksanaan transaksi hukum. AccessGrant atau grant akses adalah izin mengakses resource tertentu; maknanya berbeda dari grant dalam konteks pendanaan, yaitu hibah.

## 1. Tujuan, masalah dan hasil yang diharapkan

TemuRiset membantu inovator menemukan investor dan mitra lain yang dapat membantu memajukan inovasinya. Sistem mempertemukan penjelasan masalah, solusi yang sudah ada dan permintaan dukungan dengan mandat, sumber daya serta persyaratan pengajuan penerima. Perkenalan tersebut dilanjutkan melalui peninjauan, revisi, diskusi dan pencatatan kerja sama yang dikonfirmasi secara terpisah.

Inovator dapat berupa individu independen, tim startup, karyawan yang mewakili organisasi, kelompok riset perusahaan, organisasi nonprofit, tim komunitas atau peneliti. Inovasi dapat berupa perangkat, produk software, proses, material, formulasi atau solusi terapan lainnya. Istilah dan bukti khusus sektor dikonfigurasi untuk peluang yang relevan. Afiliasi institusi, pendirian perusahaan, paten, skor kesiapan formal atau video bukan persyaratan universal.

Inovator menghadapi presentasi yang tersebar, kecocokan mitra yang tidak jelas dan permintaan informasi berulang. Investor dan mitra perlu memahami apa yang sudah tersedia, dukungan yang dicari, siapa yang berwenang, apa yang belum diketahui dan tindakan berikutnya. Direktori saja belum menyelesaikannya. Produk karena itu menghubungkan pencarian dengan alur evaluasi bersama, sambil menjaga agar pengungkapan informasi sensitif tetap dilakukan secara sadar.

Hasil utama adalah **diskusi yang relevan selesai dilakukan dengan kedua pihak memahami dukungan yang diminta, bukti yang tersedia dan langkah berikutnya**. Ukuran pendukung mencakup waktu menyiapkan pitching yang sesuai, penyelesaian item revisi, konfirmasi pertemuan dan ketepatan pencatatan hasil. Dana yang diperoleh, lisensi yang benar-benar disepakati dan adopsi merupakan hasil jangka panjang dengan tanggal serta asal informasi; tidak dapat disimpulkan dari klik, inovasi tersimpan atau pitching yang disetujui.

## 2. Batas produk dan cakupan rilis

R1 harus mendukung alur lengkap: menetapkan identitas → menyiapkan profil inovasi nonrahasia → menyatakan kebutuhan dukungan atau pendanaan perusahaan → menemukan investor atau mitra relevan → memeriksa persyaratan → mengirim pitching secara sadar → meninjau atau meminta revisi → menyepakati pertemuan → mencatat hasil → mengusulkan dan mengonfirmasi ringkasan kerja sama. Formulir manual, aturan deterministik dan template brief harus tetap bekerja tanpa AI.

R1 mencakup pencarian dukungan proyek, co-development, validasi, manufaktur, distribusi dan lisensi, serta pencarian investasi pada perusahaan. Antarmuka hanya membuka isian yang relevan dengan tujuan terpilih. Pencarian investor merupakan tugas utama, bukan direktori tambahan yang tersembunyi di balik review institusi. Peluncuran kecil dapat merekrut satu kelompok penyedia dan pencari dukungan yang saling melengkapi, sambil mempertahankan model serta pengujian lintas sektor.

| Capability | R1 | R2 | L |
|---|---|---|---|
| Identitas dan izin | Email terverifikasi atau akun demo tertutup berlabel jelas; konteks pribadi dan organisasi; undangan tim dasar yang dapat kedaluwarsa/dicabut | Administrasi tim lebih lengkap dan antrean verifikasi operasional | Provider identitas tambahan ketika benar-benar diperlukan |
| Portofolio dan bukti | Draf, gambar, tautan video HTTPS, file terpilih, sumber dan publikasi berversi | Pemrosesan media dan alur bukti lebih lengkap | Integrasi registry terverifikasi |
| Pencarian investor dan mitra | Mandat eksplisit, penerimaan aktif, permintaan dukungan dan pendanaan perusahaan | Pengumpulan/impor terkurasi dengan konfirmasi pemilik | Personalisasi perilaku yang tervalidasi |
| Matching | Aturan bertipe, evaluasi seluruh korpus kecil, baseline lexical dan alasan | Dense retrieval serta reranking opsional berdasarkan pengukuran | Ranking terlatih setelah label hasil memadai |
| Kolaborasi | Snapshot pitching, tiga keputusan, revisi, diskusi, slot, ICS dan konfirmasi kerja sama | Preferensi email, alur tim lebih lengkap, sinkronisasi kalender opsional | Integrasi provider perjanjian setelah desain terpisah |
| Reuse | Sumber bersama, komposisi tervalidasi dan addendum klien | Deployment dan adapter klien yang didukung sesuai kebutuhan | Pooled SaaS atau federasi hanya setelah persetujuan eksplisit |

Di luar cakupan dasar: menahan atau mentransfer uang, menerbitkan saham, melaksanakan penawaran efek, transaksi crowdfunding, valuasi otomatis, nasihat investasi, jaminan perkenalan, administrasi cap table, penetapan kepemilikan secara hukum, sertifikasi regulasi universal, penilaian kelayakan paten, outreach massal tanpa permintaan, rating publik inovator dan CRM enterprise umum. Bentuk pembiayaan seperti utang, instrumen konversi, hibah atau sponsor dapat dicatat sebagai kategori diskusi yang dinyatakan; pelaksanaan atau administrasinya memerlukan keputusan produk tersendiri.

## 3. Pengguna, konteks dan kewenangan

Terdapat tepat dua persona onboarding publik: **Inovator (Inventor)** dan **Investor/Mitra (Investor/Partner)**. Persona menentukan bahasa, navigasi awal dan pertanyaan onboarding, bukan role pengendalian akses. Investor, produsen, distributor, fasilitas validasi, mentor dan penyedia dukungan lain merupakan subtipe persona kedua. Reviewer, moderator dan operator menerima capability terbatas sesuai cakupan; mereka bukan persona pasar tambahan.

Gunakan istilah antarmuka Indonesia yang konsisten dan alami: Inventor → **Inovator**; Investor/Partner → **Investor/Mitra**; tujuan portofolio → **Inovasi Saya**; pencarian → **Temukan Investor/Mitra**; project support → **Dukungan Proyek**; company funding → **Pendanaan Perusahaan**; round target → **Target Pendanaan**; investor contribution range → **Kisaran kontribusi per investor**; relationship/partnership → **Kerja Sama**. Entitas domain Inggris Invention tetap dipertahankan; copy antarmuka tidak harus menerjemahkan nama entitas teknis secara harfiah.

Akun mempunyai satu tujuan onboarding utama pada R1. Seseorang kemudian dapat bekerja dalam beberapa konteks yang diizinkan tanpa menggabungkan hak aksesnya. Memilih organisasi hanya mengubah konteks kerja aktif setelah keanggotaan diperiksa. Inovator independen dan investor individu memakai konteks pribadi yang didukung; keduanya tidak perlu membuat institusi atau perusahaan fiktif.

| Konsep | Arti dan batas |
|---|---|
| Account | Identitas login dengan status kontak terverifikasi, locale dan zona waktu tampilan |
| Person atau contributor | Orang bernama yang terkait dengan karya; tidak harus memiliki akun |
| Organization | Pelaku organisasi, misalnya perusahaan, nonprofit, komunitas atau kelompok riset |
| Legal entity | Subjek hukum yang diidentifikasi; keberadaan dan status review dinyatakan terpisah |
| Workspace | Konteks operasional yang memuat keanggotaan, pekerjaan privat dan kebijakan review |
| Customer | Pihak yang mengontrak produk yang disediakan; tidak otomatis memiliki inovasi |
| Marketplace | Katalog dan jaringan kolaborasi terpilih dengan aturan visibilitas eksplisit |
| Deployment | Instalasi berjalan dengan database, storage, identitas dan konfigurasinya sendiri |
| Tenant | Batas isolasi pelanggan hanya ketika model layanan mendefinisikannya secara eksplisit |

Gunakan PartyReference ketika diperlukan pemilik, pemohon, penerima atau pihak pengonfirmasi: tepat satu referensi PERSONAL_PARTY atau ORGANIZATION_PARTY. Pihak pribadi diarahkan ke akun/konteksnya yang berwenang; pihak organisasi melalui keanggotaan aktif dan capability yang diperlukan. Profil mitra, peluang, alamat penerima pitching, grant, koordinasi pertemuan dan konfirmasi kerja sama semuanya menerima union tersebut. Jangan mewajibkan organization id hanya untuk menyasar investor individu. LegalEntity merupakan referensi terpisah, diperlukan untuk subjek ekuitas aktual, bukan setiap pihak lawan.

Pencipta, pengelola, pihak yang mengaku memiliki hak dan pengambil keputusan berwenang merupakan konsep berbeda. Hak mengedit inovasi tidak membuktikan kepemilikan atau izin melisensikannya. Administrasi organisasi tidak memberikan kewenangan investasi milik penerima. Klaim hak dan kewenangan memiliki subjek, cakupan, sumber, tanggal pernyataan, status review dan pihak penanggung jawab. Pengungkapan publik dapat memengaruhi pelindungan dan kepemilikan bergantung konteks; aplikasi harus memberikan pratinjau publik yang disengaja tanpa menyatakan bahwa publikasi aman secara hukum. [FAQ transfer teknologi WIPO](https://www.wipo.int/en/web/technology-transfer/faq).

## 4. Aturan dasar untuk setiap komposisi

1. Pekerjaan dan dokumen privat ditolak aksesnya secara default. Setiap pembacaan, penulisan, pratinjau, proyeksi pencarian, input model, hasil job dan download diotorisasi di server.
2. Ringkasan terpublikasi tidak memberikan hak atas seluruh file pendukung. Berbagi satu versi terpilih tidak membagikan versi berikutnya atau seluruh portofolio.
3. Capability yang sudah ada, direncanakan dan diminta merupakan fakta berbeda. Rencana tidak memenuhi persyaratan fitur yang sudah tersedia.
4. Informasi dilaporkan sumber, dinyatakan sendiri, disediakan dan direview tetap mempertahankan labelnya. Upload dokumen tidak memverifikasi isinya.
5. Informasi hilang, bertentangan, kedaluwarsa atau belum direview sesuai kebutuhan menghasilkan UNKNOWN ketika relevan. Tidak diam-diam diartikan gagal, nol, tidak ada atau berhasil.
6. Eligibility, ranking, kesiapan pitching, cakupan bukti dan kekurangan komersialisasi tahap berikutnya merupakan keluaran terpisah.
7. Nominal hanya dibandingkan jika tujuan, subjek, mata uang, periode dan basisnya kompatibel. Dukungan proyek bukan ekuitas perusahaan atau harga lisensi.
8. Permintaan pendanaan perusahaan yang terkait beberapa inovasi tetap satu permintaan. Tidak menciptakan beberapa penggalangan atau hubungan kepemilikan.
9. Persetujuan pitching hanya mengizinkan diskusi. Usulan pertemuan bukan booking; waktu yang telah lewat bukan diskusi selesai.
10. Kerja sama atau perubahan materialnya memerlukan kedua perwakilan berwenang mengonfirmasi versi ringkasan dan batas usulan pengungkapan yang sama. Setiap pihak memilih subset persetujuannya sendiri; field publik efektif merupakan irisan keduanya yang dikurangi pembatasan pengungkapan aktif.
11. Retry tidak menggandakan tindakan penting. Keputusan lama tidak menimpa keadaan baru. Notifikasi tidak menentukan kebenaran bisnis.
12. Reuse sumber tidak membagikan data atau identitas antardeployment. Branding dan tombol tersembunyi bukan kontrol isolasi.

Aturan ini tetap berlaku ketika capability opsional, AI atau integrasi eksternal dimatikan. Semuanya merupakan syarat penerimaan, bukan bukti review keamanan telah selesai.

## 5. Kebutuhan fungsional

Setiap kebutuhan mempunyai tiga skenario penerimaan bernomor pada bagian 23. R1 mencakup seluruh kebutuhan kecuali paragrafnya secara eksplisit menyatakan komposisi opsional atau pengembangan berikutnya.

### FR01 — Akun dan onboarding

Tawarkan kedua persona dengan penjelasan sederhana: “Saya mempunyai inovasi dan mencari dukungan” serta “Saya berinvestasi atau memberi dukungan.” Kumpulkan nama tampilan, email, locale dan zona waktu; organisasi atau afiliasi hanya jika relevan. Badge verifikasi menyatakan persis apa yang diperiksa. Email terverifikasi tidak berarti dana, keahlian, dokumen identitas atau kepemilikan terverifikasi. Kegagalan autentikasi mempertahankan isian nonrahasia dan menyediakan pemulihan. Demo tertutup memakai akun terisolasi berlabel jelas dan dikecualikan dari metrik aktivitas nyata. Penerimaan: AC01–AC03.

### FR02 — Keanggotaan dan delegasi kewenangan

Workspace pribadi langsung tersedia. Undangan organisasi menyatakan capability, misalnya mengedit portofolio, mengirim pitching, mereview publikasi, memutuskan pitching masuk dan mengonfirmasi kerja sama. Undangan kedaluwarsa dan dapat dicabut. Server memeriksa keanggotaan aktif sekaligus izin objek tertentu. Penghapusan anggota menghentikan akses baru dan pekerjaan antrean yang memakai keanggotaan itu; catatan penulis historis tetap ada. UI menampilkan konteks perwakilan sebelum tindakan penting. Penerimaan: AC04–AC06.

### FR03 — Portofolio inovasi dan versi publikasi

Satu konteks pengelola dapat mempunyai banyak inovasi. Isian publikasi wajib adalah judul, ringkasan masalah dan solusi nonrahasia, pengguna sasaran, tahap saat ini, kemampuan saat ini serta konteks kontak/pengelola. Rincian dukungan diperlukan ketika membuka pengajuan, bukan untuk menyimpan draf. Panjang judul awal 5–120 karakter dan ringkasan singkat maksimal 350 karakter. Sektor, kata kunci dan gambar yang sesuai membantu penemuan; ilustrasi kategori menjadi fallback.

Gunakan editor empat langkah: dasar; yang sudah ada dan buktinya; dukungan serta lingkup keuangan; pratinjau publik. Simpan draf dengan status tersimpan/belum tersimpan/error yang terlihat. Terbitkan versi immutable, setelah review bila dikonfigurasi. Edit material menghasilkan draf penerus sementara versi publik saat ini tetap tersedia hingga penggantinya disetujui. Arsip menghilangkan penemuan dan pengajuan baru, mempertahankan riwayat berizin dan tidak membatalkan diskusi yang berjalan. Penerimaan: AC07–AC09.

### FR04 — Klaim hak dan pengungkapan yang disengaja

Catat pencipta, kontributor, pengelola, pihak yang menyatakan hak serta kewenangan berdiskusi atau melisensikan secara terpisah. Terima status “belum ditetapkan” secara eksplisit beserta referensi pendukung. Jangan mewajibkan paten atau perusahaan untuk menerbitkan ringkasan nonrahasia. Target dapat meminta bukti tertentu pada tahap tertentu dengan alasan terlihat oleh pemohon. Sebelum publikasi atau berbagi, tampilkan field publik, penerima dan bukti privat terpilih. Pencatatan pernyataan kerahasiaan tidak boleh disebut NDA yang telah ditandatangani. Jenis dan lingkup perjanjian berbeda; model perjanjian memerlukan penyesuaian konteks. [Panduan perjanjian WIPO](https://www.wipo.int/en/web/technology-transfer/agreements). Penerimaan: AC10–AC12.

### FR05 — Dokumen, ekstraksi dan review bukti

Dukung gambar, PDF/DOCX dan tautan aman pada R1. Dokumen default PRIVATE. Status ketersediaan/keamanan file adalah CREATED, UPLOADING, QUARANTINED, AVAILABLE dan REJECTED. Ekstraksi mempunyai status terpisah: NOT_REQUESTED, PENDING, RUNNING, SUCCEEDED, FAILED atau NEEDS_MANUAL_INPUT. Transfer jaringan selesai belum menjadikan file bukti tersedia sampai pemeriksaan keamanan/format berhasil. Sesudahnya, scan berizin dapat berstatus AVAILABLE dan memenuhi DOCUMENT_PRESENT walau ekstraksi memerlukan input manual; kriteria isi hasil ekstraksi tetap UNKNOWN. Batas usulan 20 MB per PDF/DOCX dan 5 MB per gambar ditampilkan sebelum pemilihan; video memakai tautan HTTPS yang diizinkan. Transfer terputus mempertahankan draf dan menawarkan retry.

Metadata mencakup tipe, penerbit yang dinyatakan, subjek/cakupan, tanggal, kedaluwarsa, sumber, checksum, versi dan grant akses. Ekstraksi mengusulkan fakta dengan versi dokumen serta lokasi halaman/paragraf. Pengguna mengonfirmasinya; konflik perlu klarifikasi. Scan tanpa OCR yang didukung tetap tersedia sesudah pemeriksaan keamanan untuk review manual berizin, tetapi tidak menghasilkan isi ekstraksi rekaan. Ketersediaan file, ekstraksi dan status review bukti tidak boleh saling menimpa. Status review mencakup PROVIDED_UNREVIEWED, REVIEWED_SUPPORTED, REVIEWED_UNSUPPORTED, NEEDS_CLARIFICATION, EXPIRED dan SUPERSEDED, dengan reviewer serta cakupannya. Penerimaan: AC13–AC15.

### FR06 — Permintaan dukungan dan anggaran proyek

Inovasi dapat mempunyai beberapa SupportRequests untuk hasil berbeda, seperti pilot validasi, bantuan manufaktur atau diskusi lisensi. Masing-masing menunjuk versi inovasi terpilih, dukungan yang dicari, bentuk kerja sama, lingkup, waktu, wilayah dan penerimaan dukungan parsial atau nonuang. Satu permintaan spesifik dipilih ketika pitching. Kategori dukungan menjelaskan sumber daya; PROJECT, LICENSE dan EQUITY menjelaskan catatan hubungan. Keduanya tidak boleh disimpulkan satu dari yang lain.

ProjectBudget memuat minimum/maksimum decimal, mata uang, lingkup, periode, tanggal estimasi dan asumsi. Minimum tidak boleh negatif dan maksimum setidaknya minimum. Belum diketahui disimpan null dengan tampilan “Belum ditentukan.” Kebutuhan uang nol hanya diperbolehkan untuk lingkup nonfinansial yang dinyatakan jelas. Rincian opsional menghitung secara deterministik dari jumlah × biaya unit; selisih memerlukan penjelasan, misalnya lingkup parsial. Total hasil ekstraksi spreadsheet/PDF tetap draf sampai dikonfirmasi. Penerimaan: AC16–AC18.

### FR07 — Permintaan pendanaan perusahaan

FundingRequest mewakili satu penggalangan perusahaan atau venture yang diusulkan, terpisah dari biaya proyek inovasi. Data mencakup PartyReference pemilik, tipe subjek EXISTING_ENTITY atau PROPOSED_ENTITY, entitas yang diidentifikasi jika ada, tahap pembiayaan perusahaan, bentuk pembiayaan, total target, mata uang, penggunaan, waktu, preferensi pendanaan parsial/sindikasi dan kisaran kontribusi yang diharapkan bila tersedia. Tahap pembiayaan perusahaan dan kematangan teknologi/produk setiap inovasi merupakan dimensi independen; perusahaan dengan pendapatan awal dapat mempunyai inovasi prototipe. Venture usulan berlabel “perusahaan belum dibentuk”; tidak boleh meniru entitas hukum yang sudah ada. Kaitkan nol atau lebih inovasi yang dikelola; ketika inovasi dipakai sebagai bukti pitching, pilih versi dan grant secara eksplisit.

Tampilkan satu kartu FundingRequest dengan inovasi terkait. Target pendanaan USD500,000 dan check investor USD50,000–100,000 berbeda basis, bukan bukti ketidakcocokan anggaran. Bandingkan kisaran kontribusi yang diharapkan jika dinyatakan; jika belum ada, minta klarifikasi kontribusi dan sindikasi. Komitmen atau dana diterima tidak disimpulkan dari status pitching. Catatan EQUITY terkonfirmasi memerlukan entitas hukum nyata yang diidentifikasi dan kewenangan kedua pihak. Penerimaan: AC19–AC21.

### FR08 — Profil investor dan mitra

Mitra menyatakan subtipe, sektor/masalah minat, tahap yang diterima, wilayah, dukungan, bentuk kerja sama/pembiayaan, kisaran check atau dukungan proyek yang relevan, ekspektasi review, jalur pengajuan dan tanggal penerimaan aktif. Investor individu tidak memerlukan organisasi rekaan. Profil membedakan tesis umum dari ketersediaan saat ini, serta data direktori dilaporkan sumber dari penerimaan yang dikonfirmasi pemilik. Tampilkan ketersediaan lama atau belum dikonfirmasi dengan jujur. Jangan mengarang aset kelolaan, kapasitas investasi atau kredensial. Preferensi kontak menentukan apakah aplikasi menawarkan pitching internal, jalur eksternal atau tidak menerima pendekatan baru. Penerimaan: AC22–AC24.

### FR09 — Peluang, mandat dan penerimaan langsung

Mitra dapat menerbitkan beberapa peluang atau mandat berversi, masing-masing dengan hasil jelas, cakupan masuk/keluar, dukungan yang disediakan, tahap diterima, waktu, basis keuangan dan persyaratan bertipe. Gunakan DRAFT, ACTIVE, PAUSED, CLOSED dan EXPIRED. Pemohon dapat membaca semua persyaratan yang dapat menghalangi pengajuannya. Kriteria naratif tetap menjadi pertanyaan review sampai memiliki pemetaan bertipe yang disetujui. Tidak ada kriteria rahasia yang otomatis menolak pitching.

Peluang spesifik aktif menjadi target. Profil penerimaan umum berversi hanya boleh dipakai bila pitching langsung diaktifkan, dengan label “berdasarkan profil umum mitra.” Jangan menggabungkan persyaratan menguntungkan dari satu mandat dan sumber daya dari mandat lain. Klik jalur aplikasi eksternal dicatat sebagai pengalihan eksternal, bukan pitching terkirim atau disetujui di aplikasi. Penerimaan: AC25–AC27.

### FR10 — Jelajahi, pencarian dan daftar tersimpan

Sediakan saran relevan berdasarkan preferensi eksplisit atau kebutuhan aktif, pilihan kurator dan inovasi baru terpublikasi. Mitra dapat menjelajahi inovasi atau permintaan pendanaan sebagai jenis hasil terpisah; inovator menjelajahi target investor/mitra yang sesuai. Filter meliputi sektor, tahap, tujuan, bentuk dukungan, lokasi, kisaran keuangan yang sebanding dan penerimaan saat ini. Pencarian menerima Indonesia dan Inggris. Hasil kosong menjelaskan filter dan menawarkan pelonggaran yang disengaja; produk tidak diam-diam memperluas persyaratan wajib.

Kartu mengutamakan masalah, solusi yang ada, dukungan yang diminta, tahap dan beberapa alasan. Simpan dan feedback “kurang sesuai” memengaruhi daftar pribadi, bukan reputasi publik. Label tren tidak muncul dari event demo atau aktivitas yang belum memadai. Usulan trending memerlukan sedikitnya lima pelaku mitra independen yang memenuhi syarat dalam jendela 14 hari, dengan event sendiri/bot dikeluarkan dan batas per pelaku; kemampuan ini opsional dan terpisah dari kecocokan. Penerimaan: AC28–AC30.

### FR11 — Matching yang dapat dijelaskan dan hasil persyaratan

Engine menilai permintaan/versi sumber terpilih terhadap satu versi peluang atau penerimaan umum dalam konteks berizin. Pertahankan tujuan sumber/target, izin bukti dan basis keuangan. Keluarkan eligibility, kesiapan khusus target, batas skor/coverage, jumlah bukti tersedia/direview, alasan, kekurangan dan tindakan berikutnya. Persyaratan wajib yang diketahui gagal tidak dapat dikompensasi kemiripan semantik. Tampilkan “Perlu konfirmasi” ketika fakta wajib UNKNOWN dan jangan masukkan pasangan INCOMPATIBLE ke shortlist positif. Rincian ranking berada di aksi sekunder. Penerimaan: AC31–AC33.

### FR12 — Preflight dan brief yang dapat diedit

Sebelum pengajuan, tampilkan penerima, versi permintaan dan inovasi/pendanaan yang tepat, tujuan, persyaratan, file yang dibagikan, lingkup anggaran/pendanaan dan brief ringkas yang dapat diedit. Token preflight merujuk versi, konfigurasi dan konteks izin tersebut. Periksa kembali saat pengiriman; perubahan memerlukan preflight baru. READY_TO_SUBMIT, NEEDS_INFORMATION dan BLOCKED_FOR_THIS_TARGET merupakan keluaran berbeda.

Template brief deterministik memuat masalah, solusi saat ini, bukti/tahap, dukungan yang diminta, relevansi, subjek/basis keuangan, pekerjaan tersisa, tim dan sumber kewenangan. AI opsional dapat merangkum fakta yang diberikan, tetapi tidak menambah klaim, mengirim, menerbitkan atau mengesahkan. Klaim kuantitatif tanpa dukungan ditolak atau ditandai untuk dikoreksi. Tampilan HTML siap cetak serta ekspor teks/Markdown mengikuti izin sumber saat ini. Penerimaan: AC34–AC36.

### FR13 — Pengiriman pitching yang disengaja

Pitch menyasar satu penerima dan versi peluang atau penerimaan umum. Subjeknya satu SupportRequest atau satu FundingRequest, bukan keduanya tersembunyi dalam permintaan yang sama. Pitching pendanaan dapat merujuk beberapa versi inovasi tanpa menghasilkan penggalangan tambahan. PitchSubmission membekukan versi permintaan, brief, referensi dokumen terpilih, fakta yang dinyatakan dan metadata izin. Lindungi informasi rahasia di dalam snapshot; riwayat immutable bukan grant pengambilan permanen.

Pengguna secara eksplisit mengirim sesudah preflight. Cakupan subjek–penerima–target mengizinkan paling banyak satu pitching aktif untuk tujuan sama. Key retry mengembalikan hasil semula. Batas awal usulan lima pitching baru per pelaku per hari, dapat dikonfigurasi dan dijelaskan. Diskusi lama tetap terbaca pihak berwenang ketika penerimaan ditutup; pengajuan baru berhenti. Penerimaan: AC37–AC39.

### FR14 — Keputusan penerima

Penerima berwenang memilih “Setujui untuk diskusi,” “Minta revisi,” atau “Tolak.” Persetujuan hanya membuka penjadwalan diskusi. Penolakan memerlukan alasan privat singkat; tidak menurunkan reputasi publik. Mulai mereview adalah status antara, bukan keputusan. Keputusan merujuk versi pengajuan dan expected version Pitch. Hanya satu keputusan bersamaan yang valid dapat commit. Tidak ada respons tidak pernah berarti persetujuan otomatis. Penarikan menghentikan keputusan berikutnya pada pengajuan aktif itu. Penerimaan: AC40–AC42.

### FR15 — Putaran revisi per item

Setiap putaran berisi satu atau lebih permintaan item dengan kategori, pertanyaan, alasan, bukti yang diminta, wajib/opsional dan tenggat opsional. Jawaban mencakup teks, lampiran terpilih dan “Dapat dipenuhi,” “Perlu diskusi,” atau “Belum dapat dipenuhi.” Seluruh item wajib perlu jawaban sebelum resubmit; ketidakmampuan yang disampaikan jujur merupakan jawaban, bukan persetujuan. Penerima menerima atau meminta rincian tambahan untuk setiap item.

Putaran dan jawaban berversi serta disimpan. Fitur baru yang diminta tetap PLANNED sampai bukti aktual berubah. Resubmit secara sadar memilih versi sumber dan file berbagi yang berubah; tidak mengganti snapshot lama atau mengubah persyaratan global peluang secara diam-diam. Perubahan material dapat memerlukan persetujuan ulang workspace opsional. Penerimaan: AC43–AC45.

### FR16 — Diskusi bersama, tugas dan notifikasi

Satu ruang pitching menampilkan ringkasan, revisi, dokumen, diskusi, jadwal dan linimasa. Tampilkan “Menunggu Anda” serta “Menunggu pihak lain,” dengan tindakan berikutnya langsung. R1 menggunakan pesan berutas dan polling; transport realtime tidak diperlukan. Tugas memiliki penanggung jawab, tenggat, status dan referensi ke permintaan atau kekurangan bukti terkait. Peserta mencatat hasil pertemuan serta langkah berikutnya secara eksplisit. Slot yang waktunya lewat tidak membuktikan kehadiran.

Notifikasi dalam aplikasi mencakup pengajuan, keputusan, revisi, jadwal dan konfirmasi. Pengiriman email opsional mempunyai preferensi serta retry yang terpisah dari perubahan state. Perubahan domain, event audit dan niat notifikasi di-commit atomik melalui outbox; konsumen melakukan deduplikasi event/penerima/channel. Kegagalan pengiriman tidak mengulang keputusan bisnis. Penerimaan: AC46–AC48.

### FR17 — Negosiasi pertemuan

Setelah persetujuan, koordinator berwenang dari salah satu pihak dapat mengusulkan 2–5 slot, durasi 30 atau 60 menit, zona waktu IANA, agenda dan tautan rapat HTTPS opsional. UI menunjukkan pengusul dan giliran siapa. Pihak lain memilih slot atau mengirim 2–5 alternatif. Memilih slot di UI merupakan pilihan draf; penerimaan eksplisit dan booking server yang berhasil baru mengonfirmasinya.

Simpan instant UTC dan tampilkan zona masing-masing pengguna. Usulan kedaluwarsa setelah default usulan 72 jam atau ketika semua slot telah lewat. Usulan bukan reservasi eksklusif. Menerima slot memeriksa dan memesan seluruh peserta wajib secara atomik. Konflik tetap dapat dipulihkan. Usulan pengganti tidak menghapus pertemuan terkonfirmasi sampai penggantinya berhasil atau pembatalan eksplisit dilakukan. Jadwal terkonfirmasi menyediakan ICS; free/busy eksternal belum diketahui tanpa adapter kalender yang benar-benar disediakan. Penerimaan: AC49–AC51.

### FR18 — Usulan dan konfirmasi kerja sama

Kerja sama merupakan catatan terpisah dengan tipe PROJECT, LICENSE atau EQUITY, pihak terkait, lingkup, tanggal, status, referensi entitas bila relevan, bukti rahasia dan pilihan field publik. PROJECT dapat menjelaskan dukungan, co-development, validasi, manufaktur atau distribusi. LICENSE menjelaskan hak yang dinyatakan, penggunaan diizinkan, wilayah dan periode bila diketahui; bukan pengalihan kepemilikan. EQUITY menunjuk perusahaan/entitas nyata; persentase opsional, bertanggal dan tidak pernah diturunkan dari jumlah investasi.

Kedua perwakilan berwenang mengonfirmasi versi ringkasan dan batas field publik yang sama, sambil memilih sendiri field dalam batas tersebut yang boleh diungkapkan. Pilihannya tidak harus identik; hanya irisan keduanya yang dapat publik. Perubahan material ringkasan, perluasan batas field atau usulan perluasan pengungkapan yang sebelumnya dikonfirmasi memerlukan versi/putaran konfirmasi baru. Pembatasan atau pencabutan pengungkapan langsung menyembunyikan field melalui event pembatasan yang dapat diaudit tanpa menghapus riwayat konfirmasi. Setiap pihak dapat meminta koreksi atau menolak. Pernyataan sepihak dapat tetap menjadi draf privat atau klaim dilaporkan sumber, tetapi tidak memakai badge dikonfirmasi bersama. Review bukti dan konfirmasi kedua pihak berlabel berbeda. Aplikasi mencatat ringkasan, bukan melaksanakan pengalihan hak atau penerbitan saham. Penerimaan: AC52–AC54.

### FR19 — Profil publik dan transparansi kerja sama

Profil publik hanya menampilkan field yang sengaja diterbitkan dan versi publikasi saat ini. Pisahkan pencipta, pengelola, pemilik hak yang dinyatakan, mitra proyek, pemegang lisensi dan investor pada entitas bernama. Kerja sama terkonfirmasi hanya menerbitkan irisan field pilihan kedua pihak dalam batas usulan versi tersebut, dikurangi pembatasan aktif berikutnya. Nominal pendanaan default privat. Persentase ekuitas opsional memerlukan izin eksplisit, referensi perusahaan dan tanggal berlaku. Pencabutan atau pembatasan langsung berlaku pada pembacaan publik baru; perluasan publikasi membutuhkan konfirmasi baru. Permintaan review kerja sama dapat menyembunyikan klaim publik yang disengketakan sambil mempertahankan riwayat berizin. Penerimaan: AC55–AC57.

### FR20 — Review organisasi opsional

Capability organization_review menambahkan gerbang publikasi dan/atau pengajuan yang dikonfigurasi untuk workspace. Opsional bagi inovator pribadi dan nonaktif pada komposisi generik default. Kebijakan review merujuk checklist berversi dan reviewer berwenang, dengan lingkup serta alasan terlihat. Reviewer tidak membuat keputusan mitra atau mengesahkan field di luar tugasnya. Persetujuan terikat versi yang direview; hanya perubahan material yang ditetapkan kebijakan memerlukan persetujuan ulang. Menonaktifkan capability tidak boleh meninggalkan item tertunda: migrasi berwenang menyelesaikan atau memindahkan setiap item sebelum konfigurasi baru diaktifkan. Penerimaan: AC58–AC60.

### FR21 — Impor, ekspor dan integrasi

R1 mendukung impor/ekspor JSON tervalidasi dengan versi schema, external system/id, provenance dan pratinjau sebelum apply. Impor dua kali melakukan upsert berdasarkan external system ditambah external id di dalam konteks pengelola. Impor tidak menimpa fakta direview secara diam-diam, menggabungkan organisasi hanya berdasarkan nama atau menaikkan hubungan dilaporkan sumber menjadi dikonfirmasi bersama. Field privat membutuhkan pemetaan berwenang yang eksplisit. Ekspor, pembuatan dalam antrean dan hasil download memeriksa ulang grant saat ini. Alat eksternal tidak mendapat izin hanya karena mapping memuat workspace id. Penerimaan: AC61–AC63.

### FR22 — Moderasi, privasi dan retensi

Pengguna dapat melaporkan dugaan penyamaran, klaim tanpa dukungan, kontak tidak diinginkan atau konten abusif dengan alasan privat dan objek terkait. Operator memakai antrean terbatas dan tindakan tercatat; tidak dapat menelusuri seluruh file rahasia tanpa tujuan operasional terdokumentasi. Suspensi mencegah tindakan baru dan menghilangkan penemuan publik yang terdampak, sambil mempertahankan penanganan kasus berjalan yang diizinkan.

Sebelum pilot nyata, terbitkan masa retensi, penanganan permintaan penghapusan, pengecualian audit/legal hold, kedaluwarsa backup dan tanggung jawab operator. Analitik default tidak memuat isi pesan/file. Percakapan atau bukti privat tidak digunakan untuk pelatihan model secara default. Pencabutan grant menghalangi pengambilan sumber dan keluaran turunannya berikutnya; tidak dapat menarik kembali salinan yang telah didownload. Permintaan penghapusan harus melaporkan apa yang dihapus, dipertahankan dan alasannya, bukan menjanjikan penghapusan seketika yang mustahil dari penerima atau backup. Penerimaan: AC64–AC66.

### FR23 — Komposisi produk dan adapter

Komposisi yang didukung menunjuk rilis sumber, schema/versi konfigurasi, brand/locale, capability teruji yang aktif, taksonomi/checklist terkelola dan versi adapter bernama. Tolak kombinasi tidak valid sebelum melayani trafik. Visibilitas capability dan ketersediaan mutasi harus konsisten di server serta client. Konfigurasi tidak boleh mematikan aturan dasar bagian 4. Kebutuhan klien baru diklasifikasikan sebagai data/konfigurasi, capability berulang, adapter konkret atau produk terpisah; bukan pemeriksaan nama klien yang tersebar. Penerimaan: AC67–AC69.

### FR24 — Rilis, operasi dan pemulihan

Pelihara satu riwayat sumber dan rilis reproducible untuk varian terkait. Setiap environment mencatat versi kode, konfigurasi, capability, adapter dan schema database. Perbaikan bersama diimplementasikan serta diuji regresi sekali, lalu sengaja di-rollout ke setiap komposisi yang didukung. Gunakan perubahan schema expand/migrate/contract yang kompatibel ke depan, backup/restore teruji serta rencana rollback atau forward repair untuk deployment terkait. Menerbitkan rilis tidak otomatis memperbarui semua deployment. Operasi harus membedakan kegagalan pengiriman parsial dari niat bisnis yang sudah commit. Penerimaan: AC70–AC72.

## 6. Model inti dan batas kepemilikan

Record berikut bersifat konseptual, bukan kewajiban membangun service atau tabel untuk setiap baris. Penyimpanan boleh digabung selama kepemilikan, semantik versi dan akses tetap dapat diuji. Identifier bersifat opaque dan tidak menggantikan otorisasi.

| Record | Semantik wajib |
|---|---|
| Account, Profile | Preferensi persona, status kontak terverifikasi, locale, zona waktu dan status akun |
| Organization, LegalEntity | Pelaku organisasi versus subjek hukum teridentifikasi; sumber dan status review |
| Workspace, Membership | Konteks pribadi/organisasi; keanggotaan aktif dan capability eksplisit |
| Invention, InventionVersion | Identitas stabil; versi draf/publik; tahap dan isi nonrahasia |
| Contribution, RightsClaim, AuthorityClaim | Pencipta, pengelola, pengaku hak dan pihak yang dapat bertindak; cakupan dan bukti |
| EvidenceFact, EvidenceReview | Nilai/unit, current/planned, sumber/lokasi dan cakupan/versi review |
| Document, DocumentVersion | Bytes/checksum/storage key immutable; status keamanan/ketersediaan dan ekstraksi independen; review bukti terpisah |
| AccessGrant | Resource/versi bernama, pelaku/konteks berizin, tujuan, awal, kedaluwarsa dan pencabutan |
| SupportRequest, ProjectBudget | Hasil serta sumber daya inovasi; basis/versi keuangan khusus proyek |
| FundingRequest | Satu penggalangan venture/perusahaan; subjek/entitas, target putaran, preferensi kontribusi dan status |
| FundingInventionLink | Keterkaitan pendukung berversi; bukan duplikasi pendanaan atau saham |
| PartnerProfile, OpportunityVersion | Penerimaan umum versus mandat spesifik; status dan jalur kontak saat ini |
| Requirement | Aturan bertipe, wajib, tahap, mode verifikasi, sumber, visibilitas dan versi |
| MatchRun, MatchResult | Versi input/konteks akses, versi engine/aturan/model, fitur/hasil/alasan |
| Pitch, PitchSubmission, Decision | Target dan subjek, metadata pengajuan immutable, keputusan pada versi tepat |
| RevisionRound, RevisionItem | Pertanyaan wajib, jawaban, file terpilih, pelaku dan riwayat review |
| Message, Task | Diskusi dalam cakupan pitching dan tindakan berikutnya yang ditugaskan |
| ScheduleProposal, Slot, Meeting, Booking | Putaran negosiasi, rentang UTC, status dan reservasi peserta atomik |
| Partnership, PartnershipVersion, Confirmation | Tipe, PartyReferences, versi ringkasan/batas pengungkapan, subset persetujuan per pihak dan keputusan; event pembatasan pengungkapan append-only |
| AuditEvent, OutboxEvent, Notification | Niat yang commit, transisi yang dapat diatribusikan dan percobaan pengiriman |
| ImportRun, ExternalReference, Job | Provenance preview/apply, identitas eksternal unik dan hasil async berizin |

Invention memiliki tepat satu konteks pengelola yang bertanggung jawab pada R1, dengan kontributor dari konteks lain diizinkan. Pengalihan memerlukan kewenangan sumber dan tujuan serta audit; bukan edit nama. FundingRequest memiliki target penggalangannya; link tidak boleh menyalin nominal ke setiap inovasi. Subjek Pitch memakai discriminator SUPPORT_REQUEST atau FUNDING_REQUEST dengan tepat satu referensi subjek. Nilai bisnis memakai tipe decimal dan identifier mata uang, bukan floating point. Timestamp menggunakan UTC dengan zona IANA untuk tampilan; tanggal kalender berlaku memakai tipe date.

Pengajuan berversi merujuk fakta dan versi file beserta izin saat berbagi. Pengambilan yang dilihat peserta tetap mengevaluasi grant saat ini. Audit terbatas dapat mempertahankan fakta bahwa dokumen disertakan tanpa membuka bytes atau teks rahasia turunannya sesudah pencabutan. Menghapus atau mengoreksi profil saat ini tidak boleh diam-diam menulis ulang konteks keputusan historis.

## 7. Status dan transisi valid

Status publikasi adalah DRAFT → PENDING_REVIEW jika dikonfigurasi → PUBLISHED → ARCHIVED. Review yang dikembalikan menuju DRAFT dengan alasan. Publikasi ulang versi berubah memperbarui pointer publik hanya setelah review wajib. SupportRequest, FundingRequest dan Opportunity menggunakan DRAFT → ACTIVE ↔ PAUSED → CLOSED, serta EXPIRED ketika deadline yang dikonfigurasi terlewati. Penutupan menghentikan pitching baru tanpa mengarang hasil pitching lama.

| Status Pitch | Tindakan dan pelaku berwenang | Hasil |
|---|---|---|
| DRAFT | Kirim oleh inovator berwenang setelah preflight baru | SUBMITTED atau PENDING_WORKSPACE_REVIEW |
| PENDING_WORKSPACE_REVIEW | Reviewer menyetujui versi tepat dalam antrean | SUBMITTED |
| PENDING_WORKSPACE_REVIEW | Reviewer mengembalikan dengan alasan | Asal DRAFT atau REVISION_REQUESTED sebelumnya |
| SUBMITTED | Penerima mulai review | UNDER_REVIEW |
| SUBMITTED / UNDER_REVIEW | Penerima meminta revisi per item | REVISION_REQUESTED |
| REVISION_REQUESTED | Inovator resubmit setelah semua item wajib dijawab | SUBMITTED atau PENDING_WORKSPACE_REVIEW |
| SUBMITTED / UNDER_REVIEW | Penerima menyetujui diskusi | APPROVED_FOR_DISCUSSION |
| SUBMITTED / UNDER_REVIEW | Penerima menolak dengan alasan | REJECTED |
| Nonterminal sebelum keputusan akhir | Inovator menarik | WITHDRAWN |
| APPROVED_FOR_DISCUSSION | Pihak berwenang menutup diskusi dengan alasan | CLOSED |

Simpan asal review dan versi sumber dalam antrean. Pengajuan ditolak atau ditarik tidak dibuka kembali hanya dengan mengedit profil. Pitching baru yang sebenarnya membutuhkan izin penerima atau kebijakan resubmit yang dapat dikonfigurasi, dengan awal jeda tujuh hari ditambah perubahan material. Sesudah persetujuan diskusi, klarifikasi tambahan menggunakan tugas; tidak menghapus riwayat persetujuan. Status jadwal dan kerja sama independen sehingga label pipeline merupakan proyeksi, bukan enum tunggal yang menghilangkan riwayat.

Status ScheduleProposal adalah OPEN, ACCEPTED, SUPERSEDED, EXPIRED dan CANCELLED. Usulan balik menggantikan putaran terbuka sebelumnya. Status Meeting adalah CONFIRMED, COMPLETED, CANCELLED dan NO_SHOW_REPORTED. Penyelesaian memerlukan catatan hasil peserta; ketidaksepakatan tetap terlihat. Penerimaan reschedule mengganti booking lama/baru dalam satu transaksi. Pembatalan usulan tidak membatalkan pertemuan lama kecuali pengguna memilih tindakan terpisah itu secara eksplisit.

PartnershipVersion bergerak DRAFT → PENDING_COUNTERPARTY → CONFIRMED, dengan alternatif CHANGES_REQUESTED atau DECLINED. Pengirim pertama mengonfirmasi ringkasan dan batas usulan pengungkapan; pihak lain mengonfirmasi checksum/versi sama, tetapi dapat memilih subset field berbeda. Field publik efektif adalah irisan subset kedua pihak yang dikurangi pembatasan aktif. Perubahan material ringkasan atau perluasan pengungkapan membuat versi/putaran baru tanpa mewarisi konfirmasi. Event pembatasan append-only dapat langsung mempersempit atau mencabut pengungkapan saat ini tanpa menulis ulang riwayat konfirmasi. Publikasi merupakan proyeksi berizin terpisah dari versi terkonfirmasi dan pembatasan saat ini. Hubungan yang berakhir tetap menyimpan tanggal dan riwayat; hilang dari profil publik tidak berarti catatan privat dihapus.

## 8. Kontrak otorisasi dan kerahasiaan

| Operasi | Pengelola inovasi | Pengambil keputusan penerima | Reviewer yang ditugaskan | Operator |
|---|---|---|---|---|
| Membaca katalog nonrahasia terpublikasi | Ya | Ya | Ya | Ya |
| Mengedit inovasi/permintaan sumber | Jika memiliki capability edit sesuai cakupan | Tidak | Hanya izin edit eksplisit | Tidak untuk akses rutin |
| Melihat dokumen privat | Grant pemilik/anggota | Hanya grant aktif terpilih | Hanya cakupan tugas | Grant kasus spesifik terdokumentasi |
| Submit/resubmit pitching | Capability submit sesuai cakupan | Tidak | Hanya menyetujui gerbang workspace | Tidak |
| Memutuskan pitching | Tidak | Capability penerima sesuai cakupan | Tidak | Tidak |
| Menerima jadwal | Peserta/koordinator bernama | Peserta/koordinator bernama | Hanya peserta yang diberi izin | Tidak |
| Mengonfirmasi kerja sama | Perwakilan pihak berwenang | Perwakilan pihak berwenang | Hanya bila mewakili pihak | Tidak |
| Moderasi listing publik | Tidak, dapat melaporkan | Tidak, dapat melaporkan | Tidak | Capability moderasi sesuai cakupan |

Otorisasi deny-by-default dan diperiksa pada setiap request, termasuk penyampaian resource statis. Pencarian memakai proyeksi yang sengaja publik atau memang diizinkan; bukti teknis privat tidak masuk indeks publik global. Cache bukan sumber kewenangan. Key cache memuat versi sumber/target, konteks penonton/akses dan generasi izin; perubahan grant membatalkan keluaran bergantung. Worker membangun kembali otorisasi pelaku/resource sebelum memproses dan sebelum merilis hasil. [Panduan otorisasi OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [panduan multi-tenant OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html).

Brief buatan sistem harus mempertahankan referensi dependency fakta/dokumen. Bila akses dependency rahasia dicabut, tolak artifact terlindungi atau sajikan proyeksi teredaksi berlabel jelas; jangan diam-diam mengubah pengajuan asli atau menyajikan cache lama. Metadata keputusan privat suatu pihak dapat dipertahankan menurut kebijakan retensi tersendiri yang beralasan. Materi yang sebelumnya didownload tidak dapat ditarik kembali secara teknis. R1 memakai gateway download terlindungi yang mengotorisasi ulang setiap fetch baru, termasuk range request, sebelum mengembalikan bytes terlindungi; tidak memberikan URL object storage langsung yang terlihat client. Karena itu pencabutan menghalangi request pengambilan baru, tetapi tidak menarik kembali bytes yang sudah dikirim atau respons yang sedang berjalan. Adapter direct signed URL di masa depan wajib menjelaskan umur maksimum URL yang masih aktif dan jendela pencabutannya, serta merevisi jaminan terkait, bukan menganggap URL terbit dapat langsung ditarik kembali.

Validasi ekstensi file, media type sebenarnya, signature, ukuran dan batas parsing; buat storage key aman dan karantina konten baru. Jangan menjalankan macro dokumen atau embed HTML bebas. Scan memakai processor yang disetujui tanpa mengungkapkan bahan rahasia ke layanan publik yang tidak disetujui. Impor URL tidak boleh mengambil alamat internal tanpa pembatasan. Konteks model hanya berasal dari fakta berizin. Instruksi hasil retrieval diperlakukan sebagai data tidak tepercaya; referensi output terstruktur harus terhubung ke fakta yang diberikan. Satu retry terkendali boleh memperbaiki output tidak valid, kemudian gunakan fallback deterministik. Kontrol ini mengikuti panduan OWASP terkait dan tetap membutuhkan threat modeling implementasi. [Upload file](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [pencegahan prompt injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

## 9. Unit matching, aturan bertipe dan makna tahap

Unit matching adalah versi permintaan sumber + versi inovasi pendukung + versi peluang/penerimaan target + tujuan terpilih + basis keuangan + konteks penonton berizin. FundingRequest tetap menjadi subjek sumber walaupun didukung dua inovasi. Kandidat spesifik peluang tetap terpisah sebelum dikelompokkan per mitra.

Requirement memuat field, operator, nilai, unit/basis bila relevan, wajib/preferensi, applies_at, verification_mode, sumber, reviewer penanggung jawab, visibilitas dan versi. Operator yang didukung adalah equals, in_set, intersects, minimum, maximum, range_overlap, exists dan manual_review. R1 mengimplementasikan kode bertipe yang terbatas; administrator tidak dapat mengunggah ekspresi bebas. Nilai tahap adalah SUBMISSION, DISCUSSION, PILOT dan COMMERCIALIZATION. Mode verifikasi adalah DECLARATION, DOCUMENT_PRESENT dan REVIEWER_CONFIRMED.

PASS membutuhkan bukti berizin yang cukup dan sebanding. FAIL membutuhkan bukti cukup yang menyangkal kriteria. UNKNOWN berarti informasi hilang, konflik, lama, tidak sebanding atau belum direview sesuai kebutuhan. NOT_APPLICABLE memerlukan alasan eksplisit. Persyaratan CURRENT yang diketahui tidak dipenuhi fakta PLANNED. Persyaratan naratif tanpa pemetaan disetujui menghasilkan UNKNOWN/review manual, bukan dugaan kepatuhan.

Evaluasi hard constraints untuk tahap masuk peluang terlebih dahulu. Regulasi yang dibutuhkan sebelum komersialisasi tidak otomatis menghalangi pitching co-development prototipe. Jika penerima hanya menerima solusi siap pasar, kriteria itu harus ditulis sebagai aturan tahap pengajuan. Penerima dapat mencatat pengecualian berwenang terhadap kriterianya sendiri; tidak dapat mengabaikan otorisasi platform atau kewenangan pihak lain.

Keluarkan eligibility ELIGIBLE, NEEDS_VERIFICATION atau INCOMPATIBLE terpisah dari kesiapan pitching READY_TO_SUBMIT, NEEDS_INFORMATION atau BLOCKED_FOR_THIS_TARGET. Laporkan bukti tersedia/direview sebagai jumlah terhadap persyaratan berlaku, bukan persentase kesiapan universal. Bila tidak ada checklist, tampilkan “Belum ada checklist.” Skala kematangan opsional, dengan identitas skala/versi serta sumber; tidak dihitung dari jumlah dokumen.

## 10. Retrieval kandidat dan ranking konservatif

Untuk katalog kecil, evaluasi semua kandidat aktif berizin dan jelaskan pengecualian. Mulai dari baseline lexical ditambah aturan terstruktur. Mode hybrid opsional memakai BM25 sebenarnya dan representasi dense multilingual ternormalisasi, menggabungkan rank melalui Reciprocal Rank Fusion, kemudian rerank kandidat terbatas bila manfaat terukur membenarkannya. RRF menggabungkan rank, bukan skor lexical dan cosine mentah; retrieve-and-rerank merupakan pola mapan, tetapi manfaat lokalnya tetap perlu benchmark. [Paper RRF asli](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf), [retrieve and rerank Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html).

Default hybrid usulan: hingga 50 hasil lexical dan 50 dense, konstanta RRF k=60 dengan rank mulai satu, rerank maksimal 30 kandidat gabungan dan tampilkan hingga lima kecocokan halaman awal. Retriever memberi kontribusi nol untuk kandidat yang tidak diambilnya. Tanpa overlap lexical bermakna, jangan mengarang relevansi lexical. Jangan mencampur cosine dan output cross-encoder dalam satu fitur seolah skalanya sama. Kunci identitas/revision model, tokenizer, aturan pemotongan, template input dan kalibrasi fitur. Lindungi persyaratan penting dari pemotongan diam-diam.

Mode engine adalah LEXICAL_RULES, HYBRID_NO_RERANK dan HYBRID_RERANK. Gangguan model menggunakan fallback yang dinyatakan; ambang angka dikalibrasi terpisah per mode. Bila tidak ada sinyal relevansi yang mendukung, kecocokan wilayah dan anggaran saja tidak menghasilkan rekomendasi kuat. Kembalikan kurang dari lima atau tanpa kecocokan positif bila beralasan. Penjelasan hasil kosong merupakan keluaran valid.

Fitur dua arah usulan mempunyai bobot terpisah. Arah A menilai kecocokan inovasi/permintaan terhadap peluang penerima: relevansi masalah .45, tahap diterima .15, cakupan sektor/aplikasi .15, kontribusi keuangan kompatibel .15 dan waktu .10. Arah B menilai bantuan penerima terhadap pemohon: cakupan dukungan yang dibutuhkan .40, bentuk kerja sama/pembiayaan .30, jangkauan wilayah .15 dan ketersediaan .15. Ini merupakan hipotesis desain. Aturan wajib diperiksa independen dan tidak dapat dirata-ratakan hingga hilang.

Fitur diketahui memakai nilai nol sampai satu dengan pemetaan terdokumentasi. Bobot fitur belum diketahui tetap belum diketahui, bukan menormalkan ulang fitur positif yang tersisa. Untuk A hitung A_low sebagai jumlah kontribusi berbobot yang diketahui dan A_high sebagai A_low ditambah bobot tidak diketahui; lakukan hal sama pada B. H(a,b)=0 jika a+b=0, selain itu 2ab/(a+b). Batas kecocokan adalah 100H(A_low,B_low) dan 100H(A_high,B_high). Coverage adalah setengah jumlah bobot fitur diketahui kedua arah. Rentang menggambarkan informasi hilang, bukan confidence interval statistik atau peluang memperoleh pendanaan.

Contoh: A diketahui .80; B memiliki kontribusi diketahui .65 dan bobot tidak diketahui .15. Indeks bawah 100×2×.80×.65/(.80+.65)=71.72 dan atas 80.00. Jika fakta anggaran wajib belum diketahui, label utama tetap “Perlu konfirmasi.” Usulan tampilan kecocokan kuat mensyaratkan batas bawah ≥70, coverage ≥.70 dan ELIGIBLE; potensial mensyaratkan ≥50 dan ≥.50. Coverage di bawah .40 menunjukkan informasi belum cukup. Ambang ini merupakan parameter berversi yang menunggu validasi.

Kompatibilitas keuangan membandingkan subjek serta basis sama. Total proyek dibandingkan total dukungan proyek untuk periode/lingkup sama. Kontribusi individu yang diharapkan dibandingkan kisaran check kompatibel, bukan otomatis seluruh target putaran. Biaya lisensi dan persentase royalti merupakan besaran berbeda. Rentang sebasis beririsan memberi fitur indikatif 1; tidak beririsan tetapi dukungan parsial diterima eksplisit memberi .5; tidak beririsan yang diketahui ketika dukungan penuh diwajibkan memberi 0. Konversi mata uang belum tersedia, instrumen tidak sesuai, basis kontribusi tidak jelas atau periode berbeda menghasilkan UNKNOWN atau mismatch bertipe yang sesuai. R1 tidak mengarang kurs atau valuasi.

Urutkan dalam kelompok eligibility berdasarkan batas bawah konservatif, kemudian sinyal relevansi dan stable id. Kelompokkan peluang milik mitra setelah dinilai terpisah, menampilkan peluang terbaik yang memenuhi syarat dan hingga dua alternatif nyata. Batasi konteks pengelola berulang menjadi dua dari lima hasil awal bila ada alternatif relevan. Deduplikasi FundingRequest dilakukan sebelum presentasi; inovasi terkait tidak memenuhi daftar dengan penggalangan duplikat. Bagian kurasi/baru memberi peserta baru ruang tampil tanpa membuat minat palsu.

## 11. Jaminan transaksi, retry dan event

Setiap mutasi penting menyertakan expected_version dan Idempotency-Key yang terikat pelaku/cakupan/operasi. Simpan digest request dan hasil commit secara atomik. Key sama dengan parameter berbeda menghasilkan konflik; request sama mengembalikan hasil setara secara semantik. Retensi key usulan tujuh hari untuk pengajuan, keputusan, booking dan konfirmasi kerja sama, dengan status operasi tersedia sesudahnya; tetapkan retensi akhir sebelum penggunaan nyata. Idempotency mencegah niat duplikat, sedangkan pemeriksaan versi optimistis mencegah niat lama yang berkonflik. [Panduan API idempoten AWS](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).

Gunakan aturan unik database untuk pitching aktif dengan subjek–penerima–target–tujuan sama. Commit perubahan state, event audit yang dapat diatribusikan dan niat outbox bersama. Pengiriman event setidaknya sekali; deduplikasi konsumen wajib. Retry email atau indexing secara terpisah; kegagalan efek samping tidak membatalkan keputusan yang sudah terlihat atau mengulanginya. [Transactional outbox AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html).

Penerimaan pertemuan memeriksa interval aktif semua peserta wajib dan menulis booking atomik. Gunakan constraint atau locking database yang tepat; pemeriksaan ketersediaan UI tidak cukup. Range exclusion constraints PostgreSQL adalah salah satu mekanisme konkret pencegahan overlap pada resource sama. Penerimaan reschedule mengganti booking lama dalam transaksi sama tanpa keadaan kedua pertemuan berbenturan sama-sama commit. [Range types PostgreSQL](https://www.postgresql.org/docs/current/rangetypes.html).

Sesudah timeout jaringan, client yang mengetahui operation_id dapat menanyakan route status operasi berizin. Jika id belum pernah diterima, ulangi request identik dengan key idempotency semula dalam masa retensinya. UNKNOWN merupakan ketidakpastian, bukan bukti gagal atau izin mengirim key baru. Konflik mengembalikan versi saat ini dan satu tindakan pemulihan tanpa menghilangkan teks masukan. Perubahan penerimaan atau akses antara preflight dan submit diperiksa ulang. Pencabutan izin selama job antrean mencegah pengungkapan hasil walaupun artifact sudah dihasilkan.

## 12. Kontrak API

Gunakan JSON di bawah /api/v1, didokumentasikan dalam OpenAPI. Seluruh endpoint menegakkan otorisasi objek serta aturan versi/capability. Route berikut menetapkan tanggung jawab, bukan menyatakan implementasi telah ada.

| Area | Route konkret |
|---|---|
| Akun/konteks | GET /me; PATCH /me; GET /workspaces; POST /workspaces/{id}/invitations; POST /invitations/{id}/accept |
| Portofolio | POST /inventions; GET /inventions; GET/PATCH /inventions/{id}; GET /inventions/{id}/versions; POST /inventions/{id}/publish; POST /inventions/{id}/archive |
| Hak/bukti | POST /inventions/{id}/rights-claims; GET /inventions/{id}/evidence; POST /evidence/{id}/reviews |
| File/grant | POST /documents/upload-intents; POST /documents/{id}/complete; GET /documents/{id}/download; POST /documents/{id}/grants; POST /grants/{id}/revoke |
| Dukungan/proyek | POST/GET /support-requests; GET/PATCH /support-requests/{id}; POST /support-requests/{id}/activate; POST/GET /support-requests/{id}/budgets |
| Pendanaan perusahaan | POST/GET /funding-requests; GET/PATCH /funding-requests/{id}; POST /funding-requests/{id}/activate; POST /funding-requests/{id}/inventions |
| Penerimaan mitra | GET/PATCH /partners/{id}; POST/GET /opportunities; GET/PATCH /opportunities/{id}; POST /opportunities/{id}/activate; POST /opportunities/{id}/close |
| Penemuan | GET /discovery; POST /saved-items; DELETE /saved-items/{id}; POST /discovery-feedback |
| Matching/job | POST /matches; GET /match-runs/{id}; GET /jobs/{id}; POST /jobs/{id}/cancel |
| Status operasi | GET /operations/{id} |
| Preflight/brief | POST /pitches/preflight; POST /briefs; GET /briefs/{id}; GET /briefs/{id}/export |
| Pitching/keputusan | POST /pitches; GET /pitches; GET /pitches/{id}; POST /pitches/{id}/submit; POST /pitches/{id}/decisions; POST /pitches/{id}/withdraw |
| Revisi | POST /pitches/{id}/revision-rounds; PATCH /revision-items/{id}/response; POST /pitches/{id}/resubmit |
| Diskusi | GET/POST /pitches/{id}/messages; GET/POST /pitches/{id}/tasks; GET /notifications; POST /notifications/{id}/read |
| Penjadwalan | POST /pitches/{id}/schedule-proposals; POST /schedule-proposals/{id}/accept; POST /schedule-proposals/{id}/counter; POST /schedule-proposals/{id}/cancel |
| Pertemuan | GET /meetings/{id}; POST /meetings/{id}/reschedule; POST /meetings/{id}/cancel; POST /meetings/{id}/outcome; GET /meetings/{id}/calendar.ics |
| Kerja sama | POST /partnerships; GET/PATCH /partnerships/{id}; POST /partnerships/{id}/confirmations; POST /partnerships/{id}/publish; POST /partnerships/{id}/request-review |
| Review/moderasi | GET /workspace/review-queue; POST /workspace/reviews; POST /reports; GET /operator/reports; POST /operator/reports/{id}/actions |
| Portabilitas/privasi | POST /imports/validate; POST /imports/{id}/apply; POST /exports; POST /privacy-requests; GET /privacy-requests/{id} |

Operasi parsing, matching, brief dan ekspor yang lama dapat mengembalikan 202 dengan job_id dan URL status berizin. Status job adalah PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED dan NEEDS_MANUAL_INPUT; pembatalan best effort dan tidak berarti membalik perubahan domain yang sudah commit. GET /operations/{id} terpisah dari progres job: setelah memeriksa otorisasi pelaku/cakupan, kembalikan PENDING, COMMITTED dengan referensi hasil berizin, atau UNKNOWN ketika hasil otoritatif yang tersimpan tidak dapat dipastikan. Route tidak boleh membocorkan operasi pihak lain atau menyimpulkan kegagalan bisnis dari status yang tidak ditemukan. Daftar menggunakan cursor pagination tervalidasi. Kembalikan 401 untuk request belum terautentikasi, 403/404 secara konsisten untuk objek tanpa izin, 422 untuk validasi field/domain, 409 untuk versi lama/cakupan duplikat/booking konflik, dan 429 dengan petunjuk retry untuk batas penggunaan. Capability nonaktif mengembalikan CAPABILITY_UNAVAILABLE terdokumentasi tanpa menerima mutasi.

Error memuat code stabil, pesan sederhana, field_errors bila relevan, flag retryable, operation_id dan correlation_id. Jangan membuka stack trace, prompt privat, isi sumber atau keberadaan pelaku lain. Tidak ada endpoint generik yang membolehkan client mengatur sembarang state bisnis langsung. OpenAPI serta client hasil generate harus mempertahankan serialisasi decimal, makna null/unknown dan format zona waktu.

## 13. Desain antarmuka dan pemulihan

Navigasi default inovator adalah Beranda, Inovasi Saya, Temukan Investor/Mitra, Pitching dan Diskusi, Profil. Mitra memulai dari Jelajahi, kemudian Kebutuhan/Mandat, Pitching Masuk, Diskusi dan Jadwal, Profil. Mobile menampilkan maksimal empat tujuan utama ditambah Lainnya. Jadwal tetap di dalam workspace pitching; informasi kerja sama ada pada profil inovasi/entitas terkait. Jangan membuat halaman utama terpisah untuk setiap state.

Gunakan satu tindakan utama per layar, bahasa Indonesia sederhana dan rincian bertahap. Halaman inovasi mengutamakan masalah, solusi yang ada, dukungan diminta, lingkup keuangan, bukti dan pihak bertanggung jawab. Tampilan investasi membedakan pendanaan perusahaan dari dukungan proyek. Hindari badge skor tanpa penjelasan, klaim kesiapan otomatis atau analitik dekoratif. Label membedakan “perusahaan belum dibentuk,” “belum disediakan,” “dilaporkan sumber” dan “direview untuk kriteria ini.” Jelaskan skala teknis opsional sesuai konteks.

Desain harus mencakup lima perjalanan terhubung: inovator independen mencari dukungan proyek; startup menggalang satu pendanaan untuk dua inovasi; mitra meminta dan meninjau revisi per item; usulan balik slot dan pemulihan konflik; serta koreksi kerja sama diikuti konfirmasi kedua pihak. Setiap perjalanan memuat state kosong, loading, validasi, versi lama, izin ditolak dan jaringan terputus bila relevan. Pertahankan input nonrahasia setelah kegagalan yang dapat dipulihkan dan umumkan status tersimpan/belum tersimpan. Jangan menampilkan toast sukses sebelum konfirmasi commit server.

Target aksesibilitas adalah WCAG 2.2 AA yang memerlukan verifikasi hasil render, bukan klaim conformance dari dokumen ini. Kontras teks minimal 4.5:1, atau 3:1 untuk teks yang memenuhi definisi teks besar dalam standar; batas kontrol penting dan grafik nonteks bermakna memerlukan 3:1 terhadap warna sekitar ketika dipersyaratkan. Dukung pembesaran teks hingga 200% dan reflow pada 320 CSS px tanpa kehilangan isi atau fungsi, mengikuti pengecualian konten dua dimensi yang sah dalam standar. Target interaksi memenuhi minimum 24×24 CSS px atau pengecualian yang ditentukan standar; target nyaman 44×44 CSS px merupakan preferensi produk yang lebih kuat, bukan ambang AA universal. Uji pula perjalanan inti pada 360 px dan desktop. [WCAG 2.2](https://www.w3.org/TR/WCAG22/).

Seluruh tindakan dapat dioperasikan dengan keyboard, fokus terlihat dan tidak tertutup. Label dan error yang terhubung ke field menjelaskan koreksi; pembaruan status diumumkan tanpa memindahkan fokus secara tidak perlu. Dialog mempunyai nama aksesibel, penahanan fokus logis, tindakan tutup aman dan pengembalian fokus ke pemicu ketika tepat. Hormati preferensi reduced motion dan hilangkan gerakan nonesensial; status tidak bergantung pada animasi atau warna saja. Tindakan destruktif menjelaskan efek sebenarnya; menarik pitching, menghapus draf dan mencabut grant dokumen berbeda. Halaman dokumen yang ditolak menyediakan permintaan akses atau tindakan kembali tanpa membuka judul jika judul itu sendiri dilindungi. Aksesibilitas dan pemahaman pengguna memerlukan bukti aktual komponen, halaman tersusun dan alur pengguna.

## 14. Modular monolith dan kepemilikan modul

Arsitektur yang disetujui adalah modular monolith dengan satu otoritas domain, batas internal jelas dan core reusable yang dipelihara. Usulan awal implementasi memakai Python/FastAPI, client web responsif Next.js/TypeScript, PostgreSQL, object storage privat dan worker opsional dari rilis backend sama. Rincian stack merupakan pilihan awal, bukan perbandingan benchmark atau bukti aplikasi sudah dibangun. Server memiliki kebenaran domain; web, worker, impor dan adapter memanggil use case sama. Tabel job/outbox PostgreSQL memadai pada awal. Proses terpisah untuk job lama tidak memerlukan microservice per modul.

| Modul | Memiliki | Kolaborasi yang diizinkan |
|---|---|---|
| Identity/access | Akun, keanggotaan, capability, grant dan evaluasi kebijakan | Mengekspos query otorisasi/konteks; pemanggil tidak membaca repository langsung |
| Portfolio/evidence | Inovasi, versi, klaim, file dan fakta direview | Menerbitkan proyeksi berizin dan referensi versi sumber |
| Support/funding | Permintaan dukungan, anggaran proyek dan penggalangan venture | Menentukan subjek keuangan dan lingkup sebanding untuk matching/pitching |
| Partner intake | Profil, mandat, peluang dan persyaratan bertipe | Menerbitkan versi target aktif dan kebijakan penerimaan |
| Discovery/matching | Proyeksi indeks, match run, fitur dan penjelasan | Membaca interface sumber/target berizin yang eksplisit; tidak memberi akses |
| Pitch collaboration | Pengajuan, keputusan, revisi, diskusi dan tugas | Mengorkestrasi snapshot sumber dan eligibility penjadwalan yang disetujui |
| Scheduling | Usulan, pertemuan dan booking peserta | Memerlukan eligibility pitching; memiliki constraint booking atomik |
| Relationship records | Usulan, link entitas, konfirmasi dan proyeksi publik | Memvalidasi kewenangan pihak dan kesepakatan persis atas consent/versi |
| Delivery/operations | Job, pengiriman outbox, transport audit, orkestrasi impor/ekspor | Memanggil use case dengan konteks pelaku; tidak mengimplementasikan ulang aturan |

Dependency melewati interface modul dan kontrak data. Sembunyikan repository; tolak siklus import dan akses persistence lintas modul memakai architecture checks ketika visibility bahasa belum memadai. Pertahankan evaluasi aturan dan makna keuangan dalam satu implementasi server. Validasi frontend membantu feedback, tetapi bukan satu-satunya pemeriksaan. Fixture/OpenAPI bersama menjembatani bahasa tanpa menduplikasi engine matching dalam TypeScript.

Transaksi mengikuti use case, bukan endpoint HTTP atau handler background. Pengajuan, booking dan konfirmasi kerja sama dapat mengorkestrasi modul dalam satu transaksi database dengan kepemilikan eksplisit. Panggilan eksternal di luar transaksi bisnis menggunakan outbox/job serta callback aman terhadap retry. Ini penerapan modularitas yang diusulkan, bukan bukti batas modul telah ada. [Simon Brown tentang modular monolith](https://simonbrown.je/modular-monolith/).

Jangan membangun SDK plugin publik, memuat kode klien secara dinamis, memperkenalkan bahasa workflow bebas atau memisahkan service untuk skala hipotetis. Ekstraksi berikutnya membutuhkan contention terukur, kebutuhan kepemilikan/rilis terpisah atau isolasi konkret, disertai keputusan baru. Panduan monolith-first menjelaskan tradeoff operasional dan secara eksplisit bersifat tentatif; tidak menjamin pemisahan nanti mudah. [Fowler, Monolith First](https://martinfowler.com/bliki/MonolithFirst.html).

## 15. Keluarga produk reusable dan variasi yang diizinkan

Pengguna telah menyetujui TemuRiset sebagai core kemitraan inovasi reusable dengan strategi keluarga produk yang ringan. Penawaran terkait berbagi pekerjaan penemuan, evaluasi berbukti, pengungkapan terkendali dan kolaborasi. White-label menjelaskan penawaran memakai brand lain. SaaS menjelaskan hosting dan pemeliharaan sebagai layanan. Multitenancy menjelaskan pilihan berbagi/isolasi dalam sistem berjalan. Pilihan ini independen; sumber bersama saja tidak menjadikan produk pooled SaaS. [Kurikulum product line SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/), [SaaS dan multitenancy Microsoft](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/).

Gunakan konfigurasi untuk brand/copy, locale, mata uang didukung, identifier taksonomi/checklist disetujui, kebijakan review bernama, pilihan adapter dan kombinasi capability teruji. Gunakan modul capability biasa untuk perilaku berulang seperti review organisasi atau technical diligence terstruktur. Gunakan adapter untuk layanan identitas, katalog, model, storage, email atau kalender eksternal yang benar-benar dipakai. Masalah bisnis baru yang mengubah makna inti penemuan, hak, dukungan atau kolaborasi dapat menjadi produk terpisah dengan hanya berbagi komponen teknis yang terbukti.

Komposisi R1 default mengaktifkan dukungan proyek, pendanaan perusahaan, penemuan lisensi, dokumen, slot pertemuan manual, template brief dan notifikasi dalam aplikasi. Review organisasi, dense retrieval, reranking, rangkuman AI, kalender dan email eksternal opsional. AI nonaktif tidak mematikan template brief dan fakta manual. Kalender eksternal nonaktif tetap menyediakan pemeriksaan konflik internal dan ICS. company_funding nonaktif menyembunyikan pembuatan pendanaan dan menolak mutasinya, sementara dukungan proyek tetap bekerja; catatan pendanaan historis berizin tetap terbaca melalui transisi terdokumentasi. Review organisasi mempunyai migrasi antrean eksplisit pada FR20. Kombinasi tidak didukung ditolak saat validasi konfigurasi, bukan gagal di tengah perjalanan pengguna.

Contoh record komposisi memuat config_schema_version, config_revision, source_release, marketplace_id, brand_id, default_locale, supported_currencies, capability_ids beserta versi, checklist_policy_ids dan adapter_ids beserta versi. Isinya hanya referensi secret; kredensial berada di secret storage deployment. Schema memvalidasi nilai serta dependency yang diizinkan. Nama dan logo klien adalah konten, bukan conditional di dalam matching atau aturan izin. Simpan identitas konfigurasi pada preflight, pengajuan dan match run agar perubahan dapat direproduksi.

Setiap komposisi yang didukung membutuhkan pengujian invariant core, capability aktif/nonaktif, kontrak adapter, perjalanan perwakilan lengkap, izin/ekspor dan bukti migrasi/pemulihan. Flag rollout sementara mempunyai masa berakhir dan berbeda dari capability produk permanen. Panduan sumber bersama dan deployment konsisten mendukung pendekatan ini, sementara modul/komposisi spesifik masih usulan. [Panduan deployment dan konfigurasi Microsoft](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/deployment-configuration).

## 16. Berbagi marketplace dan pilihan deployment

Arah reuse yang disetujui memungkinkan satu sumber bersama melayani pilihan deployment klien terisolasi. Usulan delivery awal adalah satu deployment marketplace dengan banyak workspace pribadi dan organisasi. Proyeksi publik terpublikasi sengaja dapat ditemukan lintas organisasi; isi privat workspace tetap terbatas. Ruang pitching bilateral membagikan informasi terpilih kepada pihak bernama. Menambahkan filter organization_id di semua tempat akan merusak penemuan sekaligus gagal menyatakan izin dokumen sebenarnya. Karena itu organisasi tidak otomatis merupakan tenant pelanggan yang tertutup.

Klien yang membutuhkan isolasi dapat menjalankan rilis didukung yang sama dengan database, object store, secret, konfigurasi identitas dan kebijakan operatornya sendiri. Deployment tersebut memiliki jaringan pengguna serta peluang sendiri. Ia tidak otomatis berpartisipasi di marketplace lain, berbagi login atau membuka katalog kepada klien lain. Federasi antardeployment membutuhkan desain identitas, consent, berbagi, sinkronisasi dan governance eksplisit; di luar R1/R2.

Pilih pooled SaaS hanya dengan definisi pelanggan/tenant serta model operasi eksplisit. Jika diterapkan, turunkan konteks tenant dari identitas/keanggotaan terverifikasi, lalu tegakkan pada query database, cache, job, file, pencarian, ekspor, akses support dan telemetry. Resource yang sengaja publik serta kolaborasi lintas pihak berizin membutuhkan kebijakan eksplisit di dalam model itu. Jangan memakai branding, parameter URL atau selector frontend sebagai kewenangan tenant. Belum ada data biaya atau skala terukur yang membuktikan hosting pooled maupun terisolasi paling optimal.

## 17. Ekstensi klien dan alur rilis bersama

Pendekatan pemeliharaan yang disetujui adalah rilis bersama dengan variasi klien yang disengaja. Untuk klien baru, tulis addendum terhadap versi PRD dasar dan rilis sumber yang dikunci. Identifikasi pengguna nyata, hasil yang dibutuhkan, perubahan kebutuhan dan contoh sebelum mengimplementasikan variasi. Klasifikasikan setiap perbedaan sebagai konten/konfigurasi, capability berulang, adapter eksternal atau produk terpisah. Pertahankan invariant bersama dan catat penanggung jawab setiap checklist serta kebijakan klien. Brand baru tidak memerlukan duplikasi logika core atau arsitektur tenant baru.

Simpan peningkatan umum dalam sumber bersama. Adapter atau capability klien mempunyai contract test dan dikomposisikan secara sengaja. Hindari branch klien jangka panjang yang menumpuk versi identitas, keuangan, matching dan consent yang saling bertentangan. Jika fork disengaja tidak terhindarkan, tetapkan pemilik backport dan biayanya secara eksplisit; jangan menjanjikan pembaruan otomatis. Template repository memulai riwayat sumber independen dan tepat hanya jika kemandirian itu memang diinginkan. [Semantik template GitHub](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template).

Alur rilis: commit perubahan direview → jalankan uji core dan komposisi didukung → build artifact immutable → catat inventaris versi → uji migrasi/restore → deploy environment canary → verifikasi perjalanan aktual dan observability → rollout per deployment → simpan instruksi rollback/forward repair. Perubahan schema dimulai dengan expand, migrasi dengan bukti yang dapat dilanjutkan, pindahkan pembacaan/penulisan setelah pemeriksaan kompatibilitas, lalu contract hanya ketika rilis lama dipensiunkan. Rollback kode tidak aman untuk membalik seluruh transformasi data; dokumentasikan kapan forward repair atau restore backup diperlukan beserta jendela kehilangan datanya.

Catat pemilik deployment, jendela rilis yang didukung, status migrasi, bukti backup/restore dan pengecualian tersisa. Perbaikan tersedia dalam sumber bukan bukti sudah sampai ke klien. Ekstrak package bersama berversi hanya ketika konsumen nyata dengan rilis independen membutuhkannya. Modul internal dalam satu rilis tidak masing-masing memerlukan package registry atau pipeline rilis terpisah.

## 18. Data operasional, performa dan sasaran aksesibilitas

| Area | Sasaran usulan dan kondisi uji wajib |
|---|---|
| API standar | p95 ≤500 ms pada 20 pengguna bersamaan, 1,000 inovasi terpublikasi, 100 peluang aktif, tanpa upload/AI; catat hardware/cache |
| Penemuan cache | p95 ≤2 detik untuk halaman pertama berizin pada dataset sama; uji perubahan izin secara terpisah |
| Matching baru | Boleh memakai job; laporkan jumlah kandidat dan waktu aktual dengan feedback progres/pembatalan; tanpa SLA instan rekaan |
| Parsing teks/brief | Sasaran awal ≤60 detik untuk dokumen teks 20 halaman pada hardware/pengaturan provider tercatat; fallback manual tetap dapat dipakai |
| UX responsif | Perjalanan inti dapat dipakai pada 360 px, 768 px dan desktop; reflow 320 CSS px dan pembesaran teks 200% tanpa kehilangan konten/fungsi, dengan pengecualian WCAG yang sah |
| Aksesibilitas | Target WCAG 2.2 AA: teks4.5:1/besar3:1, kontrol nonteks penting3:1 bila wajib, target24×24 CSS px atau pengecualian standar; preferensi nyaman44×44, perilaku keyboard/fokus/error/status/dialog/reduced motion diverifikasi pada hasil render |
| Integritas | Tidak ada hard criterion diketahui gagal yang disajikan lulus; nol pembacaan lintas konteks tanpa izin dalam pengujian keamanan terdefinisi |
| Keandalan | Request berulang menghasilkan satu efek yang dimaksud; latihan restore/migrasi terdokumentasi sebelum data pilot nyata |
| Observability | Correlation/operation id, umur antrean, mode fallback, versi model/config, kegagalan dan biaya; tanpa isi privat dalam log rutin |

Semua angka merupakan hipotesis perencanaan, bukan klaim produksi. Ukur jalur cold/warm, kondisi jaringan, ukuran file, batas provider dan concurrency perwakilan. Tetapkan retensi, ketersediaan, frekuensi backup, recovery point/time dan kontak insiden sebelum komitmen layanan nyata. R1 dapat memakai deployment kecil dengan operasi diawasi; hal itu tidak menghilangkan kebutuhan integritas atau otorisasi.

Jangan mengumpulkan nomor identitas nasional, kredensial keuangan atau dokumen pribadi sensitif hanya untuk profil publik inovator. Program verifikasi berikutnya harus menetapkan kebutuhan, pembatasan akses, retensi dan arti badge yang sebenarnya. Terbitkan penjelasan privasi serta pemrosesan sebelum upload nyata. Tinjau ketentuan pemrosesan provider model sebelum mengirim isi privat; gunakan hanya adapter yang aktif/disetujui dan izinkan deployment manual-only.

## 19. Fixture sintetis generik dan hasil acuan tepat

Semua nama, nominal dukungan, organisasi, dokumen dan aktivitas pada bagian ini adalah fixture DEMO fiktif, dikeluarkan dari tren nyata dan metrik hasil. Semuanya kontrak pengujian, bukan bukti pelanggan atau minat investasi nyata. Gunakan lima sektor dan variasi kepemilikan/tahap yang disengaja.

| Fixture | Subjek dan keadaan yang dinyatakan | Permintaan dan target | Hasil inti yang diharapkan |
|---|---|---|---|
| F01 ClearSpring | Inovator independen; prototipe penyaring air; tanpa perusahaan/paten; CURRENT 10 L/hour, PLANNED 20 L/hour; file uji fungsi tersedia | Proyek validasi enam bulan USD20,000–30,000; mitra menerima prototipe, menawarkan USD15,000–40,000 untuk lingkup sama dan mensyaratkan keberadaan file saat pengajuan | Tahap/file/anggaran PASS; READY_TO_SUBMIT; tidak ada perusahaan atau paten bukan penghalang |
| F02 FieldDry | Proses pengeringan agritech komunitas; tahap pilot; kewenangan hak belum ditetapkan | Fasilitas uji nonuang; target memerlukan kewenangan direview sebelum pengajuan | Kewenangan UNKNOWN; NEEDS_INFORMATION; tanpa nominal uang atau klaim kepemilikan rekaan |
| F03 QueueNest | Tim software kecil; alat penjadwalan sudah berfungsi; diskusi lisensi; CURRENT ekspor offline, PLANNED SSO | Target mensyaratkan CURRENT SSO saat pengajuan | SSO FAIL; INCOMPATIBLE/BLOCKED_FOR_THIS_TARGET walau topik sangat mirip |
| F04 LoopMaterial | Startup material diwakili entitas fiktif yang sudah didirikan Demo Circular Materials Ltd; perusahaan pada pembiayaan pre-seed, material kemasan pada kematangan prototipe | FRaise01 total pendanaan ekuitas USD500,000, kontribusi diharapkan USD50,000–100,000, pendanaan parsial/sindikasi diterima eksplisit; investor individu menawarkan check ekuitas USD50,000–150,000 dan menerima perusahaan pre-seed dengan prototipe | Kompatibilitas kontribusi PASS; satu permintaan, bukan lima check investasi atau valuasi; investor individu tidak membutuhkan organisasi |
| F05 ReFormPress | Inovasi manufaktur dikelola entitas demo yang sama dengan F04 | Inovasi kedua dikaitkan FRaise01, penerima sama | Satu hasil FundingRequest dan satu pitching pendanaan aktif; dua link inovasi pendukung |
| F06 GridShare | Solusi pemantauan energi komunitas; tim nonprofit; tahap ide; kebutuhan uang belum diketahui; status entitas hukum belum dikonfirmasi | Mitra menerima konsep awal untuk mentoring/dukungan nonuang; target lain memerlukan subjek ekuitas berbadan hukum | Jalur mentoring dapat memenuhi kriteria yang dinyatakan; persyaratan entitas ekuitas UNKNOWN karena status belum dikonfirmasi |

Gunakan Recipient A sebagai mitra validasi prototipe, Recipient B investor ekuitas perusahaan berbadan hukum, Recipient C distributor produk siap pasar yang meminta sertifikasi saat ini pada pengajuan, dan Recipient D target lisensi software. Setiap peluang menyatakan versi, penerimaan aktif serta tahap persyaratannya sendiri. Sertifikat komersialisasi tahap mendatang tidak menghalangi jalur prototipe Recipient A; sertifikat eksplisit tahap pengajuan Recipient C dapat menghalangi.

Hasil acuan tambahan: minimum F01 -1 atau maksimum di bawah minimum tidak valid; dukungan USD bulanan tidak dibandingkan total USD enam bulan tanpa basis ekuivalen dikonfirmasi; EUR dan USD UNKNOWN tanpa konversi bertanggal yang diaktifkan; dukungan proyek versus mandat khusus ekuitas adalah FAIL pada bentuk kerja sama. Jika fixture terpisah secara eksplisit memastikan tidak ada entitas hukum dan target mensyaratkan entitas yang sudah ada pada pengajuan, kriterianya FAIL; jangan mengganti hasil UNKNOWN F06 untuk status yang belum dikonfirmasi. Jika file F01 tersedia tetapi belum direview, DOCUMENT_PRESENT lulus sedangkan REVIEWER_CONFIRMED tetap UNKNOWN. Permintaan CURRENT20 L/hour gagal terhadap nilai CURRENT10 yang diketahui; PLANNED20 tidak menyelamatkannya.

Untuk uji jadwal, peserta P sudah dibooking 09:00–10:00 UTC. Kandidat 09:30–10:30 berkonflik; 10:00–11:00 diperbolehkan memakai interval setengah terbuka. 09:00 UTC tampil 16:00 Asia/Jakarta dan 17:00 Asia/Makassar untuk instant sama. Penerimaan pertemuan overlap secara bersamaan menghasilkan satu booking commit dan satu konflik yang dapat dipulihkan. Untuk konfirmasi, perubahan ringkasan versi 1 ke versi 2 membatalkan consent versi-1; konfirmasi versi-2 sepihak tidak menerbitkan badge bersama.

## 20. Evaluasi dan pembelajaran produk

Buat dataset direview yang mencakup pasangan relevan, tidak kompatibel dan belum diketahui lintas sektor fixture, kemudian tambahkan kasus nyata berizin. Sedikitnya dua reviewer memberi label relevansi, hasil persyaratan dan dukungan penjelasan secara independen; simpan ketidaksepakatan serta adjudikasi. Kelompokkan split berdasarkan inovasi/entitas/permintaan pendanaan dasar dan peluang terkait. Parafrasa nyaris duplikat serta dua inovasi dari pendanaan perusahaan sama tidak boleh bocor antara development dan evaluasi held-out. Atur bobot serta ambang hanya dari data development. Ini menerapkan panduan leakage yang mapan pada domain usulan. [Common pitfalls scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html).

Bandingkan lexical+rules, dense+rules, hybrid+rules dan reranking opsional pada korpus berizin serta versi input sama. Ukur candidate recall, precision terhadap hasil dikembalikan, P@5 bila terdefinisi, nDCG@5, pelanggaran hard constraint diketahui, ketepatan UNKNOWN, dukungan sumber faktual, coverage/abstention, latensi/biaya dan exposure pengelola baru/lama. Laporkan jumlah hasil sebenarnya; jangan mengubah definisi P@5 untuk menyembunyikan hasil yang lebih sedikit. Usulan target pilot adalah tidak ada pelanggaran hard rule diketahui dan seluruh klaim faktual yang diperiksa dapat ditelusuri; sasaran relevansi ditetapkan setelah baseline berlabel pertama, bukan diklaim di sini.

Lakukan sesi tugas awal dengan 5–8 orang mencakup inovator independen, pengelola startup dan investor/mitra, termasuk penggunaan keyboard/mobile. Sampel ini menemukan masalah, bukan memperkirakan efek populasi. Sasaran usulan: setidaknya 80% tugas terdefinisi selesai tanpa bantuan moderator, median pitching dengan profil siap kurang dari lima menit, pemilihan slot kurang dari dua menit dan pemahaman benar bahwa persetujuan belum berarti pendanaan. Catat kegagalan, bantuan dan pemahaman istilah, kemudian revisi. Jangan mengklaim target telah tercapai.

Pantau diskusi terkonfirmasi per permintaan aktif, waktu menuju tindakan tepat berikutnya, penyelesaian revisi, alasan diterima/ditolak/kedaluwarsa dan hasil tindak lanjut yang diizinkan. View/save hanya sinyal aktivitas. Nominal investasi dilaporkan membutuhkan subjek, tanggal, sumber dan izin pelaporan; tidak dibuat dari total proposal. Catat denominator hasil serta data tindak lanjut yang hilang agar klaim keberhasilan dapat ditafsirkan.

## 21. Urutan implementasi dan pembuktian komposisi

Bangun vertical slice berurutan: identitas/otorisasi dengan konteks pribadi; inovasi dan bukti berversi; dukungan/anggaran proyek dan pendanaan perusahaan; penerimaan mitra serta persyaratan bertipe; matching/preflight/template brief deterministik; pitching/keputusan/revisi; diskusi bersama dan penjadwalan aman terhadap race; konfirmasi kerja sama/proyeksi publik; impor/operasi/migrasi komposisi. Setiap slice mencakup kegagalan penting dan skenario penerimaannya.

Komposisi pertama untuk didemonstrasikan adalah dasar generik dengan fakta manual dan aturan lexical. Komposisi didukung kedua mengaktifkan review organisasi tanpa mengubah makna domain. Ketiga menonaktifkan company_funding tetapi mempertahankan dukungan proyek, untuk membuktikan perilaku nonaktif yang didukung, bukan membuat edisi komersial arbitrer. Adapter AI dan kalender opsional mendapat contract/fallback test hanya ketika benar-benar diimplementasikan. Komposisi tidak dianggap didukung hanya karena togglenya ada dalam konfigurasi.

R2 menambahkan kebutuhan workflow yang terbukti, data nyata disetujui, preferensi email, adapter kalender eksternal dan peningkatan matching terukur. Item L memerlukan pernyataan masalah dan model operasi baru: pooled SaaS, federasi, pelatihan model, pelaksanaan transaksi, workflow hukum lanjut atau SDK ekstensi publik. Jangan menambahkannya hanya karena arsitektur memungkinkan modul baru.

## 22. Handoff desain dan implementasi

Desainer menerima PRD lengkap ini, komposisi/versi terpilih dan fixture sintetis. Hasilkan peta layar, token/komponen reusable, copy utama/sekunder, tampilan per role serta perjalanan terhubung dengan state sukses/error/pemulihan. Catat route, kebutuhan sumber, ekspektasi akses, keputusan responsif dan batas simulasi. Prototipe harus membedakan simulasi lokal dari perilaku yang ditegakkan server. Keberadaan file desain tidak membuktikan otorisasi aktual, konsistensi booking atau ketepatan keuangan.

Gunakan urutan design-system-first: mulai dengan [04_Claude_Design_System_TemuRiset_EN.md](04_Claude_Design_System_TemuRiset_EN.md) serta [05_Prompt_Claude_Design_System_EN.md](05_Prompt_Claude_Design_System_EN.md); buat dan periksa sistem atau referensi portabel yang sebenarnya; catat nama/versi, identifier sumber/artifact, inventaris token/komponen, metode binding, status validasi dan penyimpangan; kemudian gunakan [02_Claude_Design_TemuRiset_EN.md](02_Claude_Design_TemuRiset_EN.md) dengan [03_Prompt_Claude_Design_EN.md](03_Prompt_Claude_Design_EN.md) untuk menyusun aplikasi dari referensi itu. Handoff aplikasi memuat seluruh PRD Inggris kanonis secara persis. Handoff Markdown tidak dengan sendirinya mendaftarkan design system atau menjadikannya default organisasi.

Periksa permukaan authoring aktual dan mekanisme import/komponen yang tersedia. Jika dukungan sistem terdaftar tidak ada, gunakan referensi portabel/lokal berlabel jelas dan laporkan binding dengan jujur; jangan mengklaim pewarisan sistem yang tidak tersedia atau diam-diam memakai default lain. Workbench sistem mendahului aplikasi dan memvalidasi token, komponen serta pola perwakilan. Aplikasi pemakai berikutnya harus memverifikasi binding, perjalanan lengkap dan ekspor yang tersedia. Tidak satu pun tahap dianggap sudah dijalankan hanya karena spesifikasinya ada.

Engineer menghasilkan migration database, use case domain, OpenAPI, kontrak adapter, seed berizin, schema komposisi, fixture regresi, instruksi operasi dan daftar capability/status. Rujuk FR serta AC dalam pekerjaan implementasi. Catat penyimpangan disengaja, alasan dan kriteria penerimaan pengganti yang disetujui. Jangan menafsirkan istilah bisnis ambigu secara berbeda di modul terpisah.

Delivery harus menyertakan panduan menjalankan, referensi environment/secret, identitas build immutable, inventaris schema/config, prosedur backup/restore dan instruksi rollback/forward repair. Artifact hasil, addendum klien baru dan release notes tetap berversi dalam repository sama agar pekerjaan cloud/lokal berlanjut pada commit sama. Jangan bergantung percakapan lama atau path lampiran sementara untuk menetapkan perilaku runtime.

## 23. Skenario penerimaan

Seluruh skenario berikut berstatus **NOT RUN**, belum dijalankan. Implementasi harus menyediakan bukti, environment, komposisi, versi sumber/config dan hasil aktual. Setiap baris merupakan hasil acuan perilaku; lolos pemeriksaan dokumen bukan berarti lolos pengujian ini.

| ID | Kebutuhan | Skenario | Hasil wajib |
|---|---|---|---|
| AC01 | FR01 | Inovator independen mendaftar tanpa institusi/perusahaan | Konteks pribadi dan alur Inovator tersedia; tanpa afiliasi rekaan |
| AC02 | FR01 | Investor individu memilih Investor/Mitra | Isian mandat/penerimaan investor tersedia tanpa kewajiban organisasi |
| AC03 | FR01 | Akun demo membuat save/view | Event jelas berlabel DEMO dan dikeluarkan dari tren/hasil nyata |
| AC04 | FR02 | Anggota dapat mengedit tetapi tidak memutuskan pitching masuk | Edit diizinkan sesuai cakupan; keputusan ditolak server |
| AC05 | FR02 | Pengguna memilih id workspace yang tidak diikuti | Konteks/akses ditolak; metadata resource privat tidak dibuka |
| AC06 | FR02 | Keanggotaan dicabut saat job ekspor tertunda | Akses job/hasil diperiksa ulang dan ditolak bagi pelaku yang izinnya dicabut |
| AC07 | FR03 | Satu pelaku menerbitkan dua inovasi | Versi, bukti, permintaan dan pipeline tetap terpisah |
| AC08 | FR03 | Inovasi terpublikasi diedit sesudah pengajuan | Draf/versi baru dibuat; snapshot pengajuan tidak berubah |
| AC09 | FR03 | Inovasi diarsipkan ketika diskusi berjalan | Penemuan/pengajuan baru berhenti; riwayat berizin tetap tersedia |
| AC10 | FR04 | Pencipta berbeda dari pemilik hak yang dinyatakan | Identitas/cakupan ditampilkan terpisah; tanpa inferensi kepemilikan |
| AC11 | FR04 | Inovator tanpa paten dan target tidak mewajibkannya | Publikasi/pitching tidak dihalangi oleh ketiadaan paten |
| AC12 | FR04 | Pengguna melihat pratinjau pengungkapan | Proyeksi publik serta penerima/versi file terpilih eksplisit; tanpa klaim NDA otomatis |
| AC13 | FR05 | Upload selesai ditransfer tetapi karantina/pemeriksaan keamanan belum selesai | File belum AVAILABLE dan DOCUMENT_PRESENT tetap UNKNOWN; status ekstraksi tidak melewati pemeriksaan keamanan |
| AC14 | FR05 | File tersedia tetapi kriteria review memerlukan konfirmasi | DOCUMENT_PRESENT dapat lulus; REVIEWER_CONFIRMED tetap UNKNOWN |
| AC15 | FR05 | Scan lulus pemeriksaan keamanan tetapi tidak ada OCR yang didukung | File AVAILABLE dan DOCUMENT_PRESENT dapat lulus; ekstraksi NEEDS_MANUAL_INPUT, isi belum direview UNKNOWN; tanpa fakta/skor kesiapan rekaan |
| AC16 | FR06 | Minimum anggaran negatif atau maksimum di bawah minimum | Error field 422; nilai draf dipertahankan untuk koreksi |
| AC17 | FR06 | Dukungan validasi nonuang, nominal belum diketahui | Lingkup nonuang dapat dipakai; nominal null, bukan nol rekaan atau penggalangan tersimpulkan |
| AC18 | FR06 | Nominal bulanan dan total proyek bermata uang sama | Tidak ada skor kompatibilitas langsung tanpa basis ekuivalen dikonfirmasi |
| AC19 | FR07 | FRaise01 terkait F04 dan F05 | Satu pendanaan/hasil, dua referensi inovasi; target tidak digandakan |
| AC20 | FR07 | Target putaran500k versus check50–150k, kontribusi diharapkan50–100k | Check dibandingkan kontribusi; irisan PASS, tanpa mismatch otomatis terhadap seluruh putaran |
| AC21 | FR07 | Tim prapendirian diterima mandat lalu mengusulkan ekuitas terkonfirmasi | Diskusi diizinkan; konfirmasi memerlukan entitas aktual yang diidentifikasi |
| AC22 | FR08 | Profil direktori belum mengonfirmasi penerimaan | Label sumber/ketersediaan; tanpa niat investasi aktif rekaan |
| AC23 | FR08 | Mitra menutup penerimaan langsung | Pitching langsung umum tidak tersedia; peluang spesifik valid diperiksa terpisah |
| AC24 | FR08 | Jalur pilihan mitra berupa formulir eksternal | Pengalihan eksternal ditampilkan; klik tidak dicatat sebagai pitching terkirim di aplikasi |
| AC25 | FR09 | Mitra menerbitkan dua mandat berbeda | Nilai terpisah; jangan menggabungkan field menguntungkan dari mandat berbeda |
| AC26 | FR09 | Peluang aktif ditutup sebelum submit | Submit baru ditolak dengan penjelasan state target yang dapat dipulihkan |
| AC27 | FR09 | Kriteria naratif belum memiliki pemetaan bertipe disetujui | UNKNOWN/klarifikasi manual; tanpa kegagalan otomatis tersembunyi |
| AC28 | FR10 | Pengguna baru tanpa riwayat perilaku | Preferensi eksplisit/kurasi/item baru bekerja tanpa tren palsu |
| AC29 | FR10 | Filter tidak menghasilkan kecocokan | Jelaskan dan tawarkan edit filter yang disengaja; tanpa perluasan diam-diam |
| AC30 | FR10 | Pemilik berkali-kali me-refresh inovasinya | Tidak menambah tren mitra yang memenuhi syarat |
| AC31 | FR11 | F03 mempunyai PLANNED SSO, target meminta CURRENT SSO | Kegagalan fitur diketahui; tidak masuk shortlist positif meski relevan |
| AC32 | FR11 | Bukti hak belum tersedia | UNKNOWN dan membutuhkan informasi; tidak menganggap hak tidak ada |
| AC33 | FR11 | A=.80, B_low=.65, bobot B belum diketahui=.15 | Batas71.72–80.00; label UNKNOWN wajib mendapat prioritas |
| AC34 | FR12 | Peluang berubah sesudah preflight | Respons 409/versi dan preflight ulang; pesan masukan dipertahankan |
| AC35 | FR12 | AI tidak tersedia atau menghasilkan referensi tanpa dukungan | Brief deterministik dapat diedit; klaim tidak valid tidak dikirim |
| AC36 | FR12 | Brief bergantung sumber privat yang izinnya dicabut | Artifact terlindungi ditolak/diredaksi menurut grant saat ini; tanpa pengungkapan cache lama |
| AC37 | FR13 | Key pengajuan sama diulang sesudah timeout jaringan | Satu pitching commit dan hasil setara |
| AC38 | FR13 | Key sama dipakai dengan target/body berbeda | Konflik; tanpa pengajuan kedua atau perubahan diam-diam |
| AC39 | FR13 | Permintaan pendanaan/target sama dikirim melalui inovasi terkait lain | Duplikat aktif dicegah; pitching yang ada dikembalikan/dirujuk |
| AC40 | FR14 | Penerima menyetujui pitching | Hanya APPROVED_FOR_DISCUSSION; tanpa catatan pendanaan atau kerja sama |
| AC41 | FR14 | Dua keputusan bertentangan bersamaan pada versi sama | Satu commit; pihak yang kalah menerima konflik versi |
| AC42 | FR14 | Penerima memutuskan pengajuan yang sudah ditarik | Transisi ditolak; tanpa pembukaan ulang atau perubahan reputasi publik |
| AC43 | FR15 | Revisi wajib dijawab “Belum dapat dipenuhi” | Resubmit diizinkan setelah seluruh item wajib dijawab; tidak otomatis disetujui |
| AC44 | FR15 | Fitur usulan baru ditambahkan dalam jawaban revisi | Tetap PLANNED; kemampuan saat ini tidak berubah tanpa bukti |
| AC45 | FR15 | Putaran/versi baru dipilih saat resubmit | Jawaban/snapshot lama tersimpan; gerbang review perubahan material diterapkan ulang bila aktif |
| AC46 | FR16 | Pengiriman email gagal sesudah commit keputusan | Keputusan tetap sekali; pengiriman retry/deduplikasi terpisah |
| AC47 | FR16 | Waktu pertemuan lewat tanpa konfirmasi hasil | Tidak otomatis COMPLETED atau menghasilkan pendanaan |
| AC48 | FR16 | Pengguna tidak terkait membuka URL ruang pitching | Respons ditolak/disembunyikan; tanpa kebocoran pesan/file/metadata |
| AC49 | FR17 | UTC09:00 dilihat dari Jakarta/Makassar | Instant sama tampil16:00/17:00 dengan label zona waktu |
| AC50 | FR17 | Penerimaan slot overlap bersamaan untuk peserta sama | Satu booking berbenturan commit; lainnya mendapat konflik yang dapat dipulihkan |
| AC51 | FR17 | Reschedule diusulkan tetapi belum diterima | Pertemuan/booking lama tetap sampai penggantian atomik atau pembatalan eksplisit |
| AC52 | FR18 | Satu pihak mengonfirmasi kerja sama versi1 | Tidak ada badge publik dikonfirmasi bersama |
| AC53 | FR18 | Pihak lain mengedit ringkasan menjadi versi2 | Konfirmasi versi1 tidak mengonfirmasi versi2 |
| AC54 | FR18 | Dana proyek dicatat tanpa ekuitas | Hanya hubungan PROJECT; tanpa inferensi kepemilikan/persentase saham |
| AC55 | FR19 | Kedua pihak mengonfirmasi ringkasan sama tetapi hanya satu mengizinkan nominal publik; kemudian satu pihak mencabut field publik | Nominal tetap privat; hanya irisan consent publik; field dicabut langsung tersembunyi pada pembacaan baru; perluasan memerlukan putaran konfirmasi baru |
| AC56 | FR19 | Satu hubungan ekuitas perusahaan mendukung dua inovasi | Satu hubungan tingkat entitas, dua link; tanpa saham ganda |
| AC57 | FR19 | Pihak meminta review hubungan publik yang disengketakan | Klaim publik disembunyikan/direview sesuai kebijakan; audit privat tersimpan |
| AC58 | FR20 | organization_review nonaktif untuk inovator independen | Tanpa gerbang institusi rekaan; alur pitching inti bekerja |
| AC59 | FR20 | Reviewer menyetujui versi sumber lama | Persetujuan tidak mengizinkan versi penerus yang berubah material |
| AC60 | FR20 | Capability review dinonaktifkan dengan antrean tertunda | Migrasi konfigurasi diblokir sampai penyelesaian/pemindahan item eksplisit |
| AC61 | FR21 | External system/id sama diimpor dua kali | Upsert sesuai cakupan; tanpa duplikasi inovasi atau peningkatan status kerja sama dilaporkan sumber |
| AC62 | FR21 | Impor bertentangan dengan fakta hak yang sudah direview | Pratinjau menandai konflik; tanpa overwrite diam-diam |
| AC63 | FR21 | Grant dicabut sebelum hasil ekspor didownload | Otorisasi saat ini menolak isi bergantung dan mengakhiri/membatalkan akses hasil |
| AC64 | FR22 | Pengguna melaporkan penyamaran | Kasus privat dibuat; tindakan operator sesuai cakupan diaudit |
| AC65 | FR22 | Grant dicabut sesudah penerima mendownload file | Request gateway/range baru diblokir; salinan/bytes yang sedang dikirim tidak dapat ditarik dan UI menjelaskan batas itu |
| AC66 | FR22 | Permintaan penghapusan terkena pengecualian retensi | Respons menyatakan kategori ditahan/alasan/kebijakan; tanpa klaim penghapusan lengkap palsu |
| AC67 | FR23 | company_funding nonaktif | Mutasi pendanaan baru ditolak; dukungan proyek bekerja dan riwayat berizin ditangani eksplisit |
| AC68 | FR23 | Adapter AI/kalender nonaktif | Fakta manual/template brief/slot internal+ICS tetap dapat dipakai |
| AC69 | FR23 | Konfigurasi berisi secret atau kombinasi capability tidak valid | Validasi menolak sebelum trafik dilayani; invariant tidak dapat dimatikan |
| AC70 | FR24 | Perbaikan bersama dirilis untuk dua komposisi klien | Kedua suite dan inventaris versi diperlukan; ketersediaan rilis tidak disamakan rollout |
| AC71 | FR24 | Perubahan schema dipasang dengan kode lama/baru yang didukung | Kompatibilitas expand/migrate diverifikasi; contract/penghapusan menunggu rilis lama dipensiunkan |
| AC72 | FR24 | Migrasi tidak dapat dibalik rollback kode | Prosedur forward repair/restore dan jendela kehilangan data diuji/didokumentasikan |

## 24. Penyelesaian, asumsi dan batas bukti

Pengguna telah menyetujui arah produk serta monolith/reuse; implementasi, pembuatan design system dan verifikasi runtime tetap pekerjaan terpisah yang belum selesai. R1 baru lengkap ketika perjalanan inti berjalan dengan data nyata berizin atau data sintetis berlabel, seluruh bukti penerimaan R1 tercatat, komposisi didukung lulus, operasi penting dilatih dan keterbatasan tersisa terlihat sebelum demonstrasi atau undangan pilot. Prototipe yang rapi saja tidak memenuhi otorisasi server, concurrency, privasi atau kebutuhan delivery. PRD dan laporan penelitian tidak membuktikan platform reusable sudah diimplementasikan.

Pertanyaan produk terbuka mencakup kelompok rekrutmen pertama, verifikasi penerimaan investor, kapasitas review, preferensi istilah, negara/mata uang awal, ketentuan pemrosesan provider, kebijakan retensi akhir dan tanggung jawab delivery/support. Selesaikan kewajiban pasar tertentu dan prosedur perjanjian aktual bersama pihak bertanggung jawab yang tepat sebelum menawarkan fiturnya. Dasar ini tidak menganggap satu checklist, skala kematangan atau rezim hukum menjawab semua sektor.

Sumber mendasari desain, bukan jaminan permintaan atau efektivitas. Belum ada wawancara lapangan, hasil investasi, penetration test, benchmark model, hasil beban produksi atau penilaian conformance aksesibilitas berdasarkan spesifikasi ini. Validasi alur generik lengkap terkecil dan satu variasi nyata sebelum membangun infrastruktur lebih luas.

## 25. Referensi primer terpilih

Semua halaman berikut dibuka pada penelitian 31 Oktober 2026. Halaman vendor menjelaskan capability produk yang dipublikasikan, bukan hasil tervalidasi independen. Arah produk dan modular-monolith/reuse telah disetujui pengguna. Rincian schema, pilihan stack/model, bobot/kebijakan angka dan asumsi rilis/performa belum terukur tetap merupakan usulan pada bagian yang menyatakannya; persetujuan bukan bukti implementasi.

- [Gambaran WIPO GREEN](https://www3.wipo.int/wipogreen/en/aboutus/) — penyedia/pencari teknologi dan konteks kolaborasi.
- [FAQ transfer teknologi WIPO](https://www.wipo.int/en/web/technology-transfer/faq) dan [perjanjian](https://www.wipo.int/en/web/technology-transfer/agreements) — kepemilikan, pengungkapan dan tujuan perjanjian berbeda.
- [Panduan inovator Halo](https://knowledge.halo.science/articles/8946411648-guide-for-innovators) dan [panduan pengajuan peluang](https://knowledge.halo.science/articles/4031823346-finding-and-applying-to-opportunities-on-halo) — jenis inovator beragam dan alur tugas.
- [Inpart Campaigns](https://www.inpart.io/network/campaigns) — persyaratan spesifik peluang dan hasil kolaborasi.
- [Database investor OpenVC](https://www.openvc.app/investor-database) dan [jalur outreach](https://www.openvc.app/investor-outreach) — tahap, kisaran check, mandat dan jalur kontak pilihan.
- [Software product lines SEI](https://www.sei.cmu.edu/library/software-product-lines-curriculum/) — aset bersama terkelola dan variasi produk terkait.
- [Simon Brown, Modular monolith](https://simonbrown.je/modular-monolith/) dan [Fowler, Monolith First](https://martinfowler.com/bliki/MonolithFirst.html) — batas ditegakkan dan tradeoff service awal.
- [SaaS/multitenancy Microsoft](https://learn.microsoft.com/en-us/azure/architecture/guide/saas-multitenant-solution-architecture/) dan [deployment/konfigurasi](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/deployment-configuration) — pilihan delivery/isolasi independen dan sumber bersama.
- [Template repository GitHub](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template) — riwayat independen hasil generate.
- [Reciprocal Rank Fusion](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) dan [retrieval/reranking Sentence Transformers](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) — pola retrieval.
- [Otorisasi OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [multitenancy](https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html), [upload file](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [prompt injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) — kebutuhan keamanan implementasi.
- [Range PostgreSQL](https://www.postgresql.org/docs/current/rangetypes.html), [outbox AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html), [idempotency AWS](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) — mekanisme transaksi dan retry.
- [Panduan leakage scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html) — pemisahan pemilihan model dan bukti held-out.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — target aksesibilitas, kriteria angka, pengecualian berlaku dan syarat conformance; tidak ada klaim conformance telah tercapai.
