import type { Metadata } from 'next';
import { notFound } from 'next/navigation';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import type { Invention } from '@/features/portfolio/model';
import { requireMe } from '@/features/session';
import { fundingOn } from '@/features/needs/server';
import { DocumentsPanel } from '@/features/documents/DocumentsPanel';
import type { DocumentView } from '@/features/documents/model';
import { EditorView } from '@/views/portfolio/EditorView';

export const metadata: Metadata = { title: 'Ubah inovasi' };

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ step?: string }> };

export default async function EditInventionPage({ params, searchParams }: Props) {
  const { id } = await params;
  const me = await requireMe(`/inventions/${id}/edit`);
  let invention: Invention;
  try {
    invention = await serverGet<Invention>(`/api/v1/inventions/${encodeURIComponent(id)}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') notFound();
    throw error;
  }
  const documents = await serverGet<DocumentView[]>('/api/v1/documents');
  return (
    <EditorView
      me={me}
      invention={invention}
      initialStep={Number((await searchParams).step) || 1}
      documents={<DocumentsPanel me={me} initial={documents} />}
      fundingOn={await fundingOn()}
    />
  );
}
