import Link from 'next/link';

import type { Me } from '@/api/client';
import { EmptyState } from '@/components/tr/EmptyState';
import { Screen } from '@/components/tr/Screen';
import { Status } from '@/components/tr/Status';
import { SummaryList } from '@/components/tr/SummaryList';
import { AcceptInvitationButton } from '@/features/AccountForms';
import { ContextBar } from '@/features/ContextBar';
import { capabilityList, formatDateTime, INVITATION_STATUS, type InvitationDetail } from '@/features/organizations';
import { readPersona } from '@/features/persona';
import { PROVENANCE } from '@/views/parts';

/** What an invitation grants, shown before "Terima undangan". */
export function InvitationView({ me, token, invitation }: { me: Me; token: string; invitation: InvitationDetail | null }) {
  const persona = readPersona(me.account.persona) ?? 'inovator';
  return (
    <Screen persona={persona} current="profil" title="Undangan organisasi" provenance={PROVENANCE} context={<ContextBar me={me} />}>
      {invitation ? (
        <>
          <SummaryList
            rows={[
              { id: 'undangan-organisasi', label: 'Organisasi', value: invitation.organization_name },
              { id: 'undangan-kewenangan', label: 'Kewenangan', value: capabilityList(invitation.capabilities) },
              { id: 'undangan-berlaku', label: 'Berlaku sampai', value: formatDateTime(invitation.expires_at, me.account.time_zone) },
              { id: 'undangan-status', label: 'Status', value: INVITATION_STATUS[invitation.status] },
            ]}
          />
          {invitation.status === 'pending' ? (
            <AcceptInvitationButton token={token} />
          ) : (
            <Status tone="warning" label="Undangan ini tidak dapat diterima">
              <p>Minta undangan baru kepada pengelola organisasi.</p>
            </Status>
          )}
        </>
      ) : (
        <EmptyState
          icon="question"
          title="Undangan tidak ditemukan"
          action={
            <Link className="tr-link" href="/settings">
              Kembali ke profil
            </Link>
          }>
          Undangan hanya terbuka untuk akun dengan email yang diundang. Periksa bahwa Anda masuk dengan email tersebut.
        </EmptyState>
      )}
    </Screen>
  );
}
