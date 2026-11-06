import type { Metadata } from 'next';

import { ApiError } from '@/api/errors';
import { serverGet } from '@/api/server';
import type { DocumentView } from '@/features/documents/model';
import type { Pitch } from '@/features/pitches/model';
import type { OwnFile } from '@/features/pitches/RevisionPanel';
import { tabOf } from '@/features/pitches/workspace';
import { requireMe } from '@/features/session';
import { NoAccessView, WorkspaceView, type Room } from '@/views/pitches/WorkspaceView';

export const metadata: Metadata = { title: 'Pitching' };

type Props = { params: Promise<{ id: string }>; searchParams: Promise<{ terkirim?: string; tab?: string }> };

/** Available versions of the requester's own documents, to attach to answers and share on resubmission. */
async function ownFiles(): Promise<OwnFile[]> {
  const documents = await serverGet<DocumentView[]>('/api/v1/documents');
  return documents.flatMap((document) =>
    document.versions.filter((version) => version.file_state === 'AVAILABLE').map((version) => ({ document_id: document.id, version: version.number, title: document.title })),
  );
}

export default async function PitchPage({ params, searchParams }: Props) {
  const { id } = await params;
  const query = await searchParams;
  const me = await requireMe(`/pitches/${id}`);
  let pitch: Pitch;
  try {
    pitch = await serverGet<Pitch>(`/api/v1/pitches/${encodeURIComponent(id)}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === 'NOT_FOUND') return <NoAccessView me={me} />;
    throw error;
  }
  const base = `/api/v1/pitches/${encodeURIComponent(id)}` as const;
  const [files, next, schedule, messages, tasks] = await Promise.all([
    pitch.allowed_actions.includes('answer') ? ownFiles() : Promise.resolve([]),
    serverGet<Room['next']>(`${base}/next-action`),
    serverGet<Room['schedule']>(`${base}/schedule`),
    serverGet<Room['messages']>(`${base}/messages`),
    serverGet<Room['tasks']>(`${base}/tasks`),
  ]);
  return <WorkspaceView me={me} pitch={pitch} tab={tabOf(query.tab)} files={files} justSent={query.terkirim === '1'} room={{ next, schedule, messages, tasks }} />;
}
