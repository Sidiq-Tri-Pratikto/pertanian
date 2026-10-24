# UX berbasis tugas dan aksesibilitas HematDaya

## 1. Bagaimana tiga tab mendukung tugas inti tanpa membebani pengguna dengan pengaturan?

### Takeaway

Jadikan Beranda tempat menjawab “berapa energi yang tercatat, apa cakupannya, dan perangkat mana yang terbesar”; Perangkat tempat memeriksa sumber dan riwayat; Saran tempat menilai bukti perubahan. Pengaturan jadwal, produksi, dan integrasi cukup muncul ketika dibutuhkan, sedangkan keterbatasan cakupan dan kualitas harus tetap dekat dengan angka yang ditafsirkan. Ini rekomendasi desain berdasarkan PRD, belum temuan uji pengguna. [PRD §7–8, §14](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Cited Findings

- Artikel asli Jakob Nielsen menjelaskan progressive disclosure sebagai menempatkan pilihan utama terlebih dahulu dan pilihan khusus pada tampilan berikutnya. Pembagian harus mengikuti kebutuhan tugas; kontrol menuju informasi berikutnya harus terlihat dan berlabel jelas. Ini panduan desain, bukan bukti efektivitas khusus HematDaya. [NNGroup, Progressive Disclosure, 3 Desember 2006](https://www.nngroup.com/articles/progressive-disclosure/)
- GOV.UK menggunakan ringkasan kesalahan bersama pesan di dekat isian yang bermasalah, memindahkan fokus ke ringkasan, dan menautkan tiap pesan ke isian terkait; kata-kata pada keduanya harus konsisten. Pola ini dapat diadaptasi untuk impor, tetapi bukan standar format CSV. [GOV.UK Error summary](https://design-system.service.gov.uk/components/error-summary/)
- PRD mewajibkan tiga tujuan utama berlabel Indonesia; sumber/estimasi/kesegaran/cakupan yang memengaruhi interpretasi terlihat; retry dan back mempertahankan input. Impor memerlukan preview sebelum commit, hitungan baris diterima/dilewati/duplikat/konflik, commit atomik dan aman diulang. [PRD FR-06, UX-01–06](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Inferences

Rekomendasi berikut merupakan persyaratan handoff untuk prototipe dan implementasi, bukan hasil penelitian terukur. Dasarnya adalah hierarki tugas PRD dan disclosure yang berlabel jelas. [PRD §7–8](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md), [NNGroup](https://www.nngroup.com/articles/progressive-disclosure/)

- **Beranda:** urutan baca: periode + cakupan → energi tercatat dalam kWh → estimasi biaya jika tarif tersedia → cakupan/kesegaran → kontributor terbesar → satu observasi berbukti. Gunakan judul “Energi yang dipantau” dan “Estimasi biaya energi terpantau”. “Hanya mencakup sumber yang dipilih” harus dapat ditemukan tanpa membuka pengaturan. Tidak perlu kartu produksi kosong atau kartu status setiap integrasi.
- **Perangkat:** daftar nama aset, jenis cakupan (perangkat/grup/sirkuit), kWh pada periode yang sama, dan kualitas. Seluruh baris dapat membuka detail; tindakan kecil bersebelahan harus tetap memiliki target sendiri. Detail menampilkan riwayat, asal sumber, periode, kualitas, dan saran terkait. Nama panjang boleh membungkus; nama lengkap tersedia pada detail.
- **Saran:** setiap item menyatakan observasi dan periode pembanding, bukan vonis “boros”. Detail menjawab apa yang berubah, besarnya perubahan, bukti, kualitas, dan hal yang belum diketahui. “Penyebab perubahan belum diketahui” tetap eksplisit; umpan balik “Bermanfaat”, “Tidak relevan”, “Sembunyikan”, serta pemulihan saran tidak mengubah pengukuran.
- **Pengungkapan bertahap:** jadwal, profil penggunaan, dan energi per unit output menjadi pengaturan opsional di detail/pengaturan. Jangan menyembunyikan tarif yang hilang, data parsial, konflik pengukuran, atau batas cakupan di balik disclosure karena informasi itu mengubah arti angka saat ini. Tombol seperti “Lihat dasar perhitungan” lebih konkret daripada “Selengkapnya”.
- **Navigasi:** tiga tab tetap berlabel Beranda/Perangkat/Saran; pilihan aktif dikenali selain warna. Detail menggunakan back yang mempertahankan periode dan cakupan. Prototipe web boleh menggunakan pola navigasi web, tetapi harus menjelaskan bahwa itu representasi alur mobile. Mengubah ukuran browser bukan bukti aplikasi native berjalan.
- **Kosong:** prioritaskan “Impor data” dan sediakan “Coba demo”; demo membawa “Demo · Data simulasi”. Pengguna dapat melewati konteks, jadwal, produksi, tarif, akun perangkat, dan izin notifikasi untuk mencoba manfaat inti sesuai batas data demo/CSV. Tidak ada tombol mematikan listrik atau klaim integrasi yang belum diverifikasi.

Alur impor konkret: **pilih/paste berkas → konfirmasi semantik dan pemetaan → periksa preview → konfirmasi impor → hasil**. Beri satu tindakan utama per langkah; langkah pengaturan bukan wizard wajib bagi pembacaan demo. Saat preview bermasalah, sediakan ringkasan yang dapat difokuskan dan rincian lokasi kesalahan. [PRD FR-06, §10, UX-02/05/11](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md), [GOV.UK Error summary](https://design-system.service.gov.uk/components/error-summary/)

| Keadaan | Informasi dan tindakan yang harus ada |
|---|---|
| Belum diproses | Nama berkas, format contoh, batas ukuran/baris, unit, zona waktu, makna timestamp/interval; pemetaan sumber ke aset dan cakupannya. |
| Preview valid | Jumlah diterima, dilewati, duplikat tepat, konflik; periode, nama sumber, unit/interval, zona waktu dan asumsi cadence; satu tombol konfirmasi. |
| Sebagian invalid | Lokasi baris/kolom, nilai bermasalah dan koreksi konkret, misalnya “Baris data 7, energy_wh: gunakan angka 0 atau lebih”. Jelaskan apakah nomor merujuk baris data atau baris berkas; jangan menebak nomor berkas jika parser tidak memilikinya. |
| Ambang invalid | Contoh PRD: 2 dari 10 baris nonkosong invalid → boleh mengonfirmasi 8 baris valid unik; 3 dari 10 → commit ditolak. Rincian harus sesuai hasil parser; konflik tidak boleh dilabeli duplikat tepat. |
| Gagal jaringan/commit | Pesan “Impor belum dikonfirmasi” atau status hasil aktual, input/pemetaan dipertahankan, tombol coba lagi; jangan memberi toast sukses sebelum hasil diketahui. Retry harus menghasilkan satu hasil impor. |
| Batal/perbaiki | Kembali ke berkas/pemetaan tanpa menghapus data tersimpan sebelumnya; tindakan mengganti berkas jelas. |

Tabel di atas menerapkan kontrak PRD, bukan ketentuan GOV.UK tentang ambang invalid atau idempotensi. Tidak menambahkan fitur editor spreadsheet di dalam aplikasi. [PRD FR-06, §10, AT-29–34/40](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Gaps

- Belum diketahui apakah istilah “cakupan”, “sirkuit”, dan “energi terpantau” dipahami tiap segmen. Uji dengan contoh rumah dan usaha secara terpisah; jangan menyatakan tiga tab sudah intuitif.
- Tidak ada prototipe yang diperiksa dalam riset ini. Tidak ada bukti focus management, retry, parsing, atau pemeliharaan input benar-benar berfungsi.

## 2. Apa batas aksesibilitas dan penyajian grafik yang harus diterjemahkan menjadi acceptance criteria?

### Takeaway

Pisahkan standar web, panduan platform, dan target produk yang lebih ketat. “48” bukan minimum WCAG; screenshot juga tidak membuktikan label pembaca layar, ukuran target aktual, fokus, ataupun perilaku pembesaran. [WCAG 2.2](https://www.w3.org/TR/WCAG22/), [Android accessibility](https://developer.android.com/guide/topics/ui/accessibility/apps)

### Cited Findings

Ringkasan persyaratan web dari WCAG 2.2 berikut sengaja dibatasi pada kriteria yang paling relevan; ini bukan daftar lengkap kepatuhan:

| Kriteria | Batas standar |
|---|---|
| 2.5.8 AA | Target 24×24 CSS px; ada pengecualian, termasuk jarak, ekuivalen, inline, kontrol browser, dan kebutuhan esensial. |
| 1.4.3 AA | Teks 4,5:1; teks besar 3:1, dengan pengecualian. |
| 1.4.11 AA | Informasi visual kontrol dan bagian grafik yang diperlukan: 3:1 terhadap warna bersebelahan, dengan pengecualian. |
| 1.4.4 AA | Teks dapat diperbesar hingga 200% tanpa kehilangan isi/fungsi. |
| 1.4.10 AA | Reflow pada lebar 320 CSS px untuk konten vertikal; pengecualian bagian yang memerlukan dua dimensi. |
| 1.4.1 A | Warna bukan satu-satunya pembeda. |
| 2.1.1/2.1.2 A | Fungsi melalui keyboard; tanpa jebakan keyboard. |
| 2.4.7/2.4.11 AA | Fokus terlihat; elemen terfokus tidak sepenuhnya tertutup konten buatan pengembang. |
| 3.3.1 A / 3.3.3 AA | Identifikasi kesalahan dengan teks; sarankan koreksi yang diketahui. |
| 4.1.2 A / 4.1.3 AA | Nama/peran/status terprogram; status pesan tersedia bagi teknologi bantu tanpa memindahkan fokus. |

Sumber normatif seluruh tabel: [WCAG 2.2, SC terkait](https://www.w3.org/TR/WCAG22/).

- Android merekomendasikan target sentuh setidaknya 48×48 **dp**, dan label yang menyampaikan tujuan kontrol. Ini panduan Android; dp bukan physical pixel atau satuan CSS. [Android: Make apps more accessible](https://developer.android.com/guide/topics/ui/accessibility/apps)
- WAI menjelaskan bahwa grafik kompleks perlu deskripsi singkat dan uraian informasi penting yang lebih lengkap; nilai, skala, hubungan, dan tren dapat dijelaskan dalam uraian terstruktur. Uraian yang terlihat juga membantu orang dengan penglihatan rendah dan pengalaman domain terbatas. [W3C WAI: Complex Images](https://www.w3.org/WAI/tutorials/images/complex/)
- PRD meminta target sentuh minimum 48 logical units, kontras teks normal 4,5:1, sekitar 200% skala teks, alternatif teks grafik, safe areas dan keyboard avoidance, serta perbedaan antara gap, nol dan unknown. PRD menyebut 360/390/430/768/1280/1440 px sebagai lebar pemeriksaan. [PRD UX-07–14](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Inferences

**Kontrak ukuran:** gunakan token desain target minimum **48×48** untuk kontrol mobile. Pada web ukur dalam CSS px, pada Android ukur dp, dan pada iOS nyatakan serta ukur dalam point/logical unit implementasi. Angka token yang sama merupakan kebijakan HematDaya; jangan menyebutnya kesetaraan fisik antarsatuan atau aturan minimum Apple. Pastikan hit area ikon, chip periode, tombol back, tab, titik aksi grafik, dan menu benar-benar cukup dan tidak tumpang tindih. Android 48dp mendukung keputusan produk ini; WCAG 24 CSS px tidak menggantikannya. [PRD UX-07](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md), [Android](https://developer.android.com/guide/topics/ui/accessibility/apps)

**Kontrak grafik yang diusulkan:** tampilkan ranking kontribusi sebagai batang horizontal berlabel langsung (nama + kWh + persentase jika denominator valid), dan riwayat sebagai grafik waktu sederhana. Pilihan tipe ini adalah rekomendasi untuk tugas HematDaya, bukan kesimpulan bahwa satu jenis grafik selalu lebih aksesibel. [PRD FR-07/09, UX-08/13](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md), [WAI Complex Images](https://www.w3.org/WAI/tutorials/images/complex/)

- Cantumkan periode, zona waktu, unit, sumber/cakupan, serta kualitas dekat grafik. Angka grafik, ringkasan dan tabel alternatif harus berasal dari data/periode yang sama.
- Sediakan “Lihat data” yang membuka nilai terstruktur per aset/periode dengan status kualitas. Sertakan ringkasan seperti “Kulkas memakai energi tercatat paling besar: 8,4 kWh dari 14,7 kWh pada 19–25 Oktober; hanya empat sumber yang dipilih.” Ini contoh fixture H PRD, bukan data nyata.
- Hindari mewajibkan hover, scrub presisi, drag, atau membedakan warna untuk mendapatkan angka. Legend memakai label dan bentuk/garis pembeda; pilihan aktif juga memiliki teks/ikon. Pembaca layar dapat menyelesaikan tugas melalui ringkasan dan alternatif data tanpa menelusuri setiap titik gambar.
- Gap tetap terputus dan bertuliskan “Data tidak tersedia”; jangan menyambung garis seolah diukur atau mengisi nol. Nol tercatat ditulis `0 kWh` dengan cakupan yang benar. Total parsial berlabel “Energi tercatat · sebagian data belum tersedia”. Pada total nol yang valid, hilangkan persentase kontribusi; jangan membuat `0/0` atau ranking menyesatkan.
- Tarif tidak tersedia ditampilkan “Biaya belum tersedia · tarif belum diatur”; jangan `Rp0`. Offline berarti sumber/koneksi tidak diperbarui, bukan bukti perangkat listrik mati.
- Pertahankan label dan nama aset sebagai teks yang dapat membungkus. Pada layar kecil kurangi kepadatan tick atau perpendek label waktu yang tetap jelas; jangan mengecilkan seluruh grafik hingga tidak terbaca. Tabel pada mobile dapat berupa baris bertumpuk agar halaman tidak melebar.

Semantik angka, gap, biaya dan contoh berasal dari [PRD FR-07–09, §13, fixture H dan UX-06/08/13](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md); bentuk alternatif yang terstruktur mengikuti [WAI Complex Images](https://www.w3.org/WAI/tutorials/images/complex/).

**Checklist yang harus dicantumkan pada handoff, awalnya semua “belum dijalankan”:**

| ID | Acceptance yang dapat diperiksa | Bukti yang disimpan |
|---|---|---|
| A01 | Kontrol mobile memenuhi kebijakan 48×48 pada satuan runtime; target berdekatan tidak tumpang tindih. | Pengukuran hit area tiap jenis kontrol pada web/Android/iOS yang diuji. |
| A02 | Teks normal ≥4,5:1; informasi visual grafik/kontrol yang diperlukan ≥3:1. Pilihan/status tetap dapat dipahami tanpa warna. | Nilai kontras pasangan warna aktual, nama komponen dan state. |
| A03 | Teks 200%: angka, unit, nama aset panjang, tab, tombol dan pesan tidak terpotong/bertumpuk; semua fungsi tercapai. | Browser/text-scale, OS, screenshot state penting, kegagalan. |
| A04 | Lebar web 360/390/430/768/1280/1440 CSS px dan satu layar ponsel pendek: halaman tidak scroll horizontal. Tambah pemeriksaan reflow 320 CSS px, atau 1280 CSS px pada zoom 400%; simpan detail viewport dan zoom. | Screenshot dan interaksi, bukan screenshot saja. Uji reflow dan resize text dicatat terpisah. |
| A05 | Keyboard web menyelesaikan demo, ganti periode, buka kontributor, baca bukti, preview impor, koreksi, dan retry. Fokus berurutan/terlihat; overlay menempatkan fokus dengan benar, Escape menutup, fokus kembali ke pemicu. | Rekaman/rute langkah dan elemen fokus. |
| A06 | Semua kontrol punya label Indonesia yang bermakna, peran, pilihan/state dan nilai yang benar. Grafik memiliki ringkasan + alternatif nilai. Nama aset yang sama dibedakan dengan konteks. | Transkrip/hasil inspeksi accessibility tree dan pembacaan screen reader. |
| A07 | Gagal validasi diumumkan dan dapat dituju; pesan hasil/simpan diumumkan tanpa memindahkan fokus tak perlu; status tidak hanya toast yang cepat hilang. | Langkah input, fokus sebelum/sesudah, hasil pembacaan status. |
| A08 | Papan ketik layar dan safe area tidak menutupi input aktif, pesan koreksi atau aksi utama; pengguna bisa menggulir ke semuanya. Reduced motion dihormati. | Perangkat/OS, portrait/landscape relevan, keyboard terbuka, preference dan hasil. |

Dasar A01/A03/A04/A05/A08 ialah target produk [PRD UX-07–14](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md). Tabel menerjemahkan target menjadi prosedur; pemeriksaan ini belum dilakukan. Ambang dan perilaku web A02/A04/A05/A06/A07 merujuk [WCAG 2.2](https://www.w3.org/TR/WCAG22/); pemeriksaan alternatif grafik merujuk [WAI](https://www.w3.org/WAI/tutorials/images/complex/). Daftar ini bukan audit seluruh success criteria.

### Gaps

- Tidak ada nilai warna, font, markup, build native, accessibility tree, perangkat atau teknologi bantu yang diperiksa; seluruh A01–A08 belum dijalankan.
- Panduan Apple tentang safe areas/touch targets tidak dipakai sebagai sumber dalam catatan ini; ukuran iOS 48 merupakan target produk. Implementer perlu memverifikasi pemetaan satuan, safe areas, keyboard, dan pembesaran font pada build iOS aktual.
- Bukti keyboard/screen reader browser hanya berlaku untuk prototipe web yang diuji. Evaluasi Android/TalkBack dan iOS/VoiceOver harus dicatat terpisah; prototipe browser tidak membuktikan kepatuhan atau sertifikasi native.

## 3. Bagaimana menguji “intuitif” secara realistis tanpa mengarang hasil kepatuhan atau efektivitas?

### Takeaway

Uji penyelesaian dan pemahaman tugas dengan peserta nyata pada masing-masing segmen; evaluasi aksesibilitas teknis dan usability saling melengkapi. Ambang 4 dari 5 dan 30 detik adalah target PRD, bukan angka hasil, estimasi populasi, atau jaminan kepatuhan. [PRD §3, §20.1](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Cited Findings

- GOV.UK menyarankan tugas yang punya tujuan jelas, relevan, masuk akal, dan tidak memberi petunjuk jawaban. Moderator mengamati, meminta peserta berpikir keras, dan menggunakan instruksi netral. Sesi umumnya 30–60 menit. [GOV.UK: Using moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing)
- Pengguna teknologi bantu sering mempunyai konfigurasi pribadi yang sulit ditiru; GOV.UK menyarankan menggunakan perangkat mereka bila memungkinkan. Data dummy dapat digunakan ketika data nyata tidak dapat diproses dengan aman, tetapi mengurangi konteks. [GOV.UK: Using moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing)
- PRD meminta lima peserta rumah tangga dan lima usaha/industri bila tersedia, hasil per segmen, sedikitnya 4/5 menyelesaikan interpretasi inti tanpa bantuan, dan sedikitnya 4/5 mengidentifikasi kontributor terbesar dalam 30 detik. Keberhasilan satu segmen tidak boleh menutup kegagalan segmen lain. [PRD §3, §20.1, AT-52](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Inferences

Gunakan sesi 35–45 menit dengan pengantar, lima tugas inti, satu skenario pemulihan, dan wawancara penutup. Ini rancangan riset yang diusulkan, mengikuti instruksi netral GOV.UK dan kontrak PRD. Gunakan fixture H untuk rumah dan I untuk usaha; tanpa AC, jadwal atau output sebagai syarat. Mulai tes penemuan dari Beranda terisi pada periode lengkap yang ditetapkan; jangan memberi tur tab sebelum tugas pertama. [GOV.UK](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing), [PRD fixture H/I, §20.1](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

Pengantar moderator: “Kami menguji aplikasinya. Coba lakukan seperti biasanya dan ceritakan apa yang Anda pikirkan. Beberapa data adalah simulasi. Anda boleh berhenti kapan saja.” Minta persetujuan terpisah bila merekam; sediakan konfigurasi teknologi bantu peserta bila tersedia. Jangan menyebut tombol yang perlu ditekan dalam instruksi tugas. [GOV.UK](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing)

| Tugas netral dalam bahasa Indonesia | Kriteria pengamatan yang ditetapkan sebelum sesi |
|---|---|
| “Perangkat mana yang memakai energi paling besar pada periode ini? Tunjukkan pemakaiannya.” | Nama dan nilai benar; catat waktu sampai jawaban benar. Target PRD ≥4/5 per segmen ≤30 detik. Akses kontributor/riwayat ≤3 deliberate taps diperiksa pada desain secara terpisah. |
| “Ceritakan apa yang termasuk dalam angka energi dan biaya yang Anda lihat.” | Menyebut periode, sumber yang dipilih/cakupan, estimasi biaya bukan tagihan penuh; tidak menganggap seluruh rumah/pabrik pasti terukur. |
| “Ada perubahan pemakaian. Apa yang dapat Anda simpulkan dan apa yang belum diketahui?” | Menemukan nilai/perbandingan/bukti dan keterbatasan; tidak menyimpulkan kerusakan, pemborosan terverifikasi, atau perlu mematikan proses dari data saja. |
| “Masukkan data dari berkas ini. Ada beberapa baris yang perlu diperbaiki; lanjutkan dengan cara yang menurut Anda benar.” | Preview dibaca sebelum commit; peserta mengenali kesalahan dan barisnya, memahami data yang akan masuk, dapat memperbaiki/ganti file atau memilih hasil yang diizinkan tanpa kehilangan data lama. |
| “Biaya belum muncul untuk data ini. Jelaskan penyebabnya dan cari pemakaian energinya.” | Energi masih dapat ditemukan; biaya yang hilang tidak dianggap gratis/nol. Tarif tetap opsional. |
| Skenario pemulihan: “Data baru belum masuk. Apa yang Anda lakukan untuk memeriksa keadaan sekarang?” | Peserta mengenali timestamp/parsial/offline sesuai skenario; tidak mengira meter offline membuktikan perangkat mati; menemukan retry tanpa mengulang isian yang masih tersedia. |

Kriteria tabel merupakan operasionalisasi yang diusulkan dari [PRD §3/7/13/14/20.1](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md), bukan pernyataan bahwa peserta sudah berhasil. Untuk tugas interpretasi inti, laporkan jumlah berhasil pada setiap tugas dan jumlah peserta yang menyelesaikan seluruh rangkaian tanpa bantuan; jangan memilih metrik yang lebih menguntungkan setelah melihat hasil.

Untuk peserta usaha yang memang membutuhkannya, tambahkan pengaturan jadwal melewati tengah malam dan input output aktual. Jangan memberi tugas produksi kepada rumah tangga sebagai syarat berhasil. Catat pembaca layar/ukuran teks yang digunakan, tetapi jangan menuntut peserta teknologi bantu menyamai waktu rata-rata peserta lain; laporkan temuan dan hambatan akses per tugas dan konfigurasi. Target waktu PRD bukan alat mengabaikan kebutuhan akses. [PRD UX-16, §20.1](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md), [GOV.UK assistive-technology testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing)

Format rekaman minimum per tugas: ID peserta anonim/segmen → build dan fixture → runtime/perangkat/teknologi bantu → status mandiri/dibantu/gagal → waktu → salah arah/tap → ucapan tentang cakupan/kualitas → bantuan moderator → isu dan tingkat keparahan. Definisikan bantuan sebagai instruksi yang mengarahkan tindakan atau interpretasi; pertanyaan netral “Apa yang Anda pikirkan?” bukan bantuan. Jika prototype tidak mengerjakan commit aktual, nilai langkah preview/konfirmasi yang tersedia dan tandai pengujian commit “tidak dapat diuji pada prototipe ini”. [GOV.UK](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing), [PRD AT-48/52 dan §22.3](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

Laporan akhir harus memisahkan: review desain; pengukuran browser; sesi pengguna; Android; iOS; dan perilaku backend impor. Catat tanggal dan versi runtime pada setiap hasil. Status awal seluruhnya “belum dijalankan”. Klaim yang aman sebelum pengujian adalah “dirancang untuk memenuhi target aksesibilitas yang disebutkan”; jangan “WCAG certified”, “native sudah aksesibel”, “4/5 pengguna berhasil”, atau “terbukti hemat listrik”. [PRD §0, AT-45–48/52, §22–23](/home/ahmad-widardi/Projects/random/pertanian/docs/generic/hematdaya/01_PRD_HematDaya_Generic_EN.md)

### Gaps

- Tidak ada peserta direkrut atau sesi dijalankan. Sampel lima per segmen merupakan putaran formatif kecil, tidak menghasilkan estimasi statistik keberhasilan seluruh populasi.
- Belum diketahui kebutuhan akses aktual calon pengguna Indonesia; sertakan peserta dengan kebutuhan akses dalam rekrutmen dan periksa perangkat/konfigurasi pribadi. Ketersediaan peserta dapat memerlukan putaran tersendiri; jangan mengganti pengujian dengan asumsi peneliti.
- Riset ini tidak menilai implementasi Expo, backend, hardware, ketepatan pengukuran, maupun penghematan. Semua sumber web dibuka pada 21 Oktober 2026; catatan ini menggunakan enam sumber primer: WCAG, WAI Complex Images, Android accessibility, GOV.UK Error summary, GOV.UK usability testing, dan artikel asli NNGroup.
