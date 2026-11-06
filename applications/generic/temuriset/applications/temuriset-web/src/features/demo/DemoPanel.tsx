'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { send } from '@/api/client';
import type { components } from '@/api/schema.generated';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Dialog } from '@/components/tr/Dialog';
import { Status } from '@/components/tr/Status';
import { homeFor, readPersona } from '@/features/persona';

export type DemoAccount = components['schemas']['DemoAccount'];

/** The labelled demo: sign in as a fictional account with no email, or reset every demo record (spec 021). */
export function DemoPanel({ accounts }: { accounts: DemoAccount[] }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  async function signIn(account: DemoAccount) {
    setBusy(account.key);
    setFailure(null);
    try {
      await send('POST', '/api/v1/demo/sign-in', { key: account.key });
      router.push(homeFor(readPersona(account.persona) ?? 'inovator'));
    } catch (error) {
      setFailure(ApiError.from(error).message);
      setBusy(null);
    }
  }

  async function reset() {
    setBusy('reset');
    setFailure(null);
    try {
      await send('POST', '/api/v1/demo/reset', {});
      setNotice('Demo sudah diatur ulang. Akun nyata tidak berubah.');
    } catch (error) {
      setFailure(ApiError.from(error).message);
    } finally {
      setBusy(null);
      setConfirming(false);
    }
  }

  return (
    <section className="tr-panel tr-stack" aria-labelledby="akun-demo">
      <h2 id="akun-demo" className="tr-sys-type-heading-sm">
        Coba dengan akun demo
      </h2>
      <p className="tr-muted">Semua data di akun ini fiktif. Akun demo tidak menerima email dan tidak masuk statistik.</p>
      <ul className="tr-stack">
        {accounts.map((account) => (
          <li key={account.key} className="tr-row">
            <Button busy={busy === account.key} busyLabel="Masuk…" onClick={() => void signIn(account)}>
              {`Masuk sebagai ${account.name}`}
            </Button>
            <span className="tr-muted tr-sys-type-support">{`${account.fixture} · ${account.label}`}</span>
          </li>
        ))}
      </ul>
      <div className="tr-row">
        <Button id="atur-ulang-demo" onClick={() => setConfirming(true)}>
          Atur ulang demo
        </Button>
      </div>
      <div aria-live="polite">{notice ? <Status tone="success" label={notice} /> : null}</div>
      {failure ? (
        <Status tone="danger" label="Belum berhasil" live="alert">
          <p>{failure}</p>
        </Status>
      ) : null}
      <Dialog
        open={confirming}
        onClose={() => setConfirming(false)}
        title="Atur ulang demo?"
        primary={{ label: 'Atur ulang', onClick: () => void reset(), busy: busy === 'reset', busyLabel: 'Mengatur ulang…', intent: 'danger' }}
        secondary={{ label: 'Batal', onClick: () => setConfirming(false) }}
        returnFocusId="atur-ulang-demo">
        <p>Semua perubahan pada akun demo dihapus dan data fiktif dibuat ulang. Akun nyata tidak tersentuh.</p>
      </Dialog>
    </section>
  );
}
