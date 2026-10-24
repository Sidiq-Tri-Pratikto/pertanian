# HematDaya - dokumen UMY 2026

Diperbarui 24 Oktober 2026. Dasar produk sekarang **HematDaya generik**, untuk rumah tangga, usaha, dan industri. Konteks fasilitas kesehatan hanya digunakan untuk usulan validasi UMY; tidak membentuk produk atau inti perhitungan tersendiri. Prototipe di *browser* dengan data simulasi tersedia; status implementasi dan pengujiannya dicatat terpisah.

## Berkas yang digunakan sekarang

| Berkas | Kegunaan |
|---|---|
| [PRD generik Indonesia - PDF](prd/01_PRD_HematDaya_Generic_ID.pdf) | Spesifikasi lengkap, 37 halaman, dengan daftar isi dan bookmark bagian |
| [PRD generik Indonesia - Markdown](prd/01_PRD_HematDaya_Generic_ID.md) | Salinan utuh sumber generik v1.2, 21 Oktober 2026 |
| [PRD generik English - Markdown](prd/01_PRD_HematDaya_Generic_EN.md) | Padanan Inggris dari dasar produk yang sama |
| [Proposal utama - PDF](submission/proposal/Proposal-HematDaya-UMY.pdf) | Maksimal tiga halaman A4; form substansi bagian 1-7 mengikuti lampiran pedoman revisi |
| [Proposal utama - Markdown](submission/proposal/Proposal-HematDaya-UMY.md) | Sumber isi, sitasi, dan figur tangkapan layar yang dapat diedit; renderer menyusun form dan pergantian halaman |
| [Sampul dan identitas - PDF](submission/administrasi/Administrasi-HematDaya-UMY.pdf) | Dua halaman administrasi pendamping, belum ditandatangani |
| [Sampul dan identitas - Markdown](submission/administrasi/Administrasi-HematDaya-UMY.md) | Sumber data administratif dan catatan pengisian |

PRD kanonis berada di [folder generik](../generic/hematdaya/). Kedua salinan Markdown di sini identik dalam byte dengan sumbernya, bukan PRD fasilitas kesehatan yang disusun ulang. Perubahan berikutnya dilakukan pada sumber kanonis lalu disalin kembali agar keduanya tidak berbeda tanpa disengaja.

SHA-256 saat disalin:

```text
ID 4f9a0993e4533d60d817c343f9d77ab6ebc4a610a79c191672f4c750870faaba
EN 8939667cb5f5ee6296d8c108607f98765c3ef8ff76d292513fe905d236567baa
```

## Ringkasan isi

HematDaya memantau energi dari CSV atau sumber meter yang telah diverifikasi, memperlihatkan kontribusi beban, riwayat, kualitas data, dan pengamatan yang dapat ditelusuri. Tarif, jadwal, serta energi per satuan keluaran bersifat opsional. Data hilang tidak dianggap nol dan meter induk/anak tidak dijumlahkan dua kali. Produk tidak mengendalikan peralatan.

Arsitektur yang diterima adalah monolit modular: inti pengukuran/cakupan/kualitas/bukti dipakai bersama, sedangkan biaya, jadwal, keluaran, dan adapter mengikuti kemampuan yang diperlukan. Penyesuaian klien dikembangkan dari sumber bersama, tanpa cabang perhitungan permanen per pelanggan. Ini tidak mewajibkan SaaS multi-tenant atau white-label.

Untuk UMY, proposal memilih **Bidang Strategis Kesehatan**, **Klaster 08 - Sustainable and Green Healthcare**, dengan rumah sakit dan klinik sebagai konteks penerapan awal. Dasar masalahnya ialah keragaman kebutuhan layanan dan perlunya rincian konsumsi untuk keputusan pengelola; kondisi fasilitas sasaran masih perlu divalidasi. Tim Petani Digital terdiri atas Ahmad Widardi, Sidiq Tri Pratikto, Akmal Rafli Fauzan, dan Erwin Eko Wahyudi. Keikutsertaan Akmal dikonfirmasi pemilik pada 24 Oktober 2026. Tim memperkirakan TKT awal **3** berdasarkan prototipe di *browser* yang sudah tersedia dengan data dan *backend* simulasi. Targetnya **TKT 4 pada April 2027**, melalui *integration test* dalam lingkungan terkontrol dan evaluasi mentor/asesor.

## Dasar format dan batas penafsiran

Sumber utama: [Buku Pedoman Peserta UMY Hackathon DeepTech 2026 Revisi](https://drive.google.com/file/d/1Zzk80Mf3XR-poQPG4i49x48cByk3GVod/view), dibaca 24 Oktober 2026 dari [folder yang diberikan pengguna](https://drive.google.com/drive/folders/1WaBli2s3qcdMWfiRjOkjhI0iqBs0cHvB). Folder tersebut berisi satu PDF pedoman revisi. Format Word terpisah dari pekerjaan lama tidak dijadikan acuan pembaruan ini.

- Bagian 3.3 dan halaman 17 menetapkan proposal awal maksimal tiga halaman A4. Lampiran halaman 17-20 menjadi acuan sampul, lembar identitas, dan form substansi; bagian 1-7 pada halaman 19-20 menetapkan ringkasan maksimal 250 kata, deskripsi maksimal dua halaman, serta pembagian tugas maksimal satu halaman.
- Tata letak mengikuti form dengan judul navy, label bagian teal, dan bidang isian berbingkai. Pilihan bidang menggunakan kotak centang dengan **Kesehatan** dipilih dan **Klaster 08 - Sustainable and Green Healthcare** dinyatakan. Label form memakai IBM Plex Sans; isi naskah memakai Times New Roman asli tertanam, 12 pt, leading 13,8 pt (1,15). Ringkasan berisi 178 kata dengan penghitungan kata berbasis spasi tanpa sitasi numerik; ringkasan tidak memuat sitasi.
- Penyuntingan mengikuti [kajian penulisan proposal dan masalah energi](../../reports/Penulisan%20proposal%20dan%20masalah%20energi.md). Ringkasan tiga paragraf menghubungkan kebutuhan operasional, alur informasi HematDaya, serta kesiapan dan rencana evaluasi. Dasar masalah menggunakan WHO 2023 dan HTM/NHS 2015; pedoman program menjadi acuan administrasi dan format. Kajian membedakan panduan penulisan, fakta energi, serta inferensi penerapannya. Status prototipe, target, peran tim, batas klaim, dan empat tangkapan layar dipertahankan; rincian teknologi dirujuk ke PRD. Ruang baca memakai jarak sesudah paragraf 6 pt, sebelum/sesudah judul 10/6 pt, dan padding vertikal tabel 5 pt. Label batas kata atau halaman ditempatkan pada baris tersendiri.
- Pedoman tidak menjelaskan secara tegas apakah sampul dan lembar identitas termasuk batas tiga halaman. Karena itu, substansi dibatasi maksimal tiga halaman dan administrasi dua halaman disediakan terpisah. Penggabungan atau penempatan isian mengikuti sistem panitia; belum ada konfirmasi resmi mengenai penafsiran batas tersebut.
- Jadwal Uji Terbatas pada halaman 12 berbeda dari tabel halaman 13 (24-26 versus 9-12 November). Roadmap tidak memilih salah satunya sebagai jadwal pasti; kehadiran mengikuti konfirmasi panitia.
- Proposal PetaniDigital/TemuRiset revisi yang diberikan pengguna digunakan sebagai referensi gaya, identitas, dan pengalaman tiga anggota. Status produk TemuRiset, tanda tangan, bukti demo, dan mitranya tidak dipindahkan ke HematDaya.
- [Dokumentasi Home Assistant](https://www.home-assistant.io/docs/energy/individual-devices/) digunakan untuk menempatkan pemantauan perangkat/hierarki meter sebagai kemampuan yang telah ada; proposal tidak mengklaimnya sebagai penemuan baru.

## Kelengkapan di luar naskah proposal

- CV dan portofolio seluruh anggota, termasuk CV Akmal, serta bukti status aktif dosen/mahasiswa perlu disiapkan untuk unggahan. Dosen dan mahasiswa tercatat berasal dari UGM; status aktif belum diverifikasi ke PDDIKTI.
- Lembar identitas belum ditandatangani. Ketua merupakan profesional sehingga kolom identitas disesuaikan menjadi NIK; format pedoman menampilkan NIDN/NIDK/NUPTK. Penerimaannya perlu dicocokkan dengan sistem panitia.
- Pakta integritas bertanda tangan harus memakai pedoman revisi: tujuh komitmen, termasuk etik dan keselamatan. Pakta lama dalam folder ini mengikuti format berbeda dan bukan dokumen final pembaruan ini.
- Belum ada bukti kemitraan atau izin pilot. Tidak ada berkas yang dikirim ke panitia dalam pekerjaan ini.
- Gambar 1 pada Lampiran memuat empat tangkapan layar [prototipe di *browser*](../generic/hematdaya/prototype/) dengan data simulasi (skenario "Industri · kompresor di luar jadwal"), disimpan di [submission/proposal/assets/prototipe/](submission/proposal/assets/prototipe/). Untuk mengambil ulang, jalankan server prototipe lalu `node tests/capture-screenshots.js <folder-keluaran>` dari folder prototipe. Belum ada tautan demo publik maupun hasil uji pengguna.
- PDF proposal dan administrasi telah dirender ulang dengan Times New Roman asli tertanam. Pemeriksaan format mencakup tiga halaman substansi, dua halaman administrasi, kelengkapan teks sumber, dan tampilan setiap halaman; ini bukan pengujian ulang prototipe.

## Dokumen lama

PRD dan proposal bernama `Faskes`, prototipe lama di `applications/umy-2026-hematdaya/`, serta pakta lama dipertahankan sebagai riwayat. Klaim prototipe/TKT dan format penomoran pada berkas tersebut tidak menjadi bukti versi generik sekarang. Gunakan daftar berkas terkini di atas untuk melanjutkan pekerjaan.

## Membangun ulang PDF

Renderer: [tools/build_documents.py](tools/build_documents.py). Memerlukan Python dengan `reportlab`, `markdown-it-py`, dan `pypdf`. IBM Plex Sans beserta lisensi OFL disertakan di [tools/fonts](tools/fonts/). Font Times New Roman asli tetap berasal dari instalasi berlisensi pengguna dan tidak dimasukkan ke repositori.

Pada macOS, renderer mencari font asli bernama `Times New Roman` beserta varian bold, italic, dan bold italic secara otomatis. Untuk direktori font khusus atau Linux, gunakan `--font-dir` yang memuat empat font berlisensi `Times.TTF`, `Timesbd.TTF`, `Timesi.TTF`, dan `Timesbi.TTF`. Jika font asli tidak ditemukan, sediakan direktori tersebut sebelum membangun PDF.

Pilih keluaran yang akan diperbarui secara eksplisit. Perintah berikut membangun proposal dan administrasi; PRD PDF tidak ditulis ulang:

```bash
python3 tools/build_documents.py --only proposal administrasi
```

Untuk font dari direktori khusus:

```bash
python3 tools/build_documents.py --only proposal administrasi --font-dir /path/to/licensed-times-fonts
```

Untuk menyiapkan pratinjau proposal tanpa mengganti PDF di repositori, arahkan keluaran ke direktori sementara:

```bash
python3 tools/build_documents.py --only proposal --output-dir /tmp/umy-preview
```

Jalankan dari folder ini atau gunakan lokasi absolut script. `--only` membatasi PDF yang dibangun; tanpa opsi ini ketiga target, termasuk PRD, dibangun seperti sebelumnya. `--output-dir` menentukan direktori tujuan. Renderer menolak ringkasan di atas 250 kata, proposal yang melebihi tiga halaman, atau administrasi yang bukan dua halaman. Kandidat PDF dibangun terlebih dahulu dan hanya mengganti PDF tujuan setelah batas yang berlaku terpenuhi; proposal yang terlalu panjang mempertahankan PDF tujuan sebelumnya. Setelah mengubah naskah, render ulang dan periksa tampilan setiap halaman; pemeriksaan jumlah halaman tidak menggantikan pemeriksaan visual.
