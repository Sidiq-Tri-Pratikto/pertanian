# Bahasa dan audit redaksi proposal HematDaya

## Bagaimana membuat bahasa proposal lebih jelas tanpa mengganti semua istilah teknis?

### Takeaway
Gunakan subjek yang jelas dan kata kerja yang langsung menunjukkan pekerjaan: tim menguji, pengguna mengunggah, aplikasi menghitung. Pertahankan bahasa Indonesia yang biasa digunakan, lalu sisakan istilah Inggris yang membantu ketepatan atau lebih akrab bagi pembaca teknis.

### Cited Findings
- Materi penulisan proposal yang dilaporkan DJKN menekankan manfaat bagi pembaca, kalimat ringkas, bahasa sederhana, tujuan yang terukur, dan penyuntingan sebelum dikirim. Ini saran penulisan dari forum internal, bukan penelitian tentang deteksi AI. — [DJKN, 8 Juni 2023](https://www.djkn.kemenkeu.go.id/kpknl-lhokseumawe/baca-berita/32428/Penulisan-Proposal-yang-Baik-dan-Berkualitas-dalam-Forum-Sanger-Kanwil-DJKN-Aceh.html)
- Balai Bahasa Jawa Barat menyarankan padanan Indonesia terlebih dahulu dan istilah asing bila diperlukan. Karena pengguna secara eksplisit ingin mempertahankan sebagian istilah Inggris, gunakan panduan ini untuk mencegah campuran bahasa yang berlebihan, bukan memaksakan terjemahan. — [Balai Bahasa Jawa Barat, 27 November 2025](https://balaibahasajabar.kemendikdasmen.go.id/cara-menggunakan-istilah-asing-dalam-kalimat/)

### Inferences
- Masalah redaksi saat ini bukan semata-mata terlalu baku, tetapi terlalu banyak benda abstrak dan sederet pembatas teknis dalam satu paragraf. Proposal akan lebih enak dibaca jika pembuka menggambarkan persoalan yang dikenali pembaca, lalu menjawab bagaimana pengguna terbantu.
- Jangan mengubah semua kata menjadi Inggris. Data hilang, izin, konsumsi, biaya, jadwal, pengujian, dan perangkat sudah jelas. Menulis *missing data*, *permission*, atau *consumption* di seluruh naskah justru membuatnya terasa dibuat-buat.
- Tulis manfaat sebagai kemampuan yang ingin diberikan dan pengujian sebagai rencana. Hindari menjadikan target 4 dari 5 pengguna sebagai capaian dan jangan menambahkan persentase penghematan.
- Gunakan kalimat aktif saat pelakunya relevan; kalimat pasif tetap wajar ketika fokusnya memang pada data atau alat. Tidak ada aturan semua kalimat harus aktif.

### Gaps
- Penilaian “terasa seperti AI” bersifat editorial. Ketiga sumber ini tidak memberikan dasar untuk menjanjikan tulisan lolos alat pendeteksi AI.
- Tidak ada survei lapangan atau hasil penghematan baru dalam penugasan ini. Kebutuhan klinik, mitra, dan nilai ekonominya tetap perlu diuji.

## Bagaimana memakai huruf miring dan istilah Inggris secara konsisten?

### Takeaway
Cetak miring kata atau ungkapan asing dalam narasi. Nama produk, organisasi, dan merek tetap tegak; jangan otomatis memiringkan singkatan atau satuan.

### Cited Findings
- EYD V bagian G.3 menetapkan huruf miring untuk kata atau ungkapan bahasa asing. Catatan a mengecualikan nama diri, termasuk nama orang, lembaga, organisasi, dan merek dagang. Bagian G.1 juga mengatur huruf miring pada judul buku yang dirujuk, termasuk daftar pustaka. — [EYD V, Huruf Miring](https://ejaan.kemendikdasmen.go.id/eyd/penggunaan-huruf/huruf-miring/)

### Inferences
- Miringkan *browser*, *backend*, *baseline*, *machine learning*, *pilot*, *deployment*, *backup*, *restore*, dan *usability test* jika istilah ini dipakai. Tidak semua harus dimasukkan; pilih hanya yang memudahkan pembaca.
- HematDaya dan Home Assistant adalah nama produk sehingga tetap tegak. CSV, PRD, TKT, UMY, UGM, kWh, dan nama menu Beranda/Perangkat/Saran tidak perlu dimiringkan hanya karena singkatan, satuan, atau nama label. Untuk singkatan teknis, ini keputusan editorial dari konteks, bukan kalimat eksplisit EYD yang mengatur CSV/PRD.
- Judul subbab *Executive Summary* dapat dimiringkan tanpa mengganti penomoran template. Nama tema Inggris dalam identitas program dapat dibiarkan sesuai nama resminya; jangan memperlakukannya sebagai istilah teknis narasi yang harus diterjemahkan.
- “Prototipe” sudah lazim dan tidak perlu dipaksa menjadi *prototype*. “Prototipe di *browser*” lebih alami dalam konteks ini dibanding “prototipe peramban”.

### Gaps
- EYD mengatur ejaan, bukan memilih istilah mana yang paling mudah dimengerti calon pembaca proposal teknologi. Pemilihan *browser* dan *backend* adalah keputusan editorial yang mengikuti permintaan pengguna.

## Bagian mana dari proposal saat ini sebaiknya diubah?

### Takeaway
Executive summary sebaiknya dibuka dengan persoalan tagihan dan keputusan sehari-hari, tanpa menyebut UMY atau pedoman. Rincian program, batas pengujian, dan konteks fasilitas kesehatan tetap dapat muncul di bagian yang memang membahas rencana kegiatan.

### Cited Findings
- Proposal lokal saat ini berisi executive summary dengan rujukan pedoman dan UMY, istilah “prototipe peramban”, “pengujian fungsi terpadu”, serta “nilai tengah periode terdahulu yang setara”. Pernyataan statusnya: prototipe memakai data simulasi; 36 uji acuan tercatat lulus; proses server disimulasikan; TKT awal dinilai tim pada level 3 dan target TKT 4 April 2027. Audit ini membaca naskah, bukan menjalankan ulang uji. — [Sumber lokal: Proposal-HematDaya-UMY.md](/home/ahmad-widardi/Projects/random/pertanian/docs/umy-2026-hematdaya/submission/proposal/Proposal-HematDaya-UMY.md)

### Inferences

Pilihan suntingan berikut adalah usulan editorial, bukan tambahan fakta:

| Redaksi saat ini | Usulan | Alasan |
|---|---|---|
| Pemantauan Listrik dan Saran Berbasis Bukti untuk Berbagai Kebutuhan | Memahami Pemakaian Listrik, Menentukan Langkah Penghematan | Judul lebih dekat dengan kebutuhan pembaca; jangan menyatakan penghematan sudah terbukti. |
| Pedoman UMY menyebut... | Hapus dari executive summary; pindahkan sumber masalah fasilitas kesehatan ke bagian deskripsi | Pembuka ringkasan harus berpusat pada masalah dan solusi. |
| berkas data berformat CSV | file CSV | Lebih pendek; *file* dapat dimiringkan jika dipertahankan sebagai kata Inggris. “Data CSV” juga cukup dan tanpa istilah tambahan. |
| meter yang terverifikasi dapat ditambahkan kemudian | koneksi meter akan diuji setelah alur CSV berjalan | Menegaskan status rencana tanpa mengesankan ada meter yang sudah terbukti didukung. |
| prototipe peramban | prototipe di *browser* | Sesuai istilah yang umum bagi tim teknologi. |
| proses server masih disimulasikan | *backend* masih disimulasikan | Lebih tepat untuk keterbatasan teknis saat ini. |
| satu sistem dengan komponen bersama | aplikasi memakai satu basis kode dengan modul sesuai kebutuhan | Menjelaskan reuse dengan kata yang konkret. |
| nilai tengah periode terdahulu yang setara | median dari periode pembanding yang sebanding | Istilah statistik median lebih tepat daripada menghindarinya melalui frasa panjang. |
| perhitungan awal | *baseline* sederhana | Pada kalimat pembanding *machine learning*, “awal” tidak menjelaskan pembanding metodologis. |
| pengujian fungsi terpadu | menguji alur impor, penyimpanan, perhitungan, dan tampilan sebagai satu aplikasi | Konkret; dalam paragraf berulang berikutnya cukup “uji integrasi”. |
| layanan pemasangan, penerapan aplikasi, dan dukungan berkala | jasa pemasangan, *deployment*, dan dukungan setelah pemasangan | Lebih jelas mengenai layanan; belum berarti model usaha terbukti. |
| impor yang aman diulang | impor ulang tanpa menggandakan data | Menjelaskan akibat yang dipahami pembaca. |
| keterlacakan / bukti capaian / kriteria penerimaan | catatan hasil uji / bukti hasil / syarat tugas dinyatakan selesai | Pilih sesuai maksud; jangan mengganti istilah formal jika ada makna audit yang diperlukan. |
| hasil dilaporkan per konteks | hasil rumah tangga dan industri dicatat terpisah | Menyebut konteks yang dimaksud. |
| menentukan hal yang perlu diperiksa | membantu pengguna memilih perangkat atau jam pemakaian yang perlu diperiksa | Mengganti abstraksi dengan keputusan sehari-hari. |

Kerangka executive summary yang disarankan:

1. Persoalan: tagihan menunjukkan total; pengguna belum bisa melihat penyumbang terbesar dan membedakan perubahan kebiasaan dengan perubahan perangkat.
2. Solusi: HematDaya membantu membaca data listrik per perangkat/sirkuit melalui CSV, menampilkan energi dan biaya bila tarif ada, serta menjelaskan dasar saran. Rumah tangga, usaha, dan industri dapat memakai alur yang sama dengan pengaturan sesuai kebutuhan.
3. Cara menjaga hasil tetap masuk akal: data hilang tidak dianggap nol dan meter utama tidak dijumlahkan ulang dengan perangkat di bawahnya. Memakai listrik pada malam hari belum tentu boros. Pilih satu atau dua mekanisme ini; tidak perlu memuat seluruh PRD.
4. Status dan rencana: PRD dan prototipe di *browser* sudah tersedia dengan data simulasi; TKT awal merupakan perkiraan tim pada level 3. Tim menargetkan TKT 4 April 2027 melalui uji integrasi. Biaya layanan atau penghematan belum diuji. Jangan mengaitkan kalimat ini dengan nama program di executive summary.

Fakta yang wajib dijaga saat penulisan ulang: empat anggota tim termasuk Akmal; 36 hasil uji hanya disebut sebagai hasil yang tercatat, bukan hasil verifikasi baru; *backend*, koneksi meter, dan lapangan belum divalidasi; target TKT 4 bukan sertifikasi; empat tangkapan layar tetap ada; naskah utama tiga halaman. Jangan mengubah peran Akmal menjadi tenaga kesehatan atau menambah mitra yang belum ada.

### Gaps
- Naskah tiga halaman perlu dirender lagi setelah penyuntingan; audit teks ini tidak dapat memastikan panjang halaman atau tampilan *italic* pada PDF akhir.
- Saya tidak menjalankan 36 uji terdahulu dan tidak menguji prototipe. Semua status di atas dibatasi pada pernyataan di sumber lokal saat audit.
