# Naskah Video Demo Prototype Alpha: HematDaya

Durasi target **2:40–2:50**. Rekam di jendela lebar penuh (prototipe berbentuk layar HP di tengah). Tampilkan label kecil sepanjang video: **"Prototipe · data contoh (sintetis)"**.

## Persiapan

- Buka prototipe (https://claude.ai/artifact/M7yATNgrVRv3EJksg1NnqP) setelah dibagikan lewat menu Share. Tekan **Pengaturan → Skenario demo → Normal** agar mulai dari awal.
- Untuk adegan impor, siapkan isi `data-contoh-ikm.csv` (folder `applications/angel-2026-hematdaya/`) atau pakai contoh 3 baris dari lembar Impor.
- Rekam layar 1920×1080, zoom 100%, sembunyikan notifikasi. Narasi bisa direkam terpisah lalu disinkronkan.
- Unggah ke YouTube (Unlisted) atau Google Drive, lalu masukkan tautannya ke Lampiran proposal.

## Naskah

| Waktu | Layar | Aksi | Narasi |
|---|---|---|---|
| 0:00–0:12 | Slide sampul deck | Logo dan judul | "Pemilik industri kecil biasanya hanya melihat satu angka listrik: total tagihan. HematDaya membaca konsumsi per mesin dan menjelaskan di mana energi terbuang. Ini demo prototipe dengan data contoh." |
| 0:12–0:30 | **Beranda** | Tunjuk biaya, kWh, dan label Demo | "Ini Beranda untuk minggu ini: 873 kWh dari empat mesin, dengan estimasi biaya dari tarif yang diisi pengguna. Angka ini bukan tagihan PLN dan hanya mencakup mesin yang terhubung." |
| 0:30–0:45 | Beranda, grafik | Gulir ke grafik; ketuk **Hari ini** lalu **Minggu ini** | "Grafik menunjukkan energi per hari, ditumpuk per mesin. Hari yang belum ada datanya tidak digambar sebagai nol, dan ada ringkasan teks di bawahnya." |
| 0:45–1:00 | Beranda, **Mesin terbesar** | Ketuk **Oven Pengering** | "Mesin terbesar langsung terlihat: Oven Pengering, hampir separuh energi minggu ini. Di detail ada energi saat jam operasional dan di luar jam operasional." |
| 1:00–1:20 | Tab **Saran** | Ketuk **Kompresor Udara di luar jam operasional naik 128%** | "Di tab Saran ada temuan: konsumsi Kompresor Udara di luar jam operasional naik 128% dibanding median tiga minggu sebelumnya." |
| 1:20–1:45 | Penjelasan saran | Sorot tabel dan bagian "Yang belum diketahui" | "Penjelasannya memuat angka minggu ini, pembandingnya, dan selisihnya. Aplikasi juga jujur: data listrik belum bisa menjelaskan penyebabnya. Bisa lembur, bisa mesin lupa dimatikan." |
| 1:45–1:58 | Umpan balik | Ketuk **Bermanfaat** | "Pengguna bisa menilai saran itu bermanfaat atau kurang sesuai, atau menundanya. Umpan balik tidak menghapus data." |
| 1:58–2:15 | **Pengaturan** | Buka ikon roda gigi; ubah jam mulai, kosongkan tarif | "Jam operasional, hari kerja, tarif, dan produksi per hari bisa diatur. Kalau tarif dikosongkan, aplikasi hanya menampilkan kWh dan tidak mengarang rupiah. Produksi per hari dipakai untuk menghitung IKE, energi per unit." |
| 2:15–2:38 | **Impor data** | Tempel CSV, ketuk **Analisis data** | "Pengguna tanpa meter bisa mengimpor catatan energi dalam CSV. Analisisnya berjalan langsung di peramban: waktu, mesin, dan energi dibaca, lalu biaya, konsumsi di luar jam kerja, dan IKE dihitung ulang." |
| 2:38–2:50 | Penutup | Slide penutup deck | "HematDaya hanya memantau dan menyarankan, tanpa mengontrol mesin. Berikutnya kami menguji dengan meter dan data IKM nyata. Terima kasih." |

## Catatan

- Total ±2:50; jeda saat berpindah layar bisa dipotong saat menyunting, tetapi pastikan akhir video di atas 2:00.
- Sebutkan secara jujur bahwa datanya sintetis dan belum diuji di pabrik nyata. Jangan menyebut angka akurasi.
- Alur klik sudah diuji di Chrome (impor, skenario, umpan balik). Di layar sempit (< 460 px) tampilannya tetap berbentuk HP penuh.
