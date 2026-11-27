import Link from 'next/link';

import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { SummaryList } from '@/components/tr/SummaryList';
import { publicRows, type Profile } from '@/features/relationships/model';
import { PROVENANCE } from '@/views/parts';
import { t } from '@/features/i18n/t';

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
    <Screen persona="inovator" title={profile?.name ?? t('Profil publik')} subtitle={profile ? t('Profil publik') : undefined} provenance={PROVENANCE}>
      {!profile ? <EmptyState icon="lock" title={t('Profil tidak ditemukan')}>{t('Periksa alamat profil yang Anda buka.')}</EmptyState> :
        profile.nothing_published ? <EmptyState icon="question" title={t('Belum ada yang dipublikasikan')}>{t('Biografi, inovasi, atau data Kerja Sama yang diizinkan akan tampil di sini.')}</EmptyState> : (
          <>
            {profile.bio ? <section className="tr-panel tr-stack" aria-labelledby="profil-bio">
              <h2 id="profil-bio" className="tr-sys-type-heading-sm">{t('Tentang')}</h2>
              <p>{profile.bio}</p>
            </section> : null}
            {profile.inventions.length ? <section className="tr-panel tr-stack" aria-labelledby="profil-inovasi">
              <h2 id="profil-inovasi" className="tr-sys-type-heading-sm">{t('Inovasi terbit')}</h2>
              <Inventions items={profile.inventions} />
            </section> : null}
            {profile.relationships.length ? <section className="tr-stack" aria-labelledby="profil-kerjasama">
              <h2 id="profil-kerjasama" className="tr-sys-type-heading-sm">{t('Kerja Sama')}</h2>
              {profile.relationships.map((relationship) => (
                <article key={relationship.id} className="tr-panel tr-stack">
                  <h3 className="tr-sys-type-label">{t(relationship.role)}</h3>
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
