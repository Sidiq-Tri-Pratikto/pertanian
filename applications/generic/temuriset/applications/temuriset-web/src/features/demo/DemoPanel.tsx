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
import { useMessages } from '@/features/i18n/LocaleProvider';

export type DemoAccount = components['schemas']['DemoAccount'];

const GROUPS = [
  { persona: 'inovator', title: 'inventors' },
  { persona: 'mitra', title: 'partners' },
] as const;

/** The labelled demo: sign in as a fictional account with no email, or reset every demo record (spec 021). */
export function DemoPanel({ accounts }: { accounts: DemoAccount[] }) {
  const router = useRouter();
  const words = useMessages().demo;
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
      await send('POST', '/api/v1/demo/reset');
      setNotice(words.resetDone);
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
        {words.title}
      </h2>
      <p className="tr-muted">{words.intro}</p>
      {GROUPS.map((group) => {
        const members = accounts.filter((account) => account.persona === group.persona);
        if (!members.length) return null;
        return (
          <section key={group.persona} className="tr-stack" aria-labelledby={`demo-${group.persona}`}>
            <h3 id={`demo-${group.persona}`} className="tr-sys-type-label">
              {words[group.title]}
            </h3>
            <ul className="tr-stack">
              {members.map((account) => (
                <li key={account.key} className="tr-row">
                  <Button busy={busy === account.key} busyLabel={words.signingIn} onClick={() => void signIn(account)}>
                    {words.signInAs(account.name)}
                  </Button>
                  <span className="tr-muted tr-sys-type-support" lang="id">
                    {account.summary}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        );
      })}
      <div className="tr-row">
        <Button id="atur-ulang-demo" onClick={() => setConfirming(true)}>
          {words.reset}
        </Button>
      </div>
      <div aria-live="polite">{notice ? <Status tone="success" label={notice} /> : null}</div>
      {failure ? (
        <Status tone="danger" label={words.failed} live="alert">
          <p>{failure}</p>
        </Status>
      ) : null}
      <Dialog
        open={confirming}
        onClose={() => setConfirming(false)}
        title={words.resetTitle}
        primary={{ label: words.resetConfirm, onClick: () => void reset(), busy: busy === 'reset', busyLabel: words.resetting, intent: 'danger' }}
        secondary={{ label: words.cancel, onClick: () => setConfirming(false) }}
        returnFocusId="atur-ulang-demo">
        <p>{words.resetBody}</p>
      </Dialog>
    </section>
  );
}
