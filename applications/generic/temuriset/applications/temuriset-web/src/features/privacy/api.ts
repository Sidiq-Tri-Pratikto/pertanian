import { getJson, getResponse, send } from '@/api/client';
import type { PrivacyInput, PrivacyRequest, Report, ReportInput } from '@/features/privacy/model';

export const readReports = () => getJson('/api/v1/reports');
export const readPrivacyRequests = () => getJson('/api/v1/privacy-requests');

export function submitReport(input: ReportInput, idempotencyKey: string): Promise<Report> {
  return send('POST', '/api/v1/reports', input, { idempotencyKey });
}

export function submitPrivacyRequest(input: PrivacyInput, idempotencyKey: string): Promise<PrivacyRequest> {
  return send('POST', '/api/v1/privacy-requests', input, { idempotencyKey });
}

export async function downloadExport(requestId: string): Promise<void> {
  const response = await getResponse(`/api/v1/privacy-requests/${encodeURIComponent(requestId)}/export`);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = 'temuriset-data.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
