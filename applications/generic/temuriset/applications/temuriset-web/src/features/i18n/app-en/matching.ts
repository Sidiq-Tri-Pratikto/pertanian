/**
 * English translations for Track A matching breakdown (057) and recommendations (058).
 * Kept in its own file per docs/roadmap/revamp-2-demo-feedback.md §3.
 */
export const MATCHING_EN: Record<string, string> = {
  // Toggletip
  'Penjelasan: {label}': 'Explanation: {label}',
  // Breakdown headings and labels (057)
  'Rincian kecocokan': 'Match breakdown',
  'Kecocokan dengan mandat Anda': 'Fit with your mandate',
  'Pratinjau dari profil publik': 'Preview from the public profile',
  'Hitung ulang untuk melihat rincian': 'Recalculate to see the breakdown',
  'Hitung ulang': 'Recalculate',
  Bidang: 'Field',
  'Topik dan detail produk': 'Topic and product detail',
  'Tahap dan TKT': 'Stage and TKT',
  Dana: 'Funding',
  'Bentuk kerja sama': 'Form of partnership',
  'Syarat wajib': 'Required items',
  Bukti: 'Evidence',
  'Ketersediaan investor': 'Investor availability',
  Cocok: 'Match',
  Sebagian: 'Partial',
  'Belum cocok': 'Mismatch',
  Proyek: 'Project',
  Lisensi: 'License',
  Ekuitas: 'Equity',
  '{label} {before} → {after}': '{label} {before} → {after}',
  // Dimension help tooltips
  'Bernilai 100% jika sektor inovasi termasuk sektor yang dicari mandat, 0% jika berbeda, dan belum diketahui jika salah satu belum mengisi.':
    'Scores 100% if the invention sector is among the mandate sectors, 0% if different, and unknown if either side leaves it blank.',
  'Persentase kata kunci mandat yang muncul sebagai kata utuh pada kata kunci, judul, ringkasan, masalah, atau solusi inovasi Anda.':
    'Share of mandate keywords appearing as whole words in your invention keywords, title, summary, problem, or solution.',
  'Rata-rata kecocokan tahap inovasi dan TKT (Tingkat Kesiapterapan Teknologi) terhadap preferensi mandat. Bagian yang belum diisi tidak dihitung sebagai nol.':
    'Mean of invention stage and TKT (technology readiness level) match against the mandate preferences. Unstated parts are never treated as zero.',
  'Bernilai 100% jika kisaran dana beririsan pada mata uang, periode, dan cakupan yang sama; 50% jika tidak beririsan tetapi dukungan sebagian diterima; 0% jika tidak beririsan.':
    'Scores 100% when ranges overlap on the same currency, period, and scope; 50% when they do not overlap but partial support is accepted; 0% otherwise.',
  'Bernilai 100% jika bentuk kerja sama kebutuhan Anda termasuk yang diterima mandat, 0% jika berbeda, dan belum diketahui pada pratinjau tanpa kebutuhan.':
    'Scores 100% if your need partnership form is accepted by the mandate, 0% if different, and unknown in a preview without a need.',
  'Persentase syarat wajib saat pengajuan yang terpenuhi. Jika ada syarat wajib yang gagal, hasil tetap tidak cocok meski aspek lain tinggi.':
    'Share of submission-stage required items that pass. If any required item fails, the match stays incompatible regardless of other scores.',
  'Persentase syarat yang sudah didukung berkas atau pernyataan yang tersedia maupun diperiksa. Ditampilkan untuk transparansi kepercayaan.':
    'Share of applicable checklist items backed by provided or reviewed evidence. Shown for trust transparency.',
  'Bernilai 100% jika mandat sedang aktif menerima pitching saat ini, 0% jika ditutup, dijeda, atau menggunakan jalur eksternal.':
    'Scores 100% when the mandate is actively accepting pitches now, 0% when closed, paused, or using an external form.',
  // Dimension sentences
  'Bidang belum dinyatakan oleh salah satu pihak.': 'Field is not stated by one of the sides yet.',
  'Bidang {source} sesuai dengan mandat.': 'Field {source} matches this mandate.',
  'Mandat mencari bidang {target}; produk Anda di bidang {source}.': 'This mandate looks for {target}; your product is in {source}.',
  'Mandat tidak mencantumkan kata kunci topik.': 'This mandate lists no topic keywords.',
  'Semua kata kunci mandat ditemukan: {matched}.': 'All mandate keywords found: {matched}.',
  'Belum ada kata kunci mandat yang ditemukan: {missing}.': 'None of the mandate keywords found yet: {missing}.',
  'Ditemukan: {matched}. Belum muncul: {missing}.': 'Found: {matched}. Not found yet: {missing}.',
  'Tahap {stage} diterima mandat.': 'Stage {stage} is accepted by this mandate.',
  'Mandat menerima tahap {accepted}; produk Anda {stage}.': 'This mandate accepts {accepted}; your product is at {stage}.',
  'TKT {tkt} memenuhi preferensi TKT {min} ke atas.': 'TKT {tkt} meets the TKT {min}+ preference.',
  'Mandat mencari TKT {min} ke atas; produk Anda TKT {tkt}.': 'This mandate looks for TKT {min} or above; your product is TKT {tkt}.',
  'Mandat mencari TKT {min} ke atas; TKT produk belum dinyatakan.': 'This mandate looks for TKT {min} or above; product TKT is not stated yet.',
  'Produk Anda menyatakan TKT {tkt}.': 'Your product states TKT {tkt}.',
  'Tahap dan TKT belum cukup untuk dibandingkan.': 'Stage and TKT are not complete enough to compare yet.',
  'Kisaran dana belum dapat dibandingkan.': 'Funding range cannot be compared yet.',
  'Kisaran Anda ({source}) beririsan dengan mandat ({target}).': 'Your range ({source}) overlaps the mandate ({target}).',
  'Kisaran Anda ({source}) tidak beririsan dengan {target}, tetapi dukungan sebagian diterima.':
    'Your range ({source}) does not overlap {target}, but partial support is accepted.',
  'Kisaran Anda ({source}) tidak beririsan dengan {target}.': 'Your range ({source}) does not overlap {target}.',
  'Kisaran dana sudah dibandingkan.': 'Funding range has been compared.',
  'Bentuk kerja sama belum dinyatakan.': 'Form of partnership is not stated yet.',
  'Bentuk kerja sama {source} diterima mandat.': 'Partnership form {source} is accepted by this mandate.',
  'Mandat menerima {target}; kebutuhan Anda {source}.': 'This mandate accepts {target}; your need is {source}.',
  'Mandat tidak mencantumkan syarat wajib saat pengajuan.': 'This mandate lists no required items at submission.',
  'Syarat wajib belum terpenuhi: {items}.': 'Required items not met: {items}.',
  'Syarat wajib perlu dilengkapi: {items}.': 'Required items needing completion: {items}.',
  '{passed} dari {total} syarat wajib terpenuhi.': '{passed} of {total} required items met.',
  'Belum ada daftar syarat untuk dinilai buktinya.': 'No checklist items to evaluate evidence against yet.',
  '{provided} tersedia, {reviewed} sudah diperiksa, dari {applicable} syarat.': '{provided} provided, {reviewed} reviewed, of {applicable} requirements.',
  'Mandat sedang menerima pitching.': 'This mandate is currently taking pitches.',
  'Mandat sedang tidak menerima pitching.': 'This mandate is not taking pitches right now.',
  // Recommendations (058)
  'Cara meningkatkan kecocokan': 'How to improve the match',
  'Lihat semua ({n})': 'See all ({n})',
  'Langkah paling berdampak': 'Highest-impact steps',
  'Membantu kecocokan dengan: {partners}.': 'Improves fit with: {partners}.',
  'Perkiraan bila benar untuk produk Anda: {label} ({lower}–{upper})':
    'Estimate if true for your product: {label} ({lower}–{upper})',
  'Buat kebutuhan dukungan': 'Create a support need',
  'Buat kebutuhan dukungan untuk produk ini agar dana dan bentuk kerja sama bisa dinilai.':
    'Create a support need for this product so funding and partnership form can be scored.',
  'Syarat “{label}”': 'Requirement “{label}”',
  'Lengkapi syarat wajib ini agar pengajuan dapat dilanjutkan.': 'Complete this required item so your submission can proceed.',
  'Perjelas topik yang dicari investor': 'Clarify topics the investor looks for',
  'Investor ini mencari: {missing}. Bila sesuai dengan produk Anda, tambahkan sebagai kata kunci atau jelaskan di ringkasan.':
    'This investor looks for: {missing}. If this fits your product, add them as keywords or explain them in the summary.',
  'Perbarui TKT bila pengujian sudah maju': 'Update TKT if testing has progressed',
  'Mandat mencari TKT {min} ke atas; produk Anda TKT {tkt}. Bila uji terbaru sudah mencapai tingkat itu, perbarui TKT dan lampirkan buktinya.':
    'This mandate looks for TKT {min} or above; your product is TKT {tkt}. If recent testing reached that level, update TKT and attach evidence.',
  'Nyatakan TKT produk Anda': 'State your product TKT',
  'Nyatakan TKT produk Anda. Investor ini mencari TKT {min} ke atas.':
    'State your product TKT. This investor looks for TKT {min} or above.',
  'Tahap produk belum sesuai mandat ini': 'Product stage does not fit this mandate yet',
  'Mandat menerima tahap {accepted}; produk Anda {stage}. Perbarui tahap hanya bila produk sudah maju; jika belum, lihat investor lain.':
    'This mandate accepts {accepted}; your product is {stage}. Update the stage only if the product has progressed; otherwise look at other investors.',
  'Lengkapi kisaran biaya kebutuhan ini agar investor dapat membandingkan.':
    'Complete this need cost range so investors can compare.',
  'Sesuaikan cakupan atau kisaran biaya': 'Review scope or cost range',
  'Kisaran Anda ({source}) tidak beririsan dengan {target}. Pertimbangkan menerima dukungan sebagian atau menyesuaikan cakupan bila sesuai.':
    'Your range ({source}) does not overlap {target}. Consider accepting partial support or adjusting scope if appropriate.',
  'Periksa bentuk kerja sama': 'Review form of partnership',
  'Mandat menerima {target}; kebutuhan Anda {source}. Ubah hanya bila bentuk itu sesuai dengan rencana Anda.':
    'This mandate accepts {target}; your need is {source}. Change it only if that form fits your plan.',
  'Lampirkan berkas bukti': 'Attach evidence files',
  'Lampirkan bukti untuk: {items}.': 'Attach evidence for: {items}.',
  'Bidang mandat berbeda dengan produk Anda': 'Mandate field differs from your product',
  'Mandat ini untuk bidang {target}; produk Anda {source}. Bila produk juga melayani bidang itu, jelaskan di ringkasan; jika tidak, lihat investor lain.':
    'This mandate is for {target}; your product is {source}. If your product also serves that field, explain it in the summary; otherwise look at other investors.',
  'Penerimaan sedang tidak dibuka': 'Intake is not open right now',
  'Investor ini sedang tidak menerima pitching. Simpan atau ikuti investor ini untuk kabar berikutnya.':
    'This investor is not taking pitches right now. Save or follow this investor for updates.',
  'Lihat investor lain untuk produk ini': 'See other investors for this product',
  'Perbarui kata kunci': 'Update keywords',
  'Perbarui TKT': 'Update TKT',
  'Lampirkan berkas': 'Attach files',
  'Perbarui wewenang': 'Update authority',
  'Perbarui fakta': 'Update facts',
  'Lengkapi kisaran': 'Complete range',
  'Ubah bentuk kerja sama': 'Change partnership form',
  'Kembali ke kecocokan': 'Back to matches',
  'Perubahan baru terlihat investor setelah versi baru diterbitkan.':
    'Investors see your changes only after you publish the new version.',
  'Terbitkan, lalu kembali ke kecocokan': 'Publish, then return to matches',
};
