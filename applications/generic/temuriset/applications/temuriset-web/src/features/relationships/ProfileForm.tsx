'use client';

import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import { send } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Checkbox } from '@/components/tr/Checkbox';
import { Status } from '@/components/tr/Status';
import { TextArea } from '@/components/tr/TextArea';
import { VersionConflict } from '@/components/tr/VersionConflict';
import type { ProfileSettings } from '@/features/relationships/model';
import { RelationshipError } from '@/features/relationships/RelationshipError';

export function ProfileForm({ profile }: { profile: ProfileSettings }) {
  const router = useRouter();
  const [saved, setSaved] = useState<ProfileSettings | null>(null);
  const [bio, setBio] = useState(profile.bio);
  const [published, setPublished] = useState(profile.published);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ failure: ApiError; attempt: number } | null>(null);
  const version = Math.max(profile.version, saved?.version ?? 0);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    try {
      const result = await send<ProfileSettings>('PUT', '/api/v1/profiles/me', {
        acting_party_id: profile.party_id, expected_version: version, bio, published,
      });
      setError(null);
      setSaved(result);
    } catch (failure) {
      setError((previous) => ({ failure: ApiError.from(failure), attempt: (previous?.attempt ?? 0) + 1 }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="tr-stack" onSubmit={submit}>
      {error?.failure.code === 'STALE_VERSION' ? <VersionConflict what={error.failure.message}
        currentVersion={error.failure.currentVersion?.toString()} onRefresh={() => { setError(null); router.refresh(); }} /> :
        error ? <RelationshipError error={error} prefix="bio" /> : null}
      <TextArea id="bio-bio" label="Biografi" rows={3} limit={2000} value={bio} onChange={setBio} />
      <Checkbox id="bio-published" label="Tampilkan biografi di profil publik" checked={published} onChange={setPublished} />
      <p className="tr-muted tr-sys-type-support">Pilihan ini hanya mengatur biografi. Inovasi terbit dan data Kerja Sama mengikuti izin masing-masing.</p>
      <div className="tr-row"><Button type="submit" intent="primary" busy={busy}>Simpan biografi</Button></div>
      {saved && !error ? <Status tone="success" live label={saved.published ? 'Biografi disimpan untuk publik' : 'Biografi disimpan secara privat'} /> : null}
    </form>
  );
}
