# Naskah demo TemuRiset

Semua data di naskah ini fiktif. Nilai yang diketik saat demo sama dengan `applications/temuriset-api/app/demo/service/scenario.py`. Tes `tests/integration/demo/test_scenario.py` menjalankan skenario 1 sampai 3 dan memastikan label kecocokannya.

## Sebelum mulai

1. Buka `/start`, lalu pilih **Atur ulang demo**. Kondisi awalnya:
   - **Inovator A** punya **Produk A (ClearSpring)**, saringan air tahap prototipe. Produk ini sudah terbit, kebutuhan dananya aktif, dan halaman publiknya menyala dengan ilustrasi, ringkasan uji lapangan, dan satu kabar.
   - **Investor A** fokus pada investasi pertanian tahap pilot dan punya satu peluang aktif, "Pendanaan pilot pertanian".
   - **Investor B** masih akun kosong tanpa profil.
2. Masuk ke tiap akun lewat pilihan akun demo di `/start`, tanpa email.

## Skenario 1: Investor B dibuat dengan kebutuhan berbeda

Masuk sebagai **Investor B**. Isi profil mitra lalu buka satu peluang dengan nilai berikut.

| Bagian | Isi |
|---|---|
| Jenis | Investor energi desa |
| Tesis | Mendanai energi surya skala kecil untuk desa tanpa listrik stabil. |
| Sektor | Energi |
| Tahap | Prototipe, Pilot |
| Wilayah | Indonesia |
| Bentuk dukungan | Pendanaan proyek |
| Bentuk hubungan | Proyek |
| Judul peluang | Pendanaan energi surya desa |
| Hasil | Prototipe energi surya teruji di desa dalam enam bulan. |
| Kata kunci | surya, listrik, desa, baterai |
| Dana | USD 25.000–60.000, total 6 bulan |

Aktifkan peluang itu. Poin yang ditekankan: Investor A mencari pertanian tahap pilot, Investor B mencari energi tahap prototipe.

## Skenario 2: Produk B untuk Investor B

Masuk sebagai **Inovator A**. Buat inovasi baru lalu terbitkan.

| Bagian | Isi |
|---|---|
| Judul | SolarBox Desa |
| Ringkasan | Kotak listrik surya dengan baterai untuk rumah di desa tanpa listrik stabil. |
| Sektor | Energi |
| Tahap | Prototipe |
| Kata kunci | surya, listrik, desa, baterai |

Setelah itu buat kebutuhan dukungan untuk SolarBox Desa lalu aktifkan:

- Hasil yang dicari: "Uji lapangan SolarBox di satu desa"
- Bentuk hubungan: proyek
- Dana: USD 30.000–45.000, total 6 bulan

## Skenario 3: Peluang tiap produk

Masih sebagai Inovator A, buka **Kecocokan** untuk kedua kebutuhan.

| Produk | Investor A, pertanian | Investor B, energi |
|---|---|---|
| Produk A, ClearSpring | Kecocokan lemah | Kecocokan lemah |
| Produk B, SolarBox Desa | Kecocokan lemah | **Kecocokan kuat** |

Buka "Mengapa cocok?" pada hasil Produk B dan Investor B. Sektor, tahap dan semua kata kunci cocok. Pada Produk A, hanya kata "desa" yang sama.

### Skenario 3b: Perbaiki Produk A dari rekomendasi kecocokan

Dari rincian kecocokan Produk A terhadap Investor A, buka bagian **Cara meningkatkan kecocokan** lalu ikuti tautan **Perbarui kata kunci** (atau **Perbarui TKT** setelah 056). Setelah menyimpan dan menerbitkan versi baru, tekan **Kembali ke kecocokan** untuk melihat skor aspek yang berubah secara langsung (misalnya `Topik dan detail produk 25 → 100`).

## Skenario 4: Inovator A mengajukan lebih dulu

Dari hasil Produk B dan Investor B, pilih **Siapkan pitching**. Tunjukkan ringkasan "Yang akan diterima Investor B", lalu tekan **Kirim pitching**. Masuk sebagai Investor B: pitching muncul di antrean Beranda.

## Skenario 5: Investor B mengajak lebih dulu

Masuk sebagai Investor B, buka **Jelajahi**, lalu buka SolarBox Desa. Di samping **Simpan inovasi** tertulis **Ajak pitching · segera hadir**. Fitur investor mengajak inovator untuk pitching ada di rencana berikutnya dan belum dibangun.

## Skenario tambahan yang disarankan

Skenario ini memakai fitur yang sudah ada dan bisa langsung diteruskan dari skenario 4.

6. **Tinjau dan minta revisi.** Investor B mulai meninjau pitching lalu meminta revisi pada satu jawaban. Inovator A menjawab dan mengirim ulang. Investor B menyetujui pitching untuk diskusi. Yang ditunjukkan: riwayat versi tetap tersimpan.
7. **Jadwalkan pertemuan.** Investor B menawarkan beberapa waktu, lalu Inovator A memilih satu. Jadwal tampil di zona waktu masing-masing.
8. **Ikuti inovasi lewat email, tanpa akun.** Buka halaman publik ClearSpring (`/temuan/{id}` atau `/en/inventions/{id}`) di jendela pribadi. Isi email di **Ikuti inovasi ini**, lalu konfirmasi dari kotak surat pengembangan (`/api/v1/dev/mailbox?email=...`, hanya ada di lingkungan pengembangan). Inovator A menerbitkan kabar baru, lalu email "Pembaruan dari ClearSpring" masuk satu kali.
9. **Dua bahasa.** Tekan **EN** di halaman publik atau halaman masuk. Teks antarmuka berganti, sedangkan tulisan inovator diberi label "Written in Indonesian".
10. **Kabar inovasi untuk investor tanpa akun.** Berlangganan di `/langganan` dengan kata kunci "desa". Investor mendapat kabar inovasi yang sesuai.

Urutan yang disarankan untuk demo pendek: 1 → 2 → 3 → 4 → 6 → 8 → 5. Skenario 5 ditutup dengan rencana ke depan.
