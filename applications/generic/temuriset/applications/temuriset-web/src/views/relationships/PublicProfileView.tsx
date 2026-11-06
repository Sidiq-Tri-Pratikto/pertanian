import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { SummaryList } from '@/components/tr/SummaryList';
import { publicRows, type Profile } from '@/features/relationships/model';
import { PROVENANCE } from '@/views/parts';

function Inventions({ items }: { items: Profile['inventions'] }) {
  return (
    <ul className="tr-stack">
      {items.map((item) => (
        <li key={item.id}>
          <Link className="tr-link" href={`/inventions/${item.id}`}>{item.title}</Link>
          <p className="tr-muted tr-sys-type-support">{item.role}</p>
        </li>
      ))}
    </ul>
  );
}

/** S16 uses the anonymous projection and can render without an account. */
export function PublicProfileView({ profile }: { profile: Profile | null }) {
  return (
    <Screen persona="inovator" title={profile?.name ?? 'Profil publik'} subtitle={profile ? 'Profil publik' : undefined} provenance={PROVENANCE}>
      {!profile ? <EmptyState icon="lock" title="Profil tidak ditemukan">Periksa alamat profil yang Anda buka.</EmptyState> :
        profile.nothing_published ? <EmptyState icon="question" title="Belum ada yang dipublikasikan">Biografi, inovasi, atau data Kerja Sama yang diizinkan akan tampil di sini.</EmptyState> : (
          <>
            {profile.bio ? <section className="tr-panel tr-stack" aria-labelledby="profil-bio">
              <h2 id="profil-bio" className="tr-sys-type-heading-sm">Tentang</h2>
              <p>{profile.bio}</p>
            </section> : null}
            {profile.inventions.length ? <section className="tr-panel tr-stack" aria-labelledby="profil-inovasi">
              <h2 id="profil-inovasi" className="tr-sys-type-heading-sm">Inovasi terbit</h2>
              <Inventions items={profile.inventions} />
            </section> : null}
            {profile.relationships.length ? <section className="tr-stack" aria-labelledby="profil-kerjasama">
              <h2 id="profil-kerjasama" className="tr-sys-type-heading-sm">Kerja Sama</h2>
              {profile.relationships.map((relationship) => (
                <article key={relationship.id} className="tr-panel tr-stack">
                  <h3 className="tr-sys-type-label">{relationship.role}</h3>
                  {relationship.counterpart_party_id && relationship.counterpart_name ? (
                    <Link className="tr-link" href={`/profiles/${relationship.counterpart_party_id}`}>{relationship.counterpart_name}</Link>
                  ) : null}
                  <SummaryList rows={publicRows(relationship.fields)} />
                  {relationship.inventions.length ? <Inventions items={relationship.inventions} /> : null}
                </article>
              ))}
            </section> : null}
          </>
        )}
    </Screen>
  );
}
