# Asal tanda tangan

Keempat PNG merupakan ekstraksi tanda tangan yang sudah ada pada halaman 2 berkas yang dilampirkan pengguna, `Pakta-Integritas-HematDaya-UMY (2).pdf`.

SHA-256 berkas sumber:

```text
4cf78cafadb403f7ee21a16e023a46519f03b9546c04fed71616cdaffe018e66
```

Berkas sumber tidak diubah. Aset hanya memuat goresan tanda tangan, tanpa teks identitas, tanggal, judul kolom, atau garis tabel. Tidak ada tanda tangan baru yang digambar, ditelusuri ulang, dibersihkan bentuknya, atau dihasilkan secara generatif.

## Wilayah dan metode ekstraksi

Koordinat berikut memakai PDF point dengan titik asal di kiri bawah halaman sumber berukuran 594,96 × 841,92 pt.

| Aset | Wilayah sumber `[x0, y0, x1, y1]` | Metode |
|---|---|---|
| `ahmad-widardi.png` | `[470.755, 605.634, 528.790, 660.788]` | Appearance asli anotasi `/Ink` dipisahkan sebagai Form XObject dan dirender pada 600 dpi dengan latar transparan. Koordinat dan seluruh goresan asli dipertahankan. |
| `sidiq-tri-pratikto.png` | `[479.000, 575.920, 510.000, 608.920]` | Citra `/Im1` asli dari appearance anotasi `/Stamp` diekstrak bersama soft mask transparansinya pada resolusi asli 62 × 66 px. |
| `akmal-rafli-fauzan.png` | `[471.71320, 539.08110, 521.69989, 570.89552]` | Form vektor asli Adobe Fill & Sign pada jalur XObject `/Fm0` → `/Fm1` → `/Fm0` dipisahkan dan dirender pada 600 dpi dengan latar transparan. |
| `erwin-eko-wahyudi.png` | `[483.47105, 496.41999, 507.22895, 533.41999]` | Citra `/fzImg0` asli pada konten halaman diekstrak bersama soft mask transparansinya pada resolusi asli 244 × 380 px. |

Ekstraksi memakai `pypdf` untuk memisahkan appearance/citra, Poppler `pdftocairo -png -transp -r 600` untuk merasterisasi dua Form vektor, dan Pillow untuk menambahkan margin transparan. Margin PNG ialah 6 px pada setiap sisi, kecuali sumber Sidiq yang memakai 3 px. Margin tidak mengubah piksel tanda tangan; tidak ada pembesaran atau interpolasi tambahan pada dua citra raster asli. Mutu citra Sidiq mengikuti resolusi rendah sumbernya.

## Sidik berkas aset

```text
ahmad-widardi.png       e666c1cf8fe3dc0bc9a8bf44f0ca75036a2aa2b4fb847cce4724b3d135050a19
sidiq-tri-pratikto.png  9096bac59166af1bfa2386c8794e2b654fbf0b3680502b86bbdb205644dc5aa2
akmal-rafli-fauzan.png  843c5ae5133143ba3685c707b9cc005a8fe86768dbe8f43fe88826de450015da
erwin-eko-wahyudi.png   22a38bef0da2488bda3d19f8d0049894d54feefd7c7f2497cc966ec298159858
```
