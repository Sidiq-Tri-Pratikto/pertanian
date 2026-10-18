# Solusi yang terintegrasi perangkat keras

Dibaca di langkah 6 (ide solusi) dan langkah 8 (detail solusi) bila solusinya memakai webcam, CCTV/kamera IP, Raspberry Pi atau komputer mini lain, mikrokontroler (ESP32, Arduino), sensor, atau perangkat edge. Aturan inti di `SKILL.md` tetap berlaku: tanpa data karangan, tanpa harga atau spesifikasi tanpa sumber, dan tidak merekomendasikan yang sudah ada di wilayah.

## 1. Kapan perangkat keras layak diusulkan

Perangkat keras menambah biaya, pemasangan, perawatan, risiko pencurian, dan beban hukum. Usulkan **hanya bila** setidaknya satu benar:

- Data yang dibutuhkan **tidak bisa dimasukkan manual dengan andal** (jumlah orang, tingkat penuh, suhu atau arus terus-menerus, berat, kualitas visual).
- Pengukuran harus **terus-menerus atau jarang dilakukan manusia** (malam hari, banyak titik, lokasi berbahaya).
- Ada **tindakan fisik otomatis** (relay, alarm, pintu, pompa).
- Nilai data dari perangkat jelas melebihi biaya total kepemilikan (perangkat, data seluler, perawatan, penggantian).

Bila ponsel, formulir, atau bot WhatsApp sudah cukup, **pilih itu** dan catat di `ide_gugur` atau `catatan_non_software` mengapa perangkat keras tidak dipilih. Jangan memakai perangkat keras demi terlihat canggih.

## 2. Peran perangkat yang umum

| Perangkat | Cocok untuk | Yang perlu diperhatikan |
|-----------|-------------|--------------------------|
| Webcam USB | Prototipe dan titik dalam ruangan dekat komputer mini | Fokus tetap, kurang tahan cuaca dan malam hari; kabel USB dibatasi panjangnya |
| Kamera IP atau CCTV (RTSP/ONVIF) | Titik luar ruang, banyak kamera, perangkat yang sudah terpasang | Cek apakah aliran RTSP terbuka untuk integrasi; banyak CCTV sudah punya analitik bawaan (hitung orang, plat nomor) yang harus masuk cek kebaruan; pemilik CCTV bisa instansi lain |
| Raspberry Pi atau komputer mini sejenis | Pemrosesan di tempat (edge), gerbang sensor, kios | Stok dan harga berfluktuasi; siapkan alternatif papan; kartu SD rentan rusak saat mati listrik (pakai SD industri atau SSD, watchdog) |
| Akselerator AI (Coral, Hailo, Jetson) | Deteksi objek atau video berkelanjutan yang terlalu berat untuk CPU | Biaya dan ketersediaan; mulai dari model kecil dan resolusi rendah dulu |
| ESP32 atau Arduino dengan sensor | Suhu, kelembapan, arus (CT clamp), level (ultrasonik), berat (load cell), GPS, gas | Murah dan hemat daya; kalibrasi dan drift sensor menentukan kualitas data |
| Meter listrik atau air pintar (Modbus RS485, pulse) | Konsumsi energi dan air | Sering sudah dimiliki penyedia (PLN, PDAM); cek akses data dan izin sebelum memasang meter tambahan |
| Pembaca barcode, RFID, atau NFC | Pencatatan keluar-masuk barang dan aset | Label rusak dan salah baca di lapangan |
| LoRa, Zigbee, BLE | Banyak sensor hemat daya tanpa sinyal seluler | Butuh gateway dan sertifikasi perangkat radio |

Ini daftar peran, bukan klaim produk; harga dan ketersediaan di bagian 5 harus bersumber.

## 3. Pola arsitektur yang aman dipakai

- **Edge dulu.** Proses gambar atau sinyal di perangkat, kirim hanya hasilnya (angka, label, kejadian). Menekan biaya data, menjaga privasi, dan tetap bekerja saat sinyal lemah.
- **Simpan lalu kirim ulang (store-and-forward).** Antrean lokal (SQLite) dengan kunci idempotensi supaya data aman dikirim ulang setelah offline.
- **Protokol ringan.** MQTT dengan TLS untuk telemetri; HTTPS untuk unggahan jarang. Hindari membuka port masuk di jaringan lokasi.
- **Pembaruan jarak jauh (OTA) bertanda tangan** dan **pemantauan kesehatan** (heartbeat, suhu CPU, ruang disk). Perangkat yang mati diam-diam adalah kegagalan paling umum.
- **Pemulihan otomatis**: layanan dimulai sendiri setelah listrik hidup, watchdog, dan kartu penyimpanan tahan tulis berulang.
- **Pisahkan aturan bisnis dari perangkat.** Perangkat menangkap dan mengklasifikasi; server menyimpan aturan, ambang, dan jejak audit.
- **Definisikan ukuran mutu** sejak awal (akurasi, uptime, latensi) dan cara mengukurnya di lapangan, bukan di meja.

## 4. Kondisi lapangan untuk dicek di profil wilayah (langkah 2)

Selain kondisi digital, catat dan beri sumber untuk yang relevan: ketersediaan dan keandalan listrik di titik pasang, sinyal seluler atau Wi-Fi di lokasi (bukan rata-rata kota), cuaca dan debu, risiko pencurian atau vandalisme, siapa pemilik lokasi dan izin pemasangan, ketersediaan teknisi dan suku cadang lokal, serta waktu kirim perangkat. Bila tidak ada datanya, tulis sebagai asumsi di `metodologi.keterbatasan`.

## 5. Biaya dan pengadaan

- Susun **daftar komponen (BOM)** di `perangkat_keras.perangkat`: nama, fungsi, spesifikasi, jumlah per titik, perkiraan biaya.
- **Harga dan spesifikasi harus bersumber dan bertanggal**: halaman produk distributor atau marketplace, datasheet, atau e-katalog. Masukkan sebagai `sumber` di daftar sumber dan sitasi di baris komponen. Tulis rentang, bukan satu angka, dan sebut bahwa harga berubah. Tanpa sumber, tulis jelas "estimasi" (validator memberi peringatan).
- Hitung **biaya per titik** dan **biaya bulanan** (paket data, listrik, perawatan, penggantian rutin), lalu biaya total beberapa tahun. Jangan hanya menyebut harga perangkat.
- **Pengadaan**: sumber lokal, waktu tunggu, alternatif bila stok habis, dan syarat pengadaan pemerintah (e-katalog LKPP, persyaratan TKDN) bila pembelinya instansi. Verifikasi aturan terbaru sebelum menulisnya.
- Pilih **perangkat murah yang mudah dibeli lokal**, dengan alternatif kedua, daripada komponen terbaik yang sulit didapat.

## 6. Privasi, hukum, dan keselamatan (untuk `privasi_keselamatan` dan `regulasi`)

- **Kamera dan data pribadi.** Citra wajah dan biometrik adalah data pribadi (UU No. 27/2022 tentang Pelindungan Data Pribadi, yang menggolongkan data biometrik sebagai data spesifik). Utamakan **tanpa menyimpan video**, proses di perangkat, buram atau buang wajah dan plat nomor, simpan hasil agregat, batasi masa simpan, dan pasang **pemberitahuan** bahwa area dipantau beserta tujuan dan kontak pengelola. Hindari pengenalan wajah kecuali benar-benar perlu dan ada dasar hukumnya; verifikasi aturan terbaru.
- **Lokasi pasang.** Arahkan kamera ke objek (bak, mesin, gerbang), bukan ke rumah, jalan, atau area privat.
- **Sertifikasi perangkat radio dan telekomunikasi** (Wi-Fi, seluler, LoRa) oleh otoritas yang berwenang di Indonesia; periksa label sertifikasi pada perangkat yang akan dibeli dan aturan terbaru.
- **Keselamatan kelistrikan dan K3.** Pemasangan pada panel atau listrik tegangan tinggi dilakukan teknisi yang kompeten; jangan menyarankan pengguna awam membuka panel. Gunakan catu daya, kabel, dan kotak yang sesuai (mis. IP65 untuk luar ruang).
- **Keamanan siber.** Ganti kata sandi bawaan, tutup port yang tidak dipakai, perbarui firmware, simpan rahasia di luar kode, dan pisahkan jaringan perangkat dari jaringan kantor.
- **Persetujuan dan izin.** Pemilik lokasi, pengelola kawasan, atau instansi (mis. Dishub untuk jalan) bisa mensyaratkan izin pasang.

## 7. Cek kebaruan khusus perangkat keras

Lihat bagian "Tambahan untuk solusi dengan perangkat keras" di `cek-kebaruan.md`: kanal marketplace, e-katalog, vendor CCTV dan IoT, serta aturan "sudah ada" untuk produk yang dijual dan dipasang di wilayah.

## 8. Prototipe untuk solusi berperangkat keras

Prototipe di Artifact **tidak bisa memakai kamera atau mikrofon** (diblokir tanpa permintaan izin) dan tidak bisa menjangkau perangkat fisik atau aliran RTSP. Pilihan jujur:

1. **Halaman simulasi**: unggah foto atau video contoh (file input) dan tampilkan hasil klasifikasi atau hitung dari data contoh. Beri label bahwa itu simulasi, bukan perangkat nyata.
2. **Skrip lokal yang bisa dijalankan** (mis. Python dengan OpenCV, MQTT) yang membaca webcam laptop atau berkas video dan menunjukkan hasil di terminal atau jendela. Jalankan dan uji di komputer sendiri sebelum melaporkan.
3. **Simulator** untuk mikrokontroler (mis. Wokwi) bila hanya logika sensor yang perlu ditunjukkan.

Katakan terus terang: apa yang diuji (data contoh, rekaman, simulasi) dan yang **belum diuji di lapangan** (akurasi pada cahaya dan cuaca nyata, uptime, daya tahan perangkat, pemasangan, keamanan fisik). Jangan menyatakan akurasi lapangan tanpa pengujian lapangan. Isi `prototipe.batasan` sesuai.

## 9. Kesalahan yang sering terjadi

- Menganggap akurasi model di dataset sama dengan akurasi di lokasi (cahaya, sudut, kotor, hujan, malam).
- Melupakan biaya berulang (data seluler, penggantian kartu SD, pembersihan lensa, teknisi).
- Mengusulkan sensor baru padahal data yang sama sudah dimiliki instansi (meter pintar, CCTV kota).
- Menyimpan video mentah "untuk jaga-jaga".
- Menulis harga satu toko sebagai fakta tetap.
- Mengusulkan perangkat yang hanya bisa dibeli impor tanpa mencantumkan waktu tunggu dan alternatif.
