# PRD — SOPilot

**Konversi SOP → BPMN dengan co-pilot klarifikasi**
ANGEL Innovation Hackathon 2026 · Track Artificial Intelligence · Topik 1: *AI-Powered SOP to Executable Business Process*
Status: Draft v0.5 (feedback: judul langkah formal, poster timeline, tampilan HP digeser) · Diperbarui: 18 Okt 2026

---

## 1. Ringkasan & Konteks

SOPilot adalah aplikasi web yang membaca dokumen SOP dan mengubahnya menjadi **proses bisnis yang bisa dijalankan** (BPMN 2.0 executable). SOPilot **bertanya balik** kepada admin saat SOP ambigu atau tidak lengkap, dan jawabannya langsung memperbarui model. Model bisa diuji lewat **simulasi eksekusi** sebelum diekspor.

**Pengguna utama adalah admin/analis proses.** Dari model yang sama, SOPilot menurunkan panduan kerja yang mudah dibaca pekerja (poster cetak sebagai keluaran utama, tampilan HP menyusul) sebagai pembeda.

Tiga topik AI di booklet tampak membentuk satu alur: SOP → model proses (topik ini) → analisis proses (topik 2) → eksekusi lewat percakapan (topik 3). Topik ini menghasilkan model proses yang menjadi masukan topik lain. Ini inferensi dari judul topik dan perlu dikonfirmasi (O11).

Konteks program (dari booklet ANGEL Innovation Hackathon 2026):
- Industry Problem Owner topik ini: **PT Javan Cipta Solusi**.
- Syarat **Prototype Alpha**: menerima dokumen SOP/teks proses dan mendemonstrasikan ekstraksi sebagian elemen proses menjadi representasi BPMN/draft process model. Belum wajib menghasilkan BPMN 2.0 yang sepenuhnya valid atau deployable.
- Bobot penilaian proposal: Problem–Solution Fit 20%, Technical Relevance 22%, Innovation & Feasibility 28%, Research Downstreaming & Impact 20%, TKDN & IP 10%.
- Target akhir: functional prototype yang didemokan di Deeptech Hackathon / Demo Day (Desember 2026).

## 2. Problem Statement

SOP umumnya ditulis sebagai teks atau tabel: tidak bisa dianalisis, divisualisasikan konsisten, atau dieksekusi oleh sistem. Memodelkannya ke BPMN secara manual lambat dan butuh keahlian notasi. Teks SOP juga sering ambigu (pelaksana tidak disebut, cabang keputusan tidak lengkap, istilah kabur seperti "segera" atau "pihak terkait"), dan kekurangan ini baru ketahuan saat proses dimodelkan atau dijalankan. Akibatnya SOP tidak bisa langsung menjadi alur kerja yang berjalan di sistem; membangunnya dari nol butuh analis dan developer.

Yang terdampak: analis proses/konsultan yang memodelkan proses untuk klien, dan pemilik SOP yang tidak tahu SOP-nya punya celah. Biaya tidak menyelesaikannya: otomasi proses tertunda, SOP tidak konsisten dengan praktik, dan kesalahan ditemukan terlambat.

Dampak tambahan di lapangan: SOP berbentuk dokumen panjang atau diagram BPMN sulit dipahami pekerja, sehingga SOP tidak dipakai dan pekerjaan dilakukan berdasarkan kebiasaan.

> *Catatan bukti:* bukti kuantitatif (waktu pemodelan manual, frekuensi SOP ambigu) belum dikumpulkan. Lihat Open Questions O1–O2.

## 3. Goals

Target di bawah adalah **hipotesis awal** yang dikalibrasi setelah baseline diukur (lihat §10).

| # | Goal | Ukuran | Target hipotesis |
|---|---|---|---|
| G1 | Ekstraksi proses akurat | F1 elemen (task, event, gateway, aktor) pada set uji | ≥ 0,75 pada PET; ≥ 0,70 pada SOP Indonesia |
| G2 | Output standar & valid | % output lolos validasi struktur BPMN 2.0 (bpmnlint) tanpa error | ≥ 95% |
| G3 | Hemat waktu pemodelan | Waktu SOP → diagram final vs manual (uji dengan ≥ 3 analis) | turun ≥ 50% |
| G4 | Ambiguitas terdeteksi | Recall pada ambiguitas yang diberi label manual | ≥ 80% |
| G5 | Pertanyaan relevan | % pertanyaan klarifikasi yang dinilai pengguna "berguna" | ≥ 70% |
| G6 | Mudah dipahami pekerja | % pekerja uji yang menjelaskan tugasnya dengan benar setelah membaca daftar langkah, tanpa bantuan | ≥ 80% |
| G7 | Langkah singkat dan jelas | % langkah dengan judul ≤ 4 kata dan keterangan ≤ 12 kata, diawali kata kerja | ≥ 90% |
| G8 | Siap dijalankan | % SOP uji yang berjalan dari awal sampai Selesai di simulator tanpa edit manual, setelah klarifikasi dijawab | ≥ 80% |

## 4. Non-Goals (Fase 1)

1. **Deploy ke engine produksi dan integrasi sistem klien** (Camunda/Flowable di lingkungan klien, form dan notifikasi nyata) — Fase 1 cukup simulasi eksekusi di aplikasi (R27).
2. **Repositori & relasi antar-SOP** — nilai besar tapi butuh model data dan pencarian tersendiri.
3. **Auditor kualitas SOP penuh** (skor ISO, deteksi loop/deadlock mendalam) — hanya cek dasar yang menopang klarifikasi.
4. **Elemen BPMN lanjutan**: timer, message flow antar-pool, sub-proses, boundary event, compensation.
5. **Kolaborasi multi-pengguna real-time** dan manajemen akun/organisasi lengkap.
6. **Fine-tuning model sendiri** — Fase 1 memakai LLM yang sudah ada.
7. **Fitur suara (langkah dibacakan)** — berguna, tetapi butuh TTS berbahasa Indonesia; masuk P2.

## 5. Persona & User Stories

**Persona**
- **Admin/Analis Proses (pengguna utama)** — business analyst atau supervisor; ingin model proses yang bisa dijalankan dengan cepat dan benar; paham BPMN.
- **Pekerja (pembaca panduan)** — pekerja lapangan berpenghasilan rendah; HP Android sederhana; membaca singkat; butuh bahasa sehari-hari, ikon, dan huruf besar.
- **Pemilik SOP (penjawab klarifikasi)** — staf non-teknis di unit kerja; tidak paham BPMN; paham isi SOP.
- **Developer Integrator (sekunder)** — mengambil keluaran BPMN/JSON untuk sistem lain.

**User stories** (urut prioritas)

*Analis Proses*
- US1. Sebagai analis, saya ingin mengunggah SOP (PDF/DOCX/teks) dan mendapat draf model BPMN yang bisa dijalankan, agar tidak menggambar dari nol.
- US2. Sebagai analis, saya ingin klik elemen diagram dan melihat kalimat asalnya di SOP, agar bisa memverifikasi hasil AI dengan cepat.
- US3. Sebagai analis, saya ingin melihat daftar bagian SOP yang ambigu beserta pertanyaannya, agar tidak ada asumsi tersembunyi.
- US4. Sebagai analis, saya ingin mengubah diagram secara manual dan lewat perintah chat, agar revisi cepat.
- US5. Sebagai analis, saya ingin mengekspor `.bpmn` executable dan gambar, agar bisa dipakai di tool lain (mis. Camunda Modeler).
- US15. Sebagai analis, saya ingin menjalankan simulasi proses dari awal sampai selesai, agar tahu model sudah benar sebelum dipakai.
- US16. Sebagai analis, saya ingin melihat tugas berpindah antar-peran beserta isian formnya, agar yakin pembagian tugas sudah tepat.
- US17. Sebagai analis, saya ingin simulasi berhenti dan menunjukkan bagian yang belum jelas, agar tahu apa yang harus diklarifikasi.

*Pemilik SOP*
- US6. Sebagai pemilik SOP, saya ingin menjawab pertanyaan klarifikasi dengan bahasa biasa (tanpa istilah BPMN), agar SOP saya jadi lengkap.
- US7. Sebagai pemilik SOP, saya ingin melihat teks SOP yang sudah direvisi dari jawaban saya, agar dokumen sumber ikut diperbaiki.

*Developer Integrator*
- US8. Sebagai developer, saya ingin mendapat JSON perantara bersama file BPMN, agar mudah diintegrasikan.

*Pekerja (tambahan v0.2)*
- US9. Sebagai pekerja, saya ingin memilih bagian saya dan hanya melihat tugas saya, agar tidak bingung dengan langkah orang lain.
- US10. Sebagai pekerja, saya ingin membaca daftar langkah bergambar dengan kalimat pendek, agar langsung paham apa yang harus dikerjakan.
- US11. Sebagai pekerja, saya ingin melihat jalur Ya dan Tidak tertulis jelas pada tiap keputusan, agar tidak salah jalur.
- US12. (P2) Sebagai pekerja, saya ingin mencentang langkah yang sudah selesai, agar tidak ada yang terlewat.
- US13. Sebagai pekerja, saya ingin melaporkan langkah yang tidak sesuai kenyataan lewat HP, agar SOP diperbaiki.
- US14. Sebagai pekerja, saya ingin poster cetak dengan QR code di tempat kerja, agar panduan selalu terlihat tanpa membuka HP.

*Kasus tepi*: dokumen bukan SOP; scan buram; SOP sangat panjang (> 20 halaman); SOP berformat tabel; SOP dua bahasa (Indonesia–Inggris); SOP tanpa percabangan sama sekali; LLM tidak merespons.

## 6. Requirements

### P0 — Wajib untuk Alpha / Demo Day

**R1. Unggah & parsing dokumen**
Menerima PDF (berteks), DOCX, dan teks tempel; membaca isi menjadi blok teks bernomor beserta posisinya.
- [ ] Given PDF/DOCX valid ≤ 20 hlm, When diunggah, Then teks terekstrak dan ditampilkan di panel kiri dalam ≤ 10 detik.
- [ ] Given file tidak didukung atau korup, Then muncul pesan error yang jelas, tanpa crash.
- [ ] Given dokumen jelas bukan SOP, Then sistem memberi peringatan dan tetap mengizinkan lanjut.

**R2. Ekstraksi ke representasi perantara (JSON)**
LLM mengisi JSON terstruktur: `lanes`, `tasks`, `events`, `gateways`, `flows`, masing-masing dengan `source_span` (rujukan ke teks asal).
- [ ] Output JSON tervalidasi skema; bila gagal, sistem mengulang otomatis maksimal 2 kali, lalu menampilkan error.
- [ ] Setiap elemen punya minimal satu `source_span` yang valid.
- [ ] Mendukung start event, end event, task, gateway eksklusif, dan lane.

**R3. Pembangkit BPMN 2.0 deterministik**
Kode biasa (bukan LLM) mengubah JSON menjadi XML BPMN 2.0 + tata letak otomatis.
- [ ] Input JSON yang sama selalu menghasilkan XML yang sama.
- [ ] XML terbuka tanpa error di editor bpmn-js dan Camunda Modeler.
- [ ] Diagram tampil dengan lane, tanpa elemen bertumpuk.

**R4. Penampil & editor diagram**
Diagram interaktif di browser; pengguna bisa menambah/menghapus/mengubah elemen secara manual.
- [ ] Perubahan manual tersimpan dan ikut diekspor.

**R5. Jejak ke teks sumber (traceability)**
- [ ] Klik elemen di diagram → `source_span` tersorot di panel SOP, dan sebaliknya.
- [ ] Elemen tanpa sumber (hasil edit manual) diberi penanda.

**R6. Deteksi ambiguitas & pertanyaan klarifikasi**
Aturan deterministik pada JSON menghasilkan daftar masalah; LLM menyusun pertanyaan dalam bahasa natural.
Aturan minimum: tugas tanpa pelaksana; gateway dengan < 2 cabang keluar; elemen tidak terhubung; tidak ada end event; kata kabur dari daftar (mis. "segera", "pihak terkait", "dll").
- [ ] Setiap masalah tampil sebagai penanda di diagram dan di daftar, lengkap dengan pertanyaan.
- [ ] Pengguna dapat menandai masalah sebagai "abaikan".
- [ ] Pada SOP uji yang memang ambigu, recall ≥ target G4.

**R7. Revisi lewat jawaban/chat**
Jawaban pengguna diubah LLM menjadi **operasi patch** (tambah/ubah/hapus) pada JSON, lalu diagram dibangkitkan ulang.
- [ ] Given pertanyaan terbuka, When pengguna menjawab, Then diagram berubah dan masalah terkait hilang dari daftar.
- [ ] Patch yang menghasilkan JSON tidak valid ditolak dan diagram tidak berubah.
- [ ] Ada tombol *undo* untuk satu langkah revisi.

**R8. Validasi**
- [ ] bpmnlint dijalankan pada setiap pembangkitan; temuan error/warning ditampilkan.
- [ ] Ekspor diblokir jika ada error struktur, dengan opsi "ekspor tetap" yang eksplisit.

**R9. Ekspor**
- [ ] Unduh `.bpmn` (BPMN 2.0 executable), PNG/SVG, dan JSON perantara.

**R10. Lapisan LLM agnostik**
Semua panggilan LLM melalui satu antarmuka adapter; penyedia dan model diatur lewat konfigurasi.
- [ ] Mengganti penyedia/model cukup lewat konfigurasi, tanpa mengubah kode pipeline.
- [ ] Minimal dua adapter berfungsi: satu API cloud dan satu model lokal (mis. via Ollama).
- [ ] Prompt dan skema output terpisah dari adapter.

**R25. Model executable.** JSON perantara memuat yang dibutuhkan agar proses bisa dijalankan: jenis tugas (tugas manusia atau otomatis), peran → grup pelaksana (`candidateGroups`), variabel dan kondisi tiap cabang keputusan, dan isian form per tugas.
- [ ] Setiap tugas punya jenis dan pelaksana; tugas tanpa pelaksana ditandai belum siap.
- [ ] Setiap keputusan punya variabel dan kondisi untuk jalur Ya dan Tidak.
- [ ] Isian form per tugas diusulkan LLM dari teks SOP dan bisa diedit admin.

**R26. Generator BPMN executable.** Kode deterministik menghasilkan `isExecutable="true"`, `userTask` dengan `candidateGroups`, `conditionExpression` pada alur keluar gateway, dan form properties.
- [ ] Ada pemeriksaan "Siap dijalankan": semua tugas punya pelaksana, semua keputusan punya jalur Ya dan Tidak, semua alur berakhir di end event, semua tugas punya isian form.
- [ ] XML terbuka tanpa error di Camunda Modeler; deploy ke engine nyata diuji di tahap pasca-hackathon.

**R27. Simulasi eksekusi.** Tombol Jalankan menjalankan model langkah demi langkah di dalam aplikasi.
- [ ] Langkah aktif dan yang sudah selesai disorot di diagram.
- [ ] Setiap tugas tampil untuk peran pelaksananya dengan isian form dan tombol selesai.
- [ ] Pada keputusan, admin memilih Ya atau Tidak dan simulasi mengikuti jalurnya.
- [ ] Bila model belum siap (mis. tugas tanpa pelaksana), simulasi berhenti dan menunjukkan bagian yang harus diklarifikasi.
- [ ] Log eksekusi (urutan, peran, tugas) bisa dilihat dan diekspor sebagai bahan analisis proses.

### P1 — Poster dan panduan untuk pekerja (pembeda)

R19, R21, R23 berstatus P1. R18 (tampilan HP), R20, R22, dan R24 berstatus P2: tampilan HP pekerja digeser ke belakang, sedangkan poster cetak menjadi keluaran utama untuk pekerja.

**R18 (P2). Tampilan HP pekerja = poster di HP.** Daftar langkah statis dengan komponen yang sama dengan poster A4: nomor, kalimat sederhana, chip pelaksana (warna + ikon + nama), ikon tindakan, dan petunjuk serah-terima. Tanpa tombol di dalam daftar; hanya satu pilihan bagian di atas dan satu tombol laporan di bawah.
- [ ] Huruf dasar ≥ 17px, tombol ≥ 48px, nyaman di lebar layar 360px.
- [ ] Peran tidak pernah dibedakan hanya oleh warna.
- [ ] Keputusan ditulis statis sebagai kotak pertanyaan: "Ya → Lanjut ke langkah N" dan "Tidak → …".
- [ ] Bagian yang belum diklarifikasi diberi label "Masih dikonfirmasi admin".
- [ ] Tidak ada istilah teknis (BPMN, gateway, lane) di layar pekerja.

**R19 (P1). Tampilan per peran.**
- [ ] Poster (dan tampilan HP) dapat dibuat untuk satu peran; langkah peran itu tampil penuh, langkah peran lain diringkas satu baris.

**R23 (P1). Penyederhanaan bahasa dan cek keterbacaan.** LLM menyusun tiap langkah menjadi **judul formal singkat** (≤ 4 kata, diawali kata kerja, mis. "Verifikasi Kelengkapan Dokumen") dan **keterangan satu kalimat** (≤ 12 kata); istilah sulit dijelaskan singkat di bawah keterangan ("Artinya …").
- [ ] Judul dan keterangan yang sama dipakai di diagram, simulasi, poster, tampilan HP, dan XML.
- [ ] Keterangan > 12 kata ditandai di tab Pemeriksaan dengan tombol "Sederhanakan".
- [ ] Penjelasan istilah tampil langsung di bawah kalimat, tanpa perlu diketuk.

**R24 (P2). Bagikan tanpa akun.** Tautan dan QR code; pekerja membuka tanpa login atau pasang aplikasi; tersedia tombol kirim lewat WhatsApp.
- [ ] Halaman pekerja terbuka dan terbaca di ponsel Android dengan koneksi lambat (halaman ringan, tanpa pustaka berat).

**R20 (P2). Mode kerja (checklist), diturunkan karena menambah kerumitan di layar pekerja.**
- [ ] Pekerja mencentang langkah yang selesai; progres "N dari M langkah selesai" tampil.
- [ ] Setelah semua langkah selesai tampil penanda selesai.

**R21 (P1). Poster A4 dengan QR code.**
- [ ] Poster berisi judul, legenda peran, langkah ringkas berikon, keputusan Ya/Tidak, versi, dan tanggal berlaku.
- [ ] Bisa dibuat untuk semua peran atau satu peran, dan diekspor ke PDF.
- [ ] Tata letak timeline vertikal: nomor langkah tersambung garis, judul tegas, keterangan dan petunjuk serah-terima berukuran kecil, pelaksana rata di kolom kanan, keputusan ditandai belah ketupat dengan jalur Ya/Tidak.

**R22 (P2). Masukan pekerja.**
- [ ] Satu tombol "Ada yang salah? Laporkan ke admin" di bawah daftar membuka lembar singkat: pilih langkah, pilih alasan, teks opsional.
- [ ] Masukan muncul di tab Masukan admin dan bisa ditandai sudah ditangani.

### P1 — Sebaiknya ada (Demo Day jika waktu cukup)
- **R11.** OCR untuk SOP hasil scan.
- **R12.** SOP berformat tabel/flowchart tekstual, termasuk format SOP administrasi pemerintahan (Permenpan RB 35/2012).
- **R13.** Gateway paralel dan loop dasar.
- **R14.** Skor kelengkapan SOP (0–100) dari hasil validasi dan ambiguitas.
- **R15.** Ekspor teks SOP yang sudah direvisi (DOCX).
- **R16.** Tautan klarifikasi terpisah untuk pemilik SOP (halaman jawab-pertanyaan tanpa tampilan diagram).
- **R17.** Mode privasi: tanpa penyimpanan dokumen di server setelah sesi selesai.

### P2 — Pertimbangan masa depan (dirancang agar tidak terhalang)
- Deploy ke engine nyata (Flowable/Camunda) dengan form tugas yang berfungsi untuk pekerja.
- Kirim log eksekusi ke analisis proses (topik 2) dan jalankan proses lewat percakapan (topik 3).
- Auditor kualitas SOP, repositori & relasi antar-SOP, versi.
- API/plugin (Word/Google Docs, Camunda Modeler).
- BPMN → SOP (arah sebaliknya), dukungan DMN untuk aturan keputusan.
- **Fitur suara**: langkah dibacakan untuk pekerja yang kurang nyaman membaca.
- Bahasa daerah dan mode offline untuk lokasi dengan sinyal buruk.

## 7. Arsitektur Ringkas

```
Frontend : Next.js + bpmn-js (editor), panel SOP (PDF/teks), panel chat/klarifikasi
Backend  : FastAPI (Python)
  1. Parser     → PyMuPDF / python-docx (P1: OCR)
  2. Extractor  → LLM (via adapter) → JSON perantara + source_span (peran, kondisi keputusan, isian form)
  3. Checker    → aturan deterministik → masalah → LLM menyusun pertanyaan
  4. Patcher    → jawaban pengguna → operasi patch pada JSON
  5. Generator  → JSON → BPMN XML executable (deterministik: userTask, candidateGroups, conditionExpression) → bpmn-auto-layout → bpmnlint
  6. Simplifier → LLM menyusun judul formal (≤ 4 kata) dan keterangan (≤ 12 kata) tiap langkah, serta penjelasan istilah sulit
  7. Worker View → JSON yang sama → poster A4 timeline vertikal + QR; tampilan HP (P2) memakai komponen yang sama
  8. Simulator  → menjalankan model langkah demi langkah di aplikasi; menghasilkan log eksekusi
LLM Adapter : antarmuka tunggal; implementasi cloud & lokal
```

Prinsip desain:
- **LLM tidak menulis XML.** Ia hanya mengisi/memperbarui JSON; XML dibangkitkan kode biasa agar valid dan dapat diulang.
- **Setiap elemen membawa jejak sumber**, dasar fitur traceability dan verifikasi.
- **Penyedia LLM bisa diganti**; model lokal mendukung kebutuhan data tidak keluar dari server dan nilai TKDN.
- **Model BPMN executable adalah sumber kebenaran.** Simulasi, tampilan pekerja, dan poster diturunkan dari JSON yang sama, jadi tidak pernah menyimpang dari diagram.
- **Ringan untuk HP sederhana.** Halaman pekerja tanpa pustaka berat dan memakai ikon SVG.

## 8. Pembeda

- **SOP langsung bisa dijalankan dan diuji** lewat simulasi, bukan hanya digambar.
- Mendukung **Bahasa Indonesia** dan (P1) format SOP lokal.
- **Bertanya balik** saat SOP ambigu, bukan menebak.
- **Traceability** elemen ↔ kalimat sumber.
- **Keluaran untuk pekerja**, bukan hanya diagram: poster cetak bertata letak timeline, tampilan per peran, dan tampilan HP (menyusul).
- **Agnostik terhadap LLM**, termasuk model lokal untuk skenario on-premise.
- Pembanding yang perlu dikaji: fitur pemodelan berbantuan AI di Camunda dan SAP Signavio (lihat O6).

## 9. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| LLM berhalusinasi elemen/alur | Diagram salah | Jejak sumber wajib; validasi aturan; pengguna memverifikasi |
| JSON/patch dari LLM tidak valid | Pipeline gagal | Skema ketat, retry terbatas, tolak patch tidak valid |
| Tata letak diagram berantakan | Sulit dibaca | bpmn-auto-layout; editor manual |
| SOP kompleks/panjang | Akurasi turun | Batasi lingkup Fase 1; pemrosesan per bagian |
| Kualitas model lokal lebih rendah | Akurasi turun di mode on-prem | Ukur per model; tampilkan peringatan; cloud sebagai default |
| Privasi dokumen klien | Penolakan adopsi | Opsi model lokal; mode tanpa simpan (R17) |
| Data uji Indonesia terbatas | Evaluasi lemah | Anotasi sendiri 20–30 SOP publik (O3) |

## 10. Success Metrics

**Leading (diukur saat Alpha → Demo Day)**
- F1 ekstraksi (G1), validitas BPMN (G2), recall ambiguitas (G4), relevansi pertanyaan (G5), kesiapan dijalankan (G8).
- Waktu SOP → diagram pertama (target ≤ 60 detik untuk SOP ≤ 10 hlm).
- Jumlah putaran klarifikasi sampai masalah terselesaikan.

**Lagging (Jan–Apr 2027, fase post-hackathon)**
- Waktu pemodelan nyata vs manual pada SOP milik mitra (G3).
- Jumlah pilot/uji coba bersama mitra industri.
- Kesiapan TKT dan IP.

**Metode ukur**
- Set uji: **PET** (*Process Extraction from Text*, berbahasa Inggris) untuk pembanding publik, ditambah 20–30 SOP Indonesia dari sumber publik (mis. situs JDIH pemda) yang dianotasi sendiri sebagai gold set.
- Uji waktu: ≥ 3 analis memodelkan 3 SOP, manual vs SOPilot.
- Uji eksekusi (G8): tiap SOP uji dijalankan di simulator; berhasil bila mencapai Selesai tanpa edit manual setelah klarifikasi dijawab.
- Uji pemahaman (G6): ≥ 5 pekerja membaca daftar langkah, lalu menjelaskan tugasnya; admin menilai benar atau salah.
- Keterbacaan (G7): dihitung otomatis dari jumlah kata dan kata pertama tiap langkah.
- Evaluasi diulang untuk tiap kombinasi model LLM yang didukung.

## 11. Open Questions

| # | Pertanyaan | Pemilik jawaban | Sifat |
|---|---|---|---|
| O1 | Format & karakter SOP yang umum dipakai calon pengguna (teks, tabel, flowchart, scan)? | Javan (Problem Owner Clinic) | **Blocking** untuk prioritas R11/R12 |
| O2 | Berapa waktu pemodelan manual SOP rata-rata hari ini (baseline G3)? | Javan | Non-blocking |
| O3 | Bisakah mendapat contoh SOP nyata (dianonimkan) untuk gold set? | Javan | **Blocking** untuk evaluasi realistis |
| O4 | Engine eksekusi target serta mekanisme tugas dan form yang dipakai Javan (Camunda, Flowable, lainnya)? | Javan / tim teknis | **Blocking** untuk tahap engine nyata |
| O5 | Kebijakan data: boleh dokumen dikirim ke API LLM cloud? | Javan | **Blocking** untuk memilih default adapter |
| O6 | Seberapa jauh fitur AI di Camunda/Signavio sudah mencakup SOP berbahasa Indonesia? | Tim (riset) | Non-blocking |
| O7 | Model LLM mana (cloud & lokal) yang dibandingkan, dan bagaimana anggarannya? | Tim teknis | Non-blocking |
| O8 | Apa indikator keberhasilan akhir yang dirumuskan Problem Owner di Product Requirement Specification (PRS)? | Javan | **Blocking** untuk finalisasi PRD |
| O9 | Pekerja yang dituju: tingkat literasi, bahasa sehari-hari, serta perangkat dan koneksi yang mereka punya? | Javan / mitra pengguna | **Blocking** untuk ukuran huruf, bahasa, dan pilihan offline |
| O10 | Apakah poster cetak dan tautan WhatsApp cukup, atau perlu kanal lain (layar di tempat kerja, kiosk)? | Javan | Non-blocking |
| O11 | Apakah benar ada alur topik 1 → 2 → 3 (model proses jadi masukan analisis dan eksekusi), dan format model/log apa yang diharapkan antar-topik? | Javan | **Blocking** untuk bentuk keluaran |

## 12. Timeline (mengikuti Program Journey booklet)

| Periode | Tahap | Fokus SOPilot |
|---|---|---|
| Okt 2026 | Problem Validation Bootcamp, Problem Owner Clinic | Jawab O1–O3, O5, O8; finalisasi PRD → PRS |
| Okt–Nov | Prototype Alpha Refinement | R1–R3, R5, R25 (ekstraksi + diagram + traceability + model executable) |
| Nov | Prototype Readiness Review (Go/No-Go) | R4, R6–R8, R26, R27 berfungsi; evaluasi awal G1–G2, G8 |
| Des | Strategic Innovation Workshop → Deeptech Hackathon → Demo Day | R9–R10 + fitur pekerja (P1) terpilih; evaluasi lengkap; skrip demo |
| Jan–Apr 2027 | Post-Hackathon Acceleration | Validasi teknologi, TKT/TKDN, IP, business matching; mulai P2 |

> Catatan jadwal: booklet menyebut pendaftaran 18 Sep–2 Okt 2026. Pastikan status pendaftaran tim sebelum menjadikan timeline ini mengikat.

## 13. Alur Demo (±3 menit)

1. Unggah SOP berbahasa Indonesia.
2. Diagram lengkap dengan lane muncul; arahkan kursor ke satu tugas → kalimat sumber tersorot.
3. Tampilkan 3 penanda ambiguitas beserta pertanyaannya.
4. Jawab satu pertanyaan lewat chat → diagram berubah, skor/masalah berkurang.
5. Klik **Jalankan**: proses berjalan langkah demi langkah, tugas muncul per peran, dan simulasi berhenti bila ada bagian yang belum jelas.
6. Ekspor `.bpmn` executable dan buka di Camunda Modeler untuk membuktikan kepatuhan standar.
7. Tunjukkan poster A4 (timeline vertikal) dengan QR code, termasuk versi per peran.
8. Opsional: buka tampilan HP pekerja, kirim masukan, dan lihat masukan itu muncul di admin.
9. Ganti penyedia LLM lewat konfigurasi untuk menunjukkan sifat agnostik.
