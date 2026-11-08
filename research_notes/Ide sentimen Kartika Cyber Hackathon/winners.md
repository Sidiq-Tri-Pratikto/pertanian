# Pemenang hackathon terkait analisis sentimen

Tanggal akses: 26 Oktober 2026 (WIB). Penelusuran dibatasi sekitar 15 panggilan web, dengan prioritas bukti penyelenggara dan halaman proyek primer. Semua gagasan adaptasi di bawah adalah inferensi peneliti, bukan fitur yang terbukti pernah dipakai TNI atau klaim alasan menang.

## Proyek apa yang benar-benar memperoleh penghargaan?

### Takeaway
Ada cukup bukti primer untuk delapan contoh relevan. Jenis penghargaan berbeda: juara keseluruhan, juara problem/site tertentu, kategori, serta honorable mention; jangan menyebut semuanya sebagai juara umum. Kemenangan hackathon membuktikan pengakuan juri, bukan akurasi model atau implementasi operasional.

### Cited Findings

#### 1. Linguistic Pandas — Social Media Sentiment Analysis (2018)
- **Penghargaan:** first prize Rp ekuivalen tidak dihitung; hadiah asli **Rs 100.000 / one lakh**, untuk problem Ministry of Information and Broadcasting, Smart India Hackathon 2018, final 30–31 Maret di Jaipur. **Jenis:** problem/ministry winner, bukan klaim juara umum SIH. **Bukti:** pengumuman institusi tim (MAIT), sumber primer institusional; belum ada pengumuman pusat SIH yang dibaca. — [MAIT](https://www.cse.mait.ac.in/index.php/hackathon/sih)
- **Teknis terdokumentasi:** mengambil informasi terotorisasi dari media sosial, merangkum reaksi komentar/tweet, klasifikasi positif/netral/negatif, insight dan grafik. Arsitektur model, kode, serta evaluasi tidak disebutkan. — [MAIT, bagian 2018](https://www.cse.mait.ac.in/index.php/hackathon/sih)
- **Keyakinan:** tinggi untuk kemenangan dan tujuan; terbatas untuk mekanisme ML. Halaman yang sama memuat tim bernama Linguistic Pandas di tahun lain, jadi rujuk bagian **2018**, jangan mencampur anggota/tugas dari tabel tahun lain. — [MAIT](https://www.cse.mait.ac.in/index.php/hackathon/sih)

#### 2. E-Insights (2020)
- **Penghargaan:** **Best E-Sports / Winning ESports/Gaming Team**, Wallifornia MusicTech & e-Sports 2020; penghargaan coaching empat jam dengan LeanSquare Accelerator. **Jenis:** category winner; juara umum acara ialah PianoTunesAR. **Bukti penyelenggara:** pemenang disebut langsung di landing page event. — [Wallifornia resmi di Devpost](https://wallifornia-hackathon-2020.devpost.com/)
- **Teknis:** dashboard komentar streaming, emotional index, rata-rata total dan moving average; Express/Node.js, Socket.IO dan pustaka `sentiment`. **Batas penting:** integrasi Twitter/Twitch bermasalah sehingga demo memakai live chat untuk **mensimulasikan feed**. — [Halaman proyek](https://devpost.com/software/e-insights)
- **Keyakinan:** tinggi untuk award dan prototipe, rendah untuk klaim kesiapan integrasi produksi. **Pelajaran:** demo perubahan sentimen dari waktu ke waktu lebih jelas daripada pie chart statis; beri label replay/simulasi jika API belum terhubung. — [Proyek](https://devpost.com/software/e-insights)

#### 3. Disaster Sentiment Analysis / Data Wizards (2022)
- **Penghargaan:** **SIT 1st Prize**, Joint Aston-SIT AI/ML Hackathon 2022. **Jenis:** site/institution prize, bukan juara umum global. Organizer gallery menandai proyek sebagai Winner; halaman proyek menyebut award persis. Event berlangsung 16–18 Mei 2022. — [Gallery penyelenggara](https://aston-sit-ai-ml-hackathon.devpost.com/project-gallery), [proyek dan award](https://devpost.com/software/disaster-sentiment-analysis), [jadwal event](https://aston-sit-ai-ml-hackathon.devpost.com/)
- **Teknis:** NLP dan scikit-learn untuk sentimen tweet/teks tentang bencana; Flask memuat model saat runtime sebagai aplikasi/REST API. Tidak ada metrik akurasi atau bukti disaster triage operasional di halaman. — [Proyek](https://devpost.com/software/disaster-sentiment-analysis)
- **Keyakinan:** tinggi untuk award; terbatas untuk kemampuan operasional. **Pelajaran:** sentiment dapat menjadi salah satu layer dashboard bantuan bencana; kebutuhan air/evakuasi dan urgensi harus mempunyai label terpisah, karena kalimat sedih belum tentu meminta pertolongan. Inferensi adaptasi, bukan fitur klaim pemenang.

#### 4. Clyde Chrome Extension (2021)
- **Penghargaan:** **Second Prize** pada Sentiment & Opinion Mining Natural Language API Hackathon (expert.ai), 2021. **Jenis:** peringkat kedua keseluruhan acara. Organizer gallery berlabel Winner dan halaman proyek menyebut Second Prize. — [Gallery penyelenggara](https://expertai-nlapi-042021.devpost.com/project-gallery), [proyek](https://devpost.com/software/clyde-chrome-extension)
- **Teknis:** ekstensi menganalisis konten terpilih lintas situs, screenshot hingga delapan, teks artikel dan transkrip YouTube; OCR AWS Textract, backend Python/Flask, expert.ai untuk keyphrases/sentiment/emotional traits, Chart.js. Kode publik tersedia. — [Proyek](https://devpost.com/software/clyde-chrome-extension), [repo tim](https://github.com/sarthakarora1208/clyde)
- **Keyakinan:** tinggi untuk award platform dan desain; tidak ada benchmark independen. **Pelajaran:** input dokumen/screenshot/transkrip yang pengguna berikan dapat menjadi MVP terkontrol sebelum integrasi API berbayar; simpan hubungan kalimat analisis dengan sumber. Inferensi adaptasi.

#### 5. Multilingual sentiment analyser (2021)
- **Penghargaan:** **Third Prize**, expert.ai Sentiment & Opinion Mining Natural Language API Hackathon 2021. **Jenis:** peringkat ketiga keseluruhan acara; gallery penyelenggara berlabel Winner dan proyek mencantumkan award. — [Gallery](https://expertai-nlapi-042021.devpost.com/project-gallery), [proyek](https://devpost.com/software/multilingual-review-analyser)
- **Teknis:** ulasan Amazon multi-bahasa (subset kitchen), terjemahan MarianMT ke Inggris, expert.ai untuk sentimen/entitas dan frasa positif/negatif, Elastic/BM25 untuk pencarian, Kibana dashboard, Python/React. Ulasan campuran ditampilkan lebih rinci daripada satu label polaritas. — [Proyek](https://devpost.com/software/multilingual-review-analyser)
- **Keyakinan:** tinggi untuk award/desain, terbatas untuk akurasi lintas bahasa. **Batas:** tim sendiri menyebut perlu studi pengguna dan penilaian kualitas terjemahan lebih lanjut; tidak membuktikan dukungan Jawa/Sunda atau domain TNI. **Pelajaran:** dashboard Indonesia dapat mempertahankan frasa asli dan aspek keluhan sambil mengevaluasi bahasa daerah terpisah. — [Proyek](https://devpost.com/software/multilingual-review-analyser)

#### 6. Echodex (2021)
- **Penghargaan:** **Best Project Identifying Sentiment of Brands, Companies, or Products**, expert.ai Sentiment & Opinion Mining Natural Language API Hackathon 2021. **Jenis:** category prize, bukan juara umum. Gallery penyelenggara berlabel Winner, proyek menyebut award. — [Gallery](https://expertai-nlapi-042021.devpost.com/project-gallery), [proyek](https://devpost.com/software/echodex)
- **Teknis:** agregasi berita, Reddit dan Twitter; NLP expert.ai untuk sentimen dan hubungan entitas, dashboard Streamlit, komponen pengambilan data/pemanggilan API/UI; membutuhkan API key expert.ai dan NewsAPI. Repo tim mengonfirmasi mekanisme. — [Repo primer](https://github.com/chaudhary1337/Echodex)
- **Keyakinan:** tinggi untuk award dan struktur proyek. **Batas:** deskripsi penulis mengklaim pandangan unbiased; tidak ditemukan bukti metodologi membuktikan bebas bias. **Pelajaran:** bandingkan narasi per sumber dan deduplikasi berita tersindikasi agar volume pemberitaan tidak disalahartikan sebagai jumlah opini unik. Inferensi adaptasi.

#### 7. News Report / NewsReport (2022)
- **Penghargaan:** **Honorable mention kategori Sentiment & Emotions**, Turn Language into Action: A Natural Language Hackathon for Good, expert.ai, pemenang diumumkan November 2022. **Jenis:** honorable mention kategori, bukan third place keseluruhan; blog menulis “3rd honorable mention: Sentiment & Emotions” sementara Devpost menulis “Honorable Mentions”. — [Pengumuman resmi expert.ai, 8 Desember 2022](https://content.expert.ai/blog/turning-language-into-action-results-from-a-natural-language-hackathon-for-positive-change/), [proyek](https://devpost.com/software/news-report-z2usko)
- **Teknis:** URL artikel menjadi report intensitas hate speech dan emotional language, menyorot kalimat terkait, riwayat untuk perbandingan situs; expert.ai, Python/Flask, Svelte, Docker dan Azure. — [Proyek](https://devpost.com/software/news-report-z2usko)
- **Keyakinan:** tinggi untuk award. **Batas prinsip:** klaim penulis bahwa intensitas marah/takut dapat menjadi petunjuk ketidakandalan tidak membuktikan benar/salahnya berita. Dalam adaptasi, tampilkan ini sebagai **framing/emotion indicator**, dan gunakan bukti fact-check terpisah; jangan memberi label hoaks dari sentimen.

#### 8. Bupa Australia / Team Blue Bricks — sentiment anomaly engine (2025)
- **Penghargaan:** **Second place / silver**, APJ Databricks Smart Business Insights Challenge 2025. **Jenis:** peringkat kedua keseluruhan kompetisi profesional, bukan mahasiswa. Hosted organizer page mengumumkan Bupa sebagai peraih silver; jadwal menyebut pengumuman pekan 23 Juni 2025. — [Halaman resmi event yang diselenggarakan Databricks](https://hackathon.stackup.dev/web/events/databricks-smart-business-insights-challenge)
- **Teknis:** engine anomaly real-time menandai emotional mismatch pada feedback; penjelasan tim menyebut perbedaan skor survei dengan nada percakapan, AI/BI dashboard dan Genie Spaces. Ringkasan mekanisme berasal dari tim/mitra primer, bukan kode publik. — [Penyelenggara](https://hackathon.stackup.dev/web/events/databricks-smart-business-insights-challenge), [anggota tim/mitra](https://au.linkedin.com/in/andrew-hutchings-hutchatronic)
- **Keyakinan:** tinggi untuk award dan fungsi umum; detail model dan evaluasi tidak tersedia. **Pelajaran:** ketidakcocokan rating dan isi keluhan dapat memprioritaskan review manual pada layanan publik/rumah sakit; tidak perlu menyimpulkan bahwa pengguna berbohong. Inferensi adaptasi.

### Inferences
- Pola yang dapat diadaptasi: temporal drift (E-Insights), kebutuhan saat bencana (Data Wizards), input multimodal terkontrol (Clyde), aspek dan multi-bahasa (Multilingual analyser), fusi narasi lintas sumber (Echodex), framing emosi (News Report), serta mismatch skor-vs-isi (Bupa). Pola ini adalah inspirasi desain; tidak ada bukti bahwa menyalin fitur akan menang di Kartika.
- Pemenang bukan harus model baru; menghubungkan NLP dengan keputusan pengguna, bukti sumber dan UI dapat membentuk demonstrasi yang jelas. Ini pembacaan kualitatif dari contoh, bukan estimasi sebab kemenangan.

### Gaps
- Halaman proyek adalah laporan pembuat; kecuali dinyatakan, tidak ada validasi independen, benchmark reproduksi, uji beban atau deployment produksi yang diperiksa.
- Penghargaan Clyde/Multilingual/Echodex diverifikasi melalui organizer gallery + metadata award platform; artikel pengumuman PR Newswire ditemukan tetapi berulang timeout, sehingga tidak dipakai untuk klaim tambahan.

## Komponen teknis apa yang layak diadaptasi ke Bahasa Indonesia?

### Takeaway
Gunakan model Bahasa Indonesia sebagai baseline yang dievaluasi, bukan penerjemahan otomatis sebagai satu-satunya sumber kebenaran. Pisahkan sentimen, emosi, urgensi, stance, dan kebenaran faktual.

### Cited Findings
- IndoBERTweet merupakan model pralatih Indonesian Twitter dari EMNLP 2021; repo resmi menyediakan direktori eksperimen sentiment, emotion, hate speech dan NER. Ini model dasar yang perlu fine-tuning/evaluasi untuk tugas spesifik, bukan classifier siap pakai yang dijamin cocok untuk TNI. — [Repo resmi](https://github.com/indolem/IndoBERTweet), [paper penulis](https://arxiv.org/abs/2109.04607)
- Panduan IndoBERTweet menjelaskan preprocessing lowercase, mention menjadi `@USER`, URL menjadi `HTTPURL`, dan emoticon ke teks. Data pralatih 2019–2020 tidak dirilis karena kebijakan Twitter; ketersediaan model tidak berarti tersedia izin data untuk scraping baru. — [Dokumentasi penulis](https://github.com/indolem/IndoBERTweet)
- IndoNLU menyediakan pretrained IndoBERT dan benchmark Indonesian NLU serta starter code. Repo resmi masih publik saat diakses. — [Repo resmi](https://github.com/IndoNLP/indonlu), [paper penulis](https://arxiv.org/abs/2009.05387)

### Inferences
- Pipeline MVP: input data berizin/unggahan → deduplikasi & hapus PII → identifikasi bahasa → klasifikasi aspek/entitas → head sentimen dan emosi → agregasi waktu/topik → tampilkan kutipan sumber dan confidence → review manusia. Pilih FastAPI/Flask + Postgres + frontend dashboard atau Streamlit sesuai kompetensi; ini usulan, bukan stack wajib lomba.
- Bangun dataset evaluasi lokal teranotasi ganda; split berdasarkan waktu dan thread agar balasan/duplikat tidak bocor train-test; laporkan macro-F1 per kelas serta false positive alert. Sarkasme, negasi, slang dan campur bahasa memerlukan subset uji tersendiri. Ini rekomendasi metode, tidak ada angka performa usulan yang telah diukur.
- Untuk prioritas bencana, tampilkan kartu “keluhan kebutuhan air bersih meningkat” beserta lokasi eksplisit dan kalimat bukti; jangan infer lokasi rumah penulis dari profil atau memberi individu skor risiko.

### Gaps
- Belum mengukur performa domain TNI/Indonesia untuk model-model di atas; semua target performa sebaiknya ditulis sebagai target, bukan hasil.
- Status lisensi model/dataset spesifik dan akses API per platform harus diperiksa saat implementasi; repo baseline bukan pemberian izin seluruh data.

## Klaim apa yang harus dihindari dan apa yang tidak masuk daftar utama?

### Takeaway
Kejujuran tentang jenis award, data demo, dan batas kemampuan lebih berharga daripada daftar winner panjang yang tidak terbukti. Sentimen negatif tidak sama dengan hoaks, ancaman keamanan, atau niat melanggar hukum.

### Cited Findings
- **Group Sentimental**, BCHacks 5.0 (Januari 2024), halaman Devpost mencantumkan Winner 2nd Place; mood journal lokal dengan browser storage. Tidak masuk delapan utama karena orientasi jurnal pribadi kurang cocok untuk social sentiment dashboard; halaman langsung berulang cache miss walaupun hasil pencarian menampilkan konten primer. — [Proyek](https://devpost.com/software/group-sentimental)
- **Realtime Analytics**, Symbl.ai 2021, organizer gallery Winner dan proyek menyebut **2nd Prize**; transcription/sentiment Zoom, manager dapat meninjau dan membantu call. Cadangan yang relevan untuk hotline consent-based; bukan mengklaim speech tone dapat mendiagnosis kondisi mental. — [Organizer gallery](https://symbl-ai-hackathon.devpost.com/project-gallery), [proyek](https://devpost.com/software/realtime-analytics)
- **Denoising Reviews With Mamba**, TikTok TechJam 2025, institusi NTU menyebut Second Place; tidak dimasukkan daftar utama karena riset teknis proyek belum dilanjutkan. Jangan mencampur dengan proyek tim Win One yang disebut di artikel tetapi tanpa penghargaan eksplisit. — [NTU](https://www.ntu.edu.sg/computing/news-events/news/detail/building-a-safer-digital-future--ccds-teams-shine-at-tiktok-techjam-hackathon-2025)

### Inferences
- TNI-use case yang masuk akal untuk winner patterns: OMSP/disaster situational awareness, evaluasi layanan/pengaduan, dan komunikasi publik yang transparan. Butuh sumber dari peneliti Indonesia/TNI untuk membuktikan masalah dan existing deployment; catatan ini tidak membuktikannya.
- Hindari klaim dashboard pendeteksi “provokator”, loyalitas, atau kebenaran berita hanya dari negatif/positif; semua itu melampaui keluaran yang didokumentasikan proyek di atas.

### Gaps
- Tidak meneliti database internal/rahasia TNI, menguji model, melakukan scraping akun pribadi, atau mengonfirmasi penggunaan pemenang di Indonesia. Bagian deployment Indonesia ditangani peneliti paralel.
