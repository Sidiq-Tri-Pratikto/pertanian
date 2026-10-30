# Masalah Indonesia, implementasi yang sudah ada, dan lima celah solusi untuk Kartika Cyber Hackathon

## Apa yang sudah diimplementasikan di Indonesia dan di TNI?

### Takeaway
Dashboard sentimen umum bukan hal baru di Indonesia. Peluang yang lebih defensible adalah menambahkan keputusan operasional spesifik: kebutuhan bantuan mana yang perlu diverifikasi, klaim mana yang memerlukan klarifikasi, aduan kualitas mana yang perlu diinspeksi, serta apakah masalah warga benar-benar selesai. Riset ini memakai batas waktu 26 Oktober 2026 WIB; status yang tidak dapat dikonfirmasi publik disebut gap, bukan dinyatakan belum pernah ada.

### Cited Findings
- **Drone Emprit: produk Indonesia yang ditawarkan dan dipublikasikan, bukan ide hipotetis.** Situs pengembang Media Kernels menyebut platform media/social-media monitoring, tren, dan sentimen; tersedia pula Drone Emprit Academic. Sumber ini membuktikan keberadaan serta positioning produk, tidak membuktikan akurasi atau adopsi instansi tertentu. — [Media Kernels: Drone Emprit](https://mediakernels.com/our-products/drone-emprit/)
- **NoLimit: produk komersial Indonesia untuk pemerintah.** Halaman pemerintah menawarkan dashboard khusus, integrasi sumber internal/eksternal, sentiment positif/netral/negatif, dan alarm perubahan percakapan. Logo/cerita klien di halaman vendor adalah klaim vendor, bukan audit implementasi atau bukti sistem TNI. — [NoLimit untuk kementerian](https://nolimit.id/gov)
- **Indonesia Indicator:** situs resmi tersedia, tetapi halaman hasil fetch tidak menampilkan konten yang cukup untuk memverifikasi fitur maupun pelanggan. Jangan memakai mereknya sebagai bukti implementasi sentiment tertentu tanpa sumber tambahan. — [Situs resmi Indonesia Indicator](https://www.indonesiaindicator.com/home)
- **CRM Jakarta: layanan pemerintah yang sudah beroperasi.** Artikel resmi Jakarta Smart City tanggal 12 Januari 2026 melaporkan 195.730 aduan sepanjang 2025; sistem mencatat, meneruskan, dan menindaklanjuti aduan. Ini membuktikan alur aduan dan skala, belum otomatis membuktikan ABSA/AI triase tertentu. — [Bedah Data CRM 2025](https://smartcity.jakarta.go.id/id/blog/bedah-data-crm-2025-ketika-suara-warga-gerakkan-kota/)
- **SP4N-LAPOR!/CRM bukan ruang kosong.** Situs CRM saat riset mengelompokkan kanal resmi menjadi lima kelompok; artikel Jakarta Maret 2025 menyebut 13 kanal individual. Hindari menyebut perbedaan pengelompokan sebagai kontradiksi jumlah tanpa konteks. — [CRM kanal pengaduan](https://crm.jakarta.go.id/kanal-pengaduan); [Pemprov Jakarta, 4 Maret 2025](https://www.jakarta.go.id/cepat-respon-masyarakat)
- **PetaBencana: crowdsourcing dan API sudah ada.** Dokumentasi mencantumkan endpoint laporan, arsip, dan timeseries. FAQ menyatakan arsip dapat diakses melalui Open API dan laporan dibagikan dengan instansi terkait untuk verifikasi/respons. Ini bukti produk dan dokumentasi; keberhasilan setiap integrasi tidak diuji di riset ini. — [Dokumentasi Open API](https://docs.petabencana.id/routes); [FAQ resmi](https://info.petabencana.id/faq)
- **MAFINDO: fact checking dan kanal masyarakat sudah ada.** Produk yang dijelaskan meliputi basis artikel Yudistira, WhatsApp Kalimasada, TurnBackHoax, dan Global Fact-check Database. Halaman layanan mencantumkan dokumentasi dan permintaan API key: jangan mengasumsikan API bebas tanpa key atau lisensi semua konten bebas. — [Produk MAFINDO](https://mafindo.or.id/produk/); [Layanan publik TurnBackHoax](https://turnbackhoax.id/layanan-publik)
- **TNI AD memiliki halaman publik Media Monitoring** berisi feed pemberitaan. Ini membuktikan fungsi agregasi/monitoring publik, **bukan bukti bahwa AI sentiment dashboard tertentu sudah diproduksikan**. Halaman terindeks lengkap, tetapi direct fetch dalam riset ini sempat 502. — [TNI AD dalam Media](https://tniad.mil.id/media-monitoring/)
- **Ada bukti akademik historis tentang IMM TNI AD.** Tesis di repositori Universitas Terbuka menyebut Intelligence Media Monitoring dimiliki sejak 2014 dan menggambarkan aplikasi pada beberapa satuan. Ini laporan penelitian, bukan konfirmasi kondisi 2026, rincian kontrak, maupun kinerja alat. Tidak perlu mengangkat rincian arsitektur internal yang tak relevan dengan ide publik. — [Tesis UT, bagian sekitar halaman 140](https://repository.ut.ac.id/8772/1/43794.pdf)
- **Media Center TNI historis dilaporkan diresmikan 28 Mei 2014**, dengan fasilitas media monitoring dan media analysis. Sumber ini peliputan reporter saat peresmian, bukan dokumentasi teknis primer dan bukan bukti fitur AI terkini. — [detikNews, 28 Mei 2014](https://news.detik.com/berita/d-2594535/tni-kini-punya-media-center-mata-untuk-pantau-berita-di-media)
- **BGN sudah memiliki SAGI 127, 24 jam**, untuk aduan, masukan, dan klarifikasi MBG, menurut siaran pers 27 Februari 2026. Maka jangan mengusulkan pembuatan hotline MBG seolah belum ada. — [BGN: SAGI 127](https://www.bgn.go.id/news/berita/bgn-buka-akses-pengaduan-mbg-publik-bisa-lapor-ke-127)
- **IASC sudah menangani penipuan transaksi keuangan.** Portal menjelaskan pelaporan korban, penghubungan ke lembaga keuangan, dan proses penundaan transaksi. Prototipe hackathon tidak boleh mengaku bisa memblokir rekening sendiri atau menjamin pengembalian dana. — [IASC OJK](https://iasc.ojk.go.id/)

### Inferences
- Pembeda yang layak: kebutuhan/aspek + bukti sumber + ketidakpastian + verifikasi manusia + tindak lanjut terukur. Word cloud, pie chart sentiment, dan ringkasan LLM saja akan bersaing langsung dengan produk mapan.
- Implementasi yang lebih cocok dengan kepentingan publik dan TNI AD berada pada bantuan kemanusiaan, transparansi rekrutmen, komunikasi publik faktual, layanan program sosial, dan aspirasi pembangunan desa.
- Label negatif tidak sama dengan hoaks, ancaman, intoleransi, niat kriminal, atau kebutuhan tindakan keamanan. Semua lima ide di bawah memproses isi keluhan/isu secara agregat; tidak membuat skor loyalitas/ancaman orang, profiling politik, atau pelacakan individu.

### Gaps
- Tidak ada wawancara pengguna TNI, BNPB, BGN, ataupun Pemda; pain point spesifik workflow di bawah adalah hipotesis yang diturunkan dari bukti masalah dan harus divalidasi.
- Tidak dapat memverifikasi semua sistem internal TNI/Kemhan atau deployment terkini IMM. Tidak ada dasar menyebut proposal sebagai "pertama di Indonesia".
- Tidak ada akses internal CRM, LAPOR, SAGI, atau IASC; ketersediaan data publik ≠ izin menyalin seluruh data atau membuka identitas pelapor.

## Lima ide: masalah apa yang dapat diselesaikan dan apa solusi teknisnya?

### Takeaway
Lima ide berikut sengaja berbeda dalam **keputusan pengguna**, bukan sekadar mengganti sektor untuk classifier yang sama. Semua adalah usulan desain, bukan sistem yang telah dibangun atau hasil akurasi yang sudah diukur. Peringkat editorial awal: bantuan bencana dan anti-penipuan rekrutmen paling seimbang untuk demo dengan relevansi TNI AD; MBG sangat relevan tetapi memerlukan mitra data dan kehati-hatian informasi kesehatan/anak.

### Cited Findings

#### 1. SUARA SIAGA — dashboard kebutuhan bantuan dan keresahan penyintas

**Masalah terdokumentasi.** BNPB mencatat dampak bencana 2024 berupa 8.136.271 orang menderita/mengungsi serta kerusakan 80.304 rumah. TNI AD menyebut operasi bantuan Sumatera November 2025 memprioritaskan logistik, evakuasi, dapur lapangan, sarana umum, dan akses wilayah terisolasi. Angka personel tidak dibutuhkan untuk solusi. — [BNPB: Data Bencana 2024](https://www.bnpb.go.id/buku/buku-data-bencana-indonesia-tahun-2024); [TNI AD: bantuan kemanusiaan Sumatera](https://tniad.mil.id/kerahkan-21-707-personel-dan-beragam-alutsista-tni-ad-perkuat-bantuan-kemanusiaan-di-sumatera/)

**Sudah ada apa?** PetaBencana telah memetakan laporan urun daya, mempunyai arsip/API, dan mendokumentasikan data teks, waktu, jenis bencana, serta geometri. Bukan ide baru untuk mengambil laporan masyarakat dan memasukkannya ke peta. — [Open API](https://docs.petabencana.id/routes); [Skema laporan urun daya](https://docs.petabencana.id/master-1/routes/crowdsourced-reports)

**Usulan keputusan pengguna.** Operator posko BPBD/mitra kemanusiaan/TNI AD membuka antrean kebutuhan: "tiga laporan air bersih belum dipenuhi di kecamatan A; perlu verifikasi". Petugas menandai diverifikasi, ditugaskan, dipenuhi, atau masih menunggu. Tujuan: mengurangi waktu membaca/duplikasi dan menemukan kebutuhan yang terlewat; bukan mengganti komando tanggap darurat.

**Usulan solusi teknis.** Ingest arsip PetaBencana + laporan form relawan berizin → normalisasi ringan, redaksi PII → deduplikasi semantik dan ruang-waktu → model multi-label kebutuhan (air, obat, makanan, sanitasi, akses), sentiment/aspek (misalnya distribusi terlambat), dan confidence → peta kebutuhan agregat dengan potongan bukti → antrean verifikasi serta log status. Priority berbasis kebutuhan eksplisit dan umur laporan, bukan jumlah marah/viral. Lokasi yang diekstrak dari teks harus diberi status "dugaan"; jangan menebak lokasi dari profil pengguna.

**MVP yang realistis.** Replay satu peristiwa banjir di satu wilayah, 4–6 jenis kebutuhan, 3 layar: peta, antrean verifikasi, status kebutuhan. Tambah contoh sintetis yang diberi watermark karena korpus publik mungkin lebih banyak melaporkan genangan daripada kebutuhan bantuan. Integrasi real-time opsional, jangan menjanjikan cakupan semua platform.

**Evaluasi usulan.** Anotasi ganda 200–300 sampel nyata yang sah + adjudikasi, recall kebutuhan mendesak, precision prioritas-10, akurasi geolokasi administratif, reduksi duplikat, dan waktu triase dibanding operator tanpa dashboard. Split per kejadian/waktu supaya salinan satu insiden tak bocor ke test.

**Celah yang dapat diklaim hati-hati.** "Lapisan kebutuhan dan tindak lanjut di atas peta laporan yang sudah ada." Bukti publik yang ditinjau belum mengonfirmasi fitur yang identik pada mitra tertentu; jangan menyatakan tidak ada di Indonesia.

#### 2. REKRUT AMAN — early warning penipuan yang mengatasnamakan rekrutmen TNI

**Masalah terdokumentasi.** PPID TNI AD menegaskan seleksi Tamtama/Bintara/Catar/Sepa PK gratis dan meminta masyarakat waspada penipuan. Kemnaker juga memberi peringatan lowongan palsu dan pungutan rekrutmen. Secara lebih luas, OJK melaporkan IASC menerima 373.129 laporan dengan kerugian dilaporkan Rp8,2 triliun sampai 30 November 2025; ini angka historis penipuan transaksi keseluruhan, **bukan angka penipuan rekrutmen TNI**. — [PPID TNI AD, 12 Februari 2025](https://ppid.tniad.mil.id/index.php/i/22364/rekrutmen%20-tni%20-angkatan%20-darat); [Kemnaker, 12 Januari 2025](https://cpns.kemnaker.go.id/news/detail/kemnaker-minta-masyarakat-selektif-terhadap-informasi-lowongan-pekerjaan); [OJK RDKB November 2025](https://www.ojk.go.id/id/berita-dan-kegiatan/siaran-pers/Pages/RDKB-November-2025.aspx)

**Sudah ada apa?** Peringatan resmi rekrutmen, layanan fact-check MAFINDO, dan IASC sudah berjalan; dashboard tidak boleh menjual kemampuan menggantikan investigasi, verifikasi resmi, atau pemblokiran. — [MAFINDO](https://mafindo.or.id/produk/); [IASC](https://iasc.ojk.go.id/)

**Usulan keputusan pengguna.** Dispenad/panitia rekrutmen melihat lonjakan pertanyaan dan pengalaman calon: permintaan biaya, jaminan kelulusan, domain palsu, jadwal membingungkan. Mereka memilih materi edukasi atau klarifikasi, sementara calon mendapatkan rujukan halaman resmi. Jika terdapat pengakuan telah mentransfer, pengguna diarahkan ke kanal resmi, tanpa aplikasi mengirim laporan otomatis.

**Usulan solusi teknis.** Dua jalur input: (a) CSV komentar publik yang diperoleh secara sah/pertanyaan formulir opt-in, (b) unggah tangkapan layar yang diberikan korban secara sadar. OCR → pisahkan pertanyaan biasa, testimoni, dan dugaan penawaran → ekstraksi pola permintaan uang/jaminan, URL tertera, topik rekrutmen → sentiment takut/bingung/kecewa sebagai konteks layanan → retrieval syarat/jadwal resmi berserta tanggal berlaku → klaster modus agregat dan antrean review. Cocokkan domain resmi secara deterministik; jangan mengunjungi URL mencurigakan. Model tidak memutuskan identitas seseorang penipu.

**MVP yang realistis.** Fokus TNI AD dan satu siklus penerimaan. 30–50 klaim/informasi resmi sebagai knowledge base, 100–200 contoh terkurasi/consented, dashboard 5 modus, serta tampilan bukti sebelum operator menandai "perlu klarifikasi". Hindari grafik jaringan individu.

**Evaluasi usulan.** Precision/recall indikasi pungutan dan klaim jaminan, false positive pada pengutipan peringatan resmi ("hati-hati penipu minta uang"), kesesuaian tanggal/kategori rekrutmen, recall retrieval dokumen resmi, dan waktu pengguna menemukan jawaban. Data train/test dipisah per template/modus/waktu, bukan random baris yang hampir identik.

**Celah yang dapat diklaim hati-hati.** "Dari kecemasan calon ke pola kebingungan dan modus yang memerlukan respons berbukti." Nilai sentiment tetap eksplisit; jika proyek hanya phishing detector, ia berisiko keluar dari fokus minat Sentiment Dashboard.

#### 3. GIZI DENGAR — triase aspek layanan MBG dan sinyal insiden yang perlu verifikasi

**Masalah terdokumentasi.** Dokumen rencana aksi Kemenkes menyebut belum semua SPPG beroperasi memiliki SLHS dan mengaitkannya dengan potensi keracunan; ini alasan untuk verifikasi kualitas, bukan bukti bahwa keluhan tertentu menunjukkan keracunan. BGN membuka SAGI 127 untuk aduan, masukan, klarifikasi; TNI AD secara publik mendukung pasokan pangan SPPG. — [RAP Ditjen Penanggulangan Penyakit 2025–2029](https://bbkkmakassar.kemkes.go.id/assets/files/RAP_Ditjen_Penanggulangan_Penyakit_Tahun_2025-2029.pdf); [BGN: SAGI](https://www.bgn.go.id/news/berita/bgn-buka-akses-pengaduan-mbg-publik-bisa-lapor-ke-127); [BGN: dukungan TNI AD, 30 Oktober 2025](https://www.bgn.go.id/news/infografis/tni-ad-siapkan-ribuan-hektar-lahan-untuk-perkuat-pasokan-bahan-pangan-mbg)

**Sudah ada apa?** Pengaduan SAGI dan standar sertifikasi sudah ada. Pembeda bukan call center baru atau pie chart pro/kontra MBG. — [SAGI 127](https://www.bgn.go.id/news/berita/bgn-buka-akses-pengaduan-mbg-publik-bisa-lapor-ke-127); [Pedoman Sertifikasi Keamanan Pangan SPPG](https://cdn-web.bgn.go.id/juknis/01KA7MRKDF4HY0J5H008X5Z201.pdf)

**Usulan keputusan pengguna.** Pengelola layanan/SPPG/Pemda menerima ringkasan aspek: rasa, porsi, ketepatan waktu, makanan rusak, permintaan diet khusus, atau laporan gejala yang harus diteruskan ke petugas kesehatan. Operator memisahkan perbaikan menu rutin dari inspeksi kualitas. Kepuasan tinggi tidak boleh menurunkan prioritas laporan keamanan pangan.

**Usulan solusi teknis.** Gunakan ekspor aduan yang dianonimkan oleh mitra atau survei sukarela wali/sekolah; ingest per tanggal dan kode SPPG → ABSA multi-aspek + ekstraksi sinyal insiden eksplisit → pengelompokan insiden menu/tanggal/lokasi → aturan eskalasi setelah verifikasi manusia → halaman audit respons. Sentiment "enak tetapi datang basi" harus menghasilkan aspek rasa positif dan kualitas negatif. Tidak menginferensikan diagnosis, penyebab, atau penyakit dari teks. Identitas siswa dan foto wajah tak masuk korpus demo.

**MVP yang realistis.** Satu kelompok 3–5 dapur/daerah, 6 aspek, CSV anonymized atau sintetis terlabel, tautan pedoman, dan antrean operator. Data SAGI bukan dataset publik; tanpa kemitraan, demo harus jelas berupa simulasi. Jangan mengambil data anak dari akun sosial.

**Evaluasi usulan.** Macro-F1 per aspek, recall laporan kualitas yang perlu diperiksa, salah gabung insiden antar dapur, serta waktu operator menemukan kasus uji dibanding urutan kronologis. Gold label ditentukan pengelola/ahli pangan untuk rute eskalasi; model tidak dinilai sebagai alat diagnosis.

**Celah yang dapat diklaim hati-hati.** "Lapisan triase kualitas dan tindak lanjut di atas kanal resmi yang sudah ada." Bukti terbuka belum cukup untuk menyatakan BGN tidak mempunyai analitik serupa secara internal.

#### 4. BUKTI PUBLIK — meja klarifikasi dengan sentiment, konteks, dan jejak sumber

**Masalah terdokumentasi.** Komdigi menyebut 1.923 konten hoaks teridentifikasi sepanjang 2024 dan perlunya kerja bersama pemerintah-kampus-media-industri. MAFINDO sudah memiliki arsip periksa fakta, sedangkan TNI AD telah mempublikasikan feed media monitoring. — [Komdigi, 26 November 2025](https://portal.komdigi.go.id/kanal-publik/berita-kini/9839); [Produk MAFINDO](https://mafindo.or.id/produk/); [TNI AD Media Monitoring](https://tniad.mil.id/media-monitoring/)

**Sudah ada apa?** Social listening dan mesin pencarian cek fakta sudah tersedia. Jangan mengklaim sentiment dapat menentukan kebenaran, bot, koordinasi jahat, atau niat pengguna. — [Drone Emprit](https://mediakernels.com/our-products/drone-emprit/); [Layanan MAFINDO](https://turnbackhoax.id/layanan-publik)

**Usulan keputusan pengguna.** Petugas humas layanan publik memilih pertanyaan/klaim faktual yang belum terjawab dan menyiapkan klarifikasi dengan tautan sumber. Contoh non-politis: jadwal bantuan, syarat rekrutmen, lokasi posko, atau angka penyaluran yang tertukar. Sistem juga menunjukkan kritik/keluhan yang valid agar dijawab substantif, bukan dihapus.

**Usulan solusi teknis.** CSV/news RSS/komentar berizin → pisahkan kalimat opini, pengalaman, pertanyaan, dan klaim yang dapat diperiksa → klaster per klaim → model sentiment serta confusion/uncertainty → retrieve dokumen resmi/TurnBackHoax, tampilkan tanggal dan kutipan relevan → label manusia: didukung, dibantah, bukti belum cukup → draf klarifikasi dengan provenance. LLM hanya menyusun draf berdasarkan evidence yang ditampilkan; publikasi tetap tindakan operator. Dashboard mengukur perubahan volume pertanyaan berulang, lag klarifikasi, dan persentase klaim belum diperiksa.

**MVP yang realistis.** Satu topik administratif/humanitarian, 20–30 dokumen resmi terkurasi, 100 klaim/pertanyaan campuran. Retrieval BM25 dapat menjadi baseline; embeddings hanya jika memberi peningkatan. API MAFINDO memerlukan permintaan key; fallback kurasi tautan/artikel sesuai izin, bukan scraping massal.

**Evaluasi usulan.** Precision retrieval@5, coverage klaim, groundedness tiap kalimat draf, kelengkapan/tanggal sumber, false-positive pada opini yang diberi label klaim, serta penilaian petugas. Perubahan sentiment sebelum/sesudah klarifikasi bersifat deskriptif; jangan menyebut bukti kausal keberhasilan komunikasi karena ada confounder dan platform bias.

**Celah yang dapat diklaim hati-hati.** "Tutup siklus dari kebingungan publik → bukti → respons → evaluasi pertanyaan tersisa." Lebih jelas dan dapat diaudit dibanding narasi "melawan opini negatif".

#### 5. SUARA DESA TUNTAS — aspirasi TMMD dari keluhan menjadi backlog pembangunan yang dapat diverifikasi

**Masalah terdokumentasi.** Publikasi resmi TMMD 2025 menyatakan sasaran disusun dari aspirasi masyarakat dan rencana pembangunan daerah. Korem 091 menyebut aspirasi disaring melalui Babinsa/Koramil dengan mempertimbangkan urgensi. Ini membuktikan kebutuhan proses bottom-up, **bukan bukti bahwa mereka saat ini gagal membaca aspirasi**. CRM Jakarta menunjukkan alur closed-loop pengaduan skala besar telah ada di konteks Pemda. — [PPID TNI AD: penutupan TMMD 124](https://ppid.tniad.mil.id/index.php/i/25385/penutupan-tmmd-ke-124-kodim-0610sumedang-jadikan-keberhasilan-tmmd-sebagai-inspirasi-untuk-terus-berkarya-dan-pengabdian-kepada-bangsa-dan-negara); [Korem 091: TMMD 125](https://korem091.tni-ad.mil.id/tmmd-wujud-nyata-sinergi-tni-dengan-pemerintah-daerah-dan-masyarakat/); [CRM Jakarta 2025](https://smartcity.jakarta.go.id/id/blog/bedah-data-crm-2025-ketika-suara-warga-gerakkan-kota/)

**Sudah ada apa?** Musyawarah/penyaringan aspirasi dan program TMMD sudah berjalan, CRM dan LAPOR sudah beroperasi. Jangan membangun pengganti LAPOR nasional; pilih alat pendamping satu desa/program, dengan hak akses dan ekspor sederhana.

**Usulan keputusan pengguna.** Tim desa-Pemda-TMMD membahas ringkasan kebutuhan air, jalan, sanitasi, sekolah, dan akses layanan; keputusan prioritas dicatat terbuka dengan alasan. Setelah pekerjaan selesai, warga dapat memberi konfirmasi "selesai secara administrasi tetapi masalah masih ada". Sentiment per aspek melengkapi bukti lapangan dan musyawarah, tidak memvoting hak warga dari komentar terbanyak.

**Usulan solusi teknis.** Form sukarela, transkrip wawancara dengan izin, serta catatan musyawarah → normalisasi bahasa lokal/code-mix → ekstraksi pasangan objek-masalah-lokasi dan ABSA → deduplikasi tuntutan → backlog dengan aspek, jumlah laporan, confidence, status, penanggung jawab → verifikasi penyelesaian via wawancara/inspeksi, feedback warga, dan bukti hasil. Sampling offline dan formulir petugas penting agar yang minim internet tetap terwakili. Tidak ada skor dukungan warga terhadap institusi.

**MVP yang realistis.** Satu desa, 4 aspek, sekitar 50–100 aspirasi berizin/rekayasa untuk demo, workflow usul→diskusi→keputusan→dikerjakan→diverifikasi. Fitur pembeda: arsip kebutuhan yang ditolak/ditunda beserta alasan, dan pembukaan kembali masalah jika belum selesai.

**Evaluasi usulan.** F1 aspek, precision deduplikasi, proporsi kebutuhan valid yang masuk backlog, waktu membuat ringkasan musyawarah, serta disagreement antara status administrasi dan verifikasi warga. Audit keterwakilan kanal dan bahasa tanpa menyimpulkan sampel sebagai pendapat seluruh desa.

**Celah yang dapat diklaim hati-hati.** "Transparansi aspirasi dan verifikasi manfaat di satu siklus TMMD." Sistem aspirasi sejenis sudah ada; diferensiasi adalah dukungan bahasa/aspek dan pembuktian hasil program, bukan novelty platform pengaduan.

### Inferences
- Kesesuaian relatif (penilaian peneliti, bukan skor resmi): SUARA SIAGA relevansi TNI AD tinggi dan data awal paling terbuka; REKRUT AMAN relevansi tinggi dan demo paling fokus; GIZI DENGAR relevansi tinggi tetapi akses data paling sulit; BUKTI PUBLIK cocok cognitive domain namun diferensiasi perlu ketat; SUARA DESA TUNTAS cocok administrasi/pembangunan dan pengguna lapangan, tetapi membutuhkan kerja validasi lapangan lebih banyak.
- Lima workflow berbeda: (1) alokasi/verifikasi kebutuhan; (2) edukasi anti-penipuan dan rute pengaduan; (3) inspeksi kualitas dan eskalasi layanan; (4) klarifikasi faktual berbukti; (5) prioritas pembangunan dan verifikasi penyelesaian.
- Demo perlu menunjukkan kalimat campuran, ironi, kutipan berita, copy-paste, Bahasa Indonesia–daerah, serta model abstain saat confidence rendah. Dengan ini sentiment memiliki fungsi nyata sekaligus batas yang jelas.

### Gaps
- Tidak ada angka publik tervalidasi tentang jumlah kasus penipuan rekrutmen TNI AD pada periode tertentu dalam sumber yang ditinjau; angka IASC tidak boleh dipakai sebagai substitusi.
- Belum ada izin/corpus lokal untuk semua ide. Sasaran jumlah data dan metrik di atas adalah rancangan evaluasi, bukan hasil eksperimen atau jaminan akurasi.
- Direktori data terbuka CRM/LAPOR yang berisi teks aduan lengkap belum dikonfirmasi. Data agregat publik tidak cukup untuk melatih ABSA.
- Publikasi MBG dan bantuan memiliki sensitivitas serta potensi perubahan; validasi final sebaiknya langsung dengan pemilik program. Tidak ada akses data kesehatan, identitas anak, data rekening, atau informasi internal TNI.

## Model, data, dan pembuktian teknis apa yang realistis untuk Indonesia?

### Takeaway
Gunakan model Indonesia yang sudah ada sebagai baseline dan tambahkan anotasi domain terbatas. Nilai tambah utama berada pada label aspek/keputusan, kualitas data, dan evaluasi temporal; jangan melatih foundation model atau menjanjikan akurasi nasional dari benchmark umum.

### Cited Findings
- **IndoNLU** menyediakan 12 downstream task dan model IndoBERT/IndoBERT-lite. Repositori juga menyebut Twitter dikeluarkan dari rilis Indo4B karena batasan kebijakan developer. Model tersedia tidak berarti korpus media sosial bebas didistribusikan. — [Repositori resmi IndoNLU](https://github.com/IndoNLP/indonlu/blob/master/README.md); [Paper IndoNLU](https://arxiv.org/abs/2009.05387)
- **IndoBERTweet** adalah model untuk teks Twitter Indonesia, dipublikasikan EMNLP 2021; repositori menyebut pretraining Desember 2019–Desember 2020, normalisasi mention/URL dan emoji, serta tidak merilis data pretraining karena kebijakan Twitter. Model tetap butuh fine-tuning/head klasifikasi yang sesuai, dan data lama bukan jaminan bahasa sosial 2026. — [Repositori penulis](https://github.com/indolem/IndoBERTweet); [Paper](https://arxiv.org/abs/2109.04607)
- **NusaX** merupakan corpus paralel sentiment Indonesia, Inggris, dan 10 bahasa lokal; diterjemahkan dan diverifikasi penutur lokal dari dataset sentiment. Dataset berlisensi CC-BY-SA, kode Apache 2.0. Ini dapat dipakai untuk sanity check bahasa, bukan bukti kinerja sarkasme/code-mix atau bahasa lapangan bencana. — [Repositori resmi NusaX](https://github.com/IndoNLP/nusax); [Paper EACL](https://aclanthology.org/2023.eacl-main.57.pdf)
- **PetaBencana** mempunyai endpoint laporan terkini/arsip. Dokumentasi request meminta User-Agent; contoh respons berisi teks dan created_at. Jangan mengasumsikan semua field lama selalu terisi; validasi skema aktual sebelum implementasi. — [Open API](https://docs.petabencana.id/routes); [Dokumentasi Crowdsourced Reports](https://docs.petabencana.id/master-1/routes/crowdsourced-reports)
- **MAFINDO API** dicantumkan sebagai layanan yang meminta API key; ada arsip publik periksa fakta. — [Layanan publik](https://turnbackhoax.id/layanan-publik)

### Inferences
- **Arsitektur minimum yang disarankan:** import CSV/API yang sah → simpan raw timestamp/provenance → redaksi data pribadi → dedup → baseline TF-IDF+logistic regression dibanding IndoBERT/IndoBERTweet → klasifikasi sentiment/aspek/domain → confidence/abstain → dashboard dan antrean review → ekspor catatan hasil. PostgreSQL/SQLite cukup untuk replay terbatas; vector DB terpisah, Kafka, dan agen berantai belum diperlukan.
- **Pisahkan empat output:** sentiment terhadap aspek; kebutuhan/intensi eksplisit; status kebenaran klaim dari bukti/manusia; status penyelesaian. Satu label negatif tidak dapat menggantikan keempatnya.
- **Paket evaluasi yang diusulkan:** 200–300 sampel domain dianotasi ganda untuk MVP, adjudikasi, laporkan disagreement dan distribusi kelas; uji macro-F1/per-class recall plus metrik keputusan per ide. Angka target akurasi baru ditetapkan setelah baseline; jangan menjanjikan >90% dari hasil paper beda domain.
- **Hindari leakage:** train/test dipisah waktu, per kejadian/per template; semua duplicate group masuk split sama; evaluasi tersendiri untuk slang, code-mix, sarkasme, keluhan campuran, dan sumber berbeda. Laporkan confidence calibration/abstention coverage dan confusion matrix. Validasi 20 contoh gagal secara kualitatif bisa lebih berguna daripada satu accuracy besar.
- **Paket demo jujur:** satu dataset nyata yang legal + subset sintetis ditandai jelas, manifest sumber/izin/tanggal, replay deterministik, human override, bukti setiap kesimpulan, dan kalkulasi latensi aktual. Tidak perlu klaim streaming semua platform.
- **Dampak diukur pada pengguna:** menit yang dihemat, kebutuhan/keluhan valid yang ditemukan, kualitas rute tindak lanjut, serta berapa kasus yang benar-benar diverifikasi selesai. Banyaknya sentimen negatif bukan metrik ancaman atau kinerja instansi secara keseluruhan.

### Gaps
- Belum mengunduh dataset, memeriksa availability runtime API, menjalankan model, menilai lisensi tiap aset turunan, atau melakukan uji akurasi/biaya pada perangkat target.
- Akses YouTube/X/TikTok/Instagram harus diverifikasi saat implementasi melalui API/izin yang tersedia; tidak ada dasar menjanjikan scraping tanpa batas atau akses percakapan WhatsApp privat.
- Belum mendapat konfirmasi pengguna akhir bahwa kelima workflow lebih penting daripada alternatif sederhana berupa spreadsheet/kanal pengaduan yang ada.
