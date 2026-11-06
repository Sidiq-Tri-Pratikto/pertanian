import { getResponse, send } from '@/api/client';
import type { components } from '@/api/schema.generated';

export type ImportStatus = components['schemas']['ImportStatusResponse'];
export type ExportStatus = components['schemas']['ExportStatusResponse'];
export type ExportRequest = components['schemas']['CreateExportRequest'];
export type PreviewRow = components['schemas']['PreviewRow'];

export async function validateImport(file: File, party: string, mapPrivate: boolean, key: string): Promise<ImportStatus> {
  const query = new URLSearchParams({ acting_party_id: party, map_private_notes: String(mapPrivate) });
  const response = await getResponse(`/api/v1/imports/validate?${query}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key },
    body: file,
  });
  return (await response.json()) as ImportStatus;
}

export async function readImport(id: string, offset = 0): Promise<ImportStatus> {
  const response = await getResponse(`/api/v1/imports/${id}?offset=${offset}`);
  return (await response.json()) as ImportStatus;
}

export function changeImport(
  id: string, action: 'apply' | 'cancel', party: string, version: number, key: string,
): Promise<ImportStatus> {
  const body: components['schemas']['ImportActionRequest'] = { acting_party_id: party, expected_version: version };
  return send('POST', `/api/v1/imports/${id}/${action}`, body, { idempotencyKey: key });
}

export function createExport(body: ExportRequest, key: string): Promise<ExportStatus> {
  return send('POST', '/api/v1/exports', body, { idempotencyKey: key });
}

export async function readExport(id: string): Promise<ExportStatus> {
  return (await (await getResponse(`/api/v1/exports/${id}`)).json()) as ExportStatus;
}

export async function downloadExport(id: string): Promise<void> {
  const response = await getResponse(`/api/v1/exports/${id}/download`);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = 'temuriset-export.json';
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
