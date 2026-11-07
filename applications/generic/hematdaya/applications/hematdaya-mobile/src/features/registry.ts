/**
 * Every planned feature, in one place. `HDComingSoon` and the feature list render from it, and each feature's
 * pull request flips `status`. `screens` map to the PRD screen contract; `specs` name folders under `specs/`.
 * Spec numbers are for engineers and stay out of product copy.
 */
export type FeatureStatus = 'coming_soon' | 'available';

export type Feature = {
  id: string;
  title: string;
  summary: string;
  points: string[];
  screens: string[];
  specs: string[];
  status: FeatureStatus;
};

export const FEATURES: Feature[] = [
  {
    id: 'demo',
    title: 'Data demo',
    summary: 'Coba HematDaya dengan data simulasi rumah tangga atau industri, tanpa akun dan tanpa alat ukur.',
    points: ['Pilih contoh rumah tangga atau industri', 'Data simulasi diberi label jelas', 'Dapat diatur ulang kapan saja'],
    screens: ['S01', 'S02'],
    specs: ['007', '008', '012'],
    status: 'available',
  },
  {
    id: 'ringkasan-energi',
    title: 'Ringkasan energi',
    summary: 'Lihat energi yang dipantau pada periode dan cakupan yang Anda pilih.',
    points: ['Pilih hari ini, tujuh hari terakhir, atau rentang tanggal', 'Cakupan pengukuran tampil di dekat angka', 'Kelengkapan data dan kesegaran sumber terlihat'],
    screens: ['S03'],
    specs: ['009', '013'],
    status: 'available',
  },
  {
    id: 'kontributor',
    title: 'Kontributor terbesar',
    summary: 'Bandingkan perangkat yang dipantau pada satu garis dasar, lengkap dengan nilai dan porsinya.',
    points: ['Urutan berdasarkan energi tercatat', 'Tersedia juga sebagai tabel data', 'Urutan bukan penilaian boros atau hemat'],
    screens: ['S03'],
    specs: ['009', '013'],
    status: 'available',
  },
  {
    id: 'estimasi-biaya',
    title: 'Estimasi biaya',
    summary: 'Perkirakan biaya energi terpantau dari tarif yang Anda isi.',
    points: ['Tarif bersifat opsional', 'Tarif yang belum diatur tidak dianggap Rp0', 'Estimasi berbeda dari tagihan listrik'],
    screens: ['S03', 'S09'],
    specs: ['018', '019'],
    status: 'coming_soon',
  },
  {
    id: 'daftar-perangkat',
    title: 'Daftar perangkat',
    summary: 'Lihat perangkat, grup, sirkuit, dan meter lokasi beserta energi tercatatnya.',
    points: ['Jenis cakupan tampil di setiap baris', 'Nama panjang tetap utuh', 'Tidak ada tombol nyala atau mati'],
    screens: ['S04'],
    specs: ['014'],
    status: 'available',
  },
  {
    id: 'detail-perangkat',
    title: 'Riwayat perangkat',
    summary: 'Periksa riwayat, kekosongan data, dan asal pengukuran satu perangkat.',
    points: ['Grafik dengan ringkasan teks dan tabel', 'Data kosong berbeda dari 0 kWh', 'Ubah nama atau arsipkan tanpa menghapus riwayat'],
    screens: ['S06'],
    specs: ['010', '014', '015', '016'],
    status: 'coming_soon',
  },
  {
    id: 'saran',
    title: 'Saran berbasis bukti',
    summary: 'Temukan perubahan pemakaian yang layak diperiksa, dibandingkan dengan periode yang sebanding.',
    points: ['Hanya muncul bila datanya cukup', 'Catatan kualitas data dipisahkan', 'Saran umum diberi label jelas'],
    screens: ['S07'],
    specs: ['020', '021', '022'],
    status: 'available',
  },
  {
    id: 'bukti-saran',
    title: 'Bukti dan umpan balik',
    summary: 'Baca dasar perhitungan setiap saran, lalu tandai, tunda, atau sembunyikan.',
    points: ['Nilai, pembanding, dan batasan terlihat', 'Penyebab yang belum diketahui disebutkan', 'Umpan balik tidak mengubah data'],
    screens: ['S08'],
    specs: ['022', '023'],
    status: 'available',
  },
  {
    id: 'impor-data',
    title: 'Impor data CSV',
    summary: 'Masukkan riwayat energi dari berkas CSV dengan pratinjau sebelum disimpan.',
    points: ['Periksa arti kolom, zona waktu, dan interval', 'Baris bermasalah dijelaskan satu per satu', 'Mencoba lagi tidak menggandakan data'],
    screens: ['S10'],
    specs: ['024', '025', '026', '027'],
    status: 'available',
  },
  {
    id: 'cakupan-sumber',
    title: 'Cakupan dan sumber',
    summary: 'Pilih tampilan yang dapat dijumlahkan bila meter saling mencakup atau satu beban punya dua sumber.',
    points: ['Meter utama dan sub-meter tidak dijumlahkan', 'Alasan pengecualian ditampilkan', 'Nilai masing-masing tetap terlihat'],
    screens: ['S11'],
    specs: ['028', '029'],
    status: 'coming_soon',
  },
  {
    id: 'sumber-meter',
    title: 'Sumber dan meter',
    summary: 'Lihat sumber data yang didukung dan statusnya yang sebenarnya.',
    points: ['Status tersedia dan direncanakan dipisahkan', 'Tidak ada koneksi tanpa pembacaan valid', 'Tidak ada petunjuk mengubah kabel listrik'],
    screens: ['S05'],
    specs: ['035', '046'],
    status: 'coming_soon',
  },
  {
    id: 'pengaturan-lokasi',
    title: 'Pengaturan lokasi',
    summary: 'Atur nama lokasi, konteks penggunaan, dan zona waktu.',
    points: ['Konteks hanya mengubah contoh', 'Perubahan zona waktu dikonfirmasi lebih dulu', 'Pengukuran tidak ditulis ulang'],
    screens: ['S09'],
    specs: ['017'],
    status: 'coming_soon',
  },
  {
    id: 'jadwal-pemakaian',
    title: 'Jadwal pemakaian',
    summary: 'Tentukan jam pemakaian yang diharapkan untuk melihat energi di luar jadwal.',
    points: ['Opsional untuk setiap lokasi', 'Mendukung jendela melewati tengah malam', 'Perangkat yang menyala terus tidak dianggap masalah'],
    screens: ['S09'],
    specs: ['030', '031'],
    status: 'coming_soon',
  },
  {
    id: 'metrik-keluaran',
    title: 'Energi per keluaran',
    summary: 'Hitung energi per unit, batch, atau keluaran lain bila usaha Anda memerlukannya.',
    points: ['Tidak diperlukan untuk rumah tangga', 'Pembilang dan penyebut ditampilkan', 'Keluaran nol tidak menghasilkan angka'],
    screens: ['S12'],
    specs: ['032', '033'],
    status: 'coming_soon',
  },
  {
    id: 'data-tersimpan',
    title: 'Offline dan pemulihan',
    summary: 'Tetap membaca data tersimpan saat offline, dengan draf yang tidak hilang.',
    points: ['Waktu data tersimpan terlihat', 'Offline berbeda dari sumber yang belum diperbarui', 'Perubahan menunggu konfirmasi layanan'],
    screens: ['S03'],
    specs: ['034'],
    status: 'coming_soon',
  },
  {
    id: 'akun',
    title: 'Akun dan data tersimpan',
    summary: 'Simpan data Anda dengan aman, ekspor, atau hapus kapan saja.',
    points: ['Data terpisah per pemilik', 'Ekspor data pengukuran', 'Penghapusan dikonfirmasi lebih dulu'],
    screens: ['S09'],
    specs: ['036', '037', '038'],
    status: 'coming_soon',
  },
  {
    id: 'notifikasi',
    title: 'Notifikasi',
    summary: 'Terima pemberitahuan saran baru bila Anda menyetujuinya.',
    points: ['Mati sampai Anda menyalakannya', 'Saran tetap tersedia di dalam aplikasi'],
    screens: ['S09'],
    specs: ['045'],
    status: 'coming_soon',
  },
];

export function findFeature(id: string | undefined): Feature | undefined {
  return FEATURES.find((feature) => feature.id === id);
}
