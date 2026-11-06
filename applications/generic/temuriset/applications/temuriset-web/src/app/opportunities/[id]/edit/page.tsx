import type { Metadata } from 'next';

import type { Mandate } from '@/features/intake/model';
import { ownedOr404 } from '@/features/needs/server';
import { requireMe } from '@/features/session';
import { MandateEditView } from '@/views/intake/MandateEditView';

export const metadata: Metadata = { title: 'Ubah mandat' };

type Props = { params: Promise<{ id: string }> };

export default async function MandateEditPage({ params }: Props) {
  const { id } = await params;
  const me = await requireMe(`/opportunities/${id}/edit`);
  const mandate = await ownedOr404<Mandate>(`/api/v1/opportunities/${encodeURIComponent(id)}`);
  return <MandateEditView me={me} mandate={mandate} />;
}
