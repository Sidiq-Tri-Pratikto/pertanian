'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { send, type Me } from '@/api/client';
import { ApiError } from '@/api/errors';
import { ContextSwitcher, type ContextOption } from '@/components/tr/ContextSwitcher';
import { Status } from '@/components/tr/Status';

export function contextOptions(me: Me): ContextOption[] {
  return [
    { id: me.personal_party_id, kind: 'personal', name: me.account.display_name },
    ...(me.organizations ?? []).map((organization) => ({ id: organization.party_id, kind: 'organization' as const, name: organization.name })),
  ];
}

/**
 * Who the account acts as, in the bar of every signed-in screen (UX-02). A switch reloads the page in the new
 * context and is announced without moving focus; a failure keeps the old context and says why.
 */
export function ContextBar({ me }: { me: Me }) {
  const router = useRouter();
  const options = contextOptions(me);
  const [value, setValue] = useState(me.active_party_id);
  const [notice, setNotice] = useState<{ tone: 'success' | 'danger'; label: string; body?: string } | null>(null);

  async function change(partyId: string) {
    const previous = value;
    setValue(partyId);
    try {
      await send('PUT', '/api/v1/me/context', { party_id: partyId });
      const name = options.find((option) => option.id === partyId)?.name ?? '';
      setNotice({ tone: 'success', label: `Sekarang bertindak sebagai ${name}` });
      router.refresh();
    } catch (error) {
      setValue(previous);
      const failure = ApiError.from(error);
      setNotice({ tone: 'danger', label: 'Konteks tidak berubah', body: failure.message });
    }
  }

  return (
    <div className="tr-stack">
      <ContextSwitcher id="konteks" value={value} options={options} onChange={change} />
      <div aria-live="polite">
        {notice ? (
          <Status tone={notice.tone} label={notice.label}>
            {notice.body ? <p>{notice.body}</p> : null}
          </Status>
        ) : null}
      </div>
    </div>
  );
}
