# Sumber data dan pola pencarian

Nama situs dan alamat bisa berubah; cari dengan nama lembaga bila URL lama tidak berfungsi. Utamakan sumber primer, lalu berita. Selalu catat **tanggal terbit** dan **tahun data**, dan beri `jenis` yang benar di daftar `sumber`:

| `jenis` | Untuk |
|---------|-------|
| `data` | Statistik, survei, dataset terbuka |
| `resmi` | Dokumen pemerintah/lembaga: rencana, laporan kinerja, peraturan |
| `berita` | Media massa |
| `jurnal` | Artikel ilmiah, tesis, laporan riset |
| `lainnya` | Kanal pengaduan, media sosial, blog, situs perusahaan |

## Indonesia

**Statistik dan data terbuka**
- BPS dan publikasi "<Wilayah> Dalam Angka" (kabupaten/kota/provinsi); Sensus dan Susenas.
- Satu Data Indonesia (data.go.id) dan portal data terbuka milik pemda setempat.
- Portal sektoral: SatuSehat/Kemenkes (kesehatan), Dapodik dan Kemendikdasmen (pendidikan), SIPSN KLHK (persampahan), DIBI BNPB (bencana), Kementan (pertanian), Kemnaker/Sakernas (tenaga kerja), OJK (keuangan dan literasi), Kemenhub (transportasi), PUPR (infrastruktur air dan sanitasi).
- APJII dan BPS/Susenas untuk penetrasi internet; Kominfo/Komdigi dan BAKTI untuk sinyal dan desa blank spot.

**Perencanaan dan kinerja daerah**
- RPJMD, Renstra OPD, RKPD, LKPJ/LPPD kepala daerah, dan APBD; biasanya ada di situs Bappeda, dinas terkait, atau JDIH.
- Catatan: dokumen ini sering menyebut masalah dan target resmi, sehingga berguna untuk mengukur celah antara target dan kondisi nyata.

**Suara warga**
- LAPOR! (lapor.go.id), kanal pengaduan pemda, Google Maps ulasan layanan publik, media sosial dinas/pemda (komentar), forum warga.
- Gunakan untuk melihat pola dan tren keluhan; jangan mengutip individu secara identifiable.

**Berita dan analisis**
- Antara, Kompas, Detik, Tempo, CNN Indonesia, media regional (Tribun, Radar, Pikiran Rakyat, dsb.), serta media lokal yang meliput wilayah tersebut.
- Jurnal: Garuda, SINTA, Google Scholar, repositori kampus setempat; cari skripsi/tesis dan laporan penelitian wilayah itu.

## Untuk solusi dengan perangkat keras
- **Harga dan ketersediaan**: halaman produk distributor resmi, marketplace besar (catat tanggal akses; harga berubah), e-katalog LKPP. Simpan tangkapan atau URL, dan tulis rentang.
- **Spesifikasi**: datasheet dan dokumentasi pabrikan (Raspberry Pi, Espressif, vendor kamera dan sensor); jangan mengandalkan ulasan atau ringkasan pencarian untuk angka teknis.
- **Regulasi dan sertifikasi**: Kemkomdigi/Ditjen SDPPI (sertifikasi perangkat telekomunikasi), BSN (SNI), peraturan pemerintah daerah tentang pemasangan kamera di ruang publik, dan UU PDP No. 27/2022.
- **Kondisi lokasi**: PLN dan pemda untuk keandalan listrik, operator seluler dan BAKTI untuk sinyal, BMKG untuk cuaca.
- **Bukti kinerja**: jurnal dan laporan pilot tentang akurasi di lapangan; bedakan hasil dataset dengan hasil lapangan.

## Global dan luar Indonesia
- World Bank Open Data, UN Data dan UNDP, indikator SDG (UN Stats), WHO (Global Health Observatory), OECD Data, Our World in Data.
- ITU dan GSMA (konektivitas dan adopsi mobile), DataReportal/We Are Social (penetrasi digital).
- Portal data terbuka kota/negara bersangkutan, laporan anggaran dan kinerja pemerintah kota, dan berita lokal.

## Pola pencarian yang efektif

| Tujuan | Contoh query |
|--------|--------------|
| Angka resmi | `<topik> <wilayah> dalam angka 2025`, `<topik> <wilayah> filetype:pdf` |
| Target vs kenyataan | `RPJMD <wilayah> <topik> target`, `LKPJ <wilayah> 2024 <topik>` |
| Pengaduan | `keluhan <topik> <wilayah>`, `lapor <topik> <wilayah>` |
| Tren berita | `<topik> <wilayah> 2025`, `<topik> <wilayah> viral`, `krisis <topik> <wilayah>` |
| Riset akademik | `<topik> <wilayah> studi kasus`, `<topik> <wilayah> jurnal` |
| Kondisi digital | `penetrasi internet <wilayah> 2024`, `blank spot <wilayah>`, `literasi digital <wilayah>` |

## Pemeriksaan mutu sumber
- Angka yang sama dari dua sumber berbeda → pakai, sebutkan keduanya.
- Angka berbeda antar sumber → tulis rentang dan jelaskan perbedaan definisinya.
- Data lebih dari 3 tahun → tulis tahunnya dengan jelas, dan turunkan skor `bukti` bila itu satu-satunya dasar.
- Satu berita saja tanpa data pendukung → belum cukup untuk masalah prioritas.
- Jangan mengutip tiruan/agregator bila sumber aslinya bisa dibuka.
