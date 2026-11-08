import type { Summary } from '@/api/client';
import { currentCopy } from '@/features/localization/messages';

type ScopeIssue = Summary['scope']['issues'][number];
type NamedAsset = { asset_id: string; name: string };

export function scopeIssueCopy(issue: ScopeIssue, assets: NamedAsset[]): string {
  const [first, second] = issue.asset_ids.map((id) =>
    assets.find((asset) => asset.asset_id === id)?.name ?? currentCopy('Perangkat', 'Device'));
  switch (issue.type) {
    case 'parent_child':
      return currentCopy(`${first} sudah mencakup ${second}. Keduanya tidak dapat dijumlahkan.`,
        `${first} already includes ${second}. Their readings stay separate.`);
    case 'source_conflict':
      return currentCopy(`${first} memiliki lebih dari satu sumber untuk beban yang sama. Pilih sumber acuan; nilainya tidak dijumlahkan.`,
        `${first} has multiple sources for the same load. Choose a reference source.`);
    case 'shared_source':
      return currentCopy(`${first} dan ${second} memakai sumber yang sama pada waktu yang bertumpang tindih.`,
        `${first} and ${second} use the same source at overlapping times.`);
    case 'unconfirmed':
      return currentCopy(`Belum ada bukti bahwa ${first} dan ${second} mengukur beban yang terpisah.`,
        `Check that ${first} and ${second} measure separate loads.`);
    case 'unknown_overlap':
      return currentCopy(`Belum diketahui apakah ${first} dan ${second} mengukur beban yang terpisah.`,
        `We don’t know whether ${first} and ${second} measure separate loads.`);
  }
}
