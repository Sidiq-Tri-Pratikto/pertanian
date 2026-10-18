# Naskah Video Demo Prototype Alpha: SOPilot

Durasi target **2:40–2:50** · 12 layar kanvas (UC1–UC6) + pembuka dan penutup · ±290 kata narasi (±130 kata/menit, sisanya jeda klik).

## Persiapan rekaman

- Buka kanvas desain SOPilot, tekan **Play**, lalu mulai dari layar 1 ("UC1.1 Beranda dan unggah SOP"). Pindah layar lewat tombol utama di layar atau **Lanjut ›** di bilah bawah.
- Rekam layar 1920×1080 (macOS: Cmd+Shift+5), zoom browser 100%, sembunyikan bilah bookmark dan notifikasi.
- Tampilkan label kecil di pojok sepanjang video: **"Prototipe interaktif · data contoh (fiktif)"**.
- Narasi bisa direkam terpisah lalu disinkronkan; potong jeda kosong saat menyunting.
- Unggah ke YouTube (Unlisted) atau Google Drive (siapa pun yang memiliki tautan dapat melihat), lalu salin tautannya ke formulir pendaftaran dan lampiran proposal.

## Naskah

| Waktu | Layar | Aksi di layar | Narasi |
|---|---|---|---|
| 0:00–0:10 | Pembuka: slide sampul deck | Logo dan judul SOPilot; label "data contoh" | "SOP di banyak organisasi masih berupa dokumen. SOPilot mengubahnya menjadi proses bisnis yang bisa dijalankan. Berikut demo prototipe interaktif kami dengan data contoh." |
| 0:10–0:22 | 1 · Beranda dan unggah SOP | Klik **Pakai contoh SOP** | "Admin cukup mengunggah SOP dalam PDF atau DOCX. Kami memakai contoh SOP Pengadaan Barang/Jasa sampai Rp200 juta: sembilan langkah, tiga pelaksana." |
| 0:22–0:34 | 2 · Ekstraksi dan penyusunan model | Tunggu tahap tercentang; sorot catatan di bawah | "SOPilot mengekstrak teks, mengenali pelaksana dan aktivitas, lalu menyusun model. LLM hanya mengisi model perantara; XML BPMN dibangkitkan oleh kode, sehingga selalu valid." |
| 0:34–0:47 | 3 · Model proses dan jejak sumber | Klik elemen diagram; kalimat sumber tersorot | "Hasilnya diagram BPMN per pelaksana, dan setiap elemen terhubung ke kalimat sumbernya. Kalimat lima ditandai: 'segera diproses oleh pihak terkait'. Siapa pihak terkait?" |
| 0:47–1:00 | 4 · Simulasi menemukan celah | Tab **Jalankan**; simulasi berhenti | "Sebelum diekspor, model diuji lewat simulasi. Simulasi berhenti di 'Proses Permintaan Pengadaan' karena pelaksananya belum ada. Masalah ini ketahuan sekarang, bukan saat proses sudah dipakai." |
| 1:00–1:13 | 5 · Klarifikasi ambiguitas | Klik **Bagian Pengadaan**, lalu **Terapkan** | "SOPilot tidak menebak. Ia bertanya: siapa yang memproses permintaan ini? Admin memilih Bagian Pengadaan, atau meneruskan pertanyaan ke pemilik SOP." |
| 1:13–1:25 | 6 · Model lengkap dan siap dijalankan | Sorot daftar **Siap dijalankan: 4 dari 4 syarat** | "Tiga jawaban diterapkan: pelaksana, jalur 'Tidak', dan akhir proses. Keempat syarat terpenuhi, dan model siap dijalankan." |
| 1:25–1:37 | 7 · Tugas berpindah antar-peran | Isi **Sisa anggaran**, klik **Selesaikan tugas** | "Simulasi dijalankan ulang. Tugas berpindah antar-peran: Bagian Keuangan mengisi sisa anggaran dan menyelesaikan tugasnya, seperti di mesin workflow." |
| 1:37–1:48 | 8 · Keputusan Ya atau Tidak | Klik **Ya** | "Di gerbang 'Anggaran tersedia?', keputusan diambil dari isian formulir. Jalur Ya lanjut ke pengadaan; jalur Tidak kini jelas: permintaan ditolak." |
| 1:48–2:00 | 9 · Proses selesai dan log eksekusi | Sorot log eksekusi | "Proses berjalan sampai selesai: delapan tugas oleh tiga peran, tanpa edit manual. Log eksekusinya bisa diekspor untuk analisis proses." |
| 2:00–2:12 | 10 · Ekspor BPMN executable | Sorot `isExecutable` dan `candidateGroups` di XML; klik **Unduh .bpmn** | "Model diekspor sebagai BPMN 2.0 executable, lengkap dengan grup pelaksana, kondisi keputusan, dan isian formulir, siap diimpor ke Camunda atau Flowable." |
| 2:12–2:25 | 11 · Poster panduan pekerja | Gulir poster pelan-pelan | "Dari model yang sama, SOPilot menyusun poster untuk pekerja: judul langkah yang singkat dan formal, pelaksana tiap langkah, dan QR untuk membuka versi terbaru." |
| 2:25–2:36 | 12 · Model LLM lokal | Pilih **Lokal (Ollama)** | "Untuk dokumen sensitif, SOPilot bisa memakai model lokal, sehingga teks SOP tidak keluar dari server instansi." |
| 2:36–2:45 | Penutup: logo atau slide penutup deck | Tampilkan nama tim dan tautan prototipe | "SOPilot: dari SOP menjadi proses yang dapat dijalankan, diuji, dan dipahami pekerja. Terima kasih." |

## Catatan

- Jika durasi lewat 3:00, persingkat layar 12 atau gabungkan layar 6 ke akhir layar 5.
- Jangan menyebut angka akurasi; prototipe ini memvalidasi alur dan pengalaman pengguna, sedangkan mesin ekstraksi, generator, dan simulator dibangun pada tahap Prototype Alpha Refinement.
- Kanvas demo masih privat. Video tidak memerlukannya, tetapi bagikan kanvas dulu jika tautannya ikut dicantumkan di lampiran.
