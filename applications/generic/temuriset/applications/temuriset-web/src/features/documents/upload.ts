import { send } from '@/api/client';
import { ApiError, readFailure } from '@/api/errors';
import type { UploadIntent } from '@/features/documents/model';

export type Upload = { promise: Promise<void>; cancel: () => void };

/**
 * Declares the file, then streams it to the same-origin intent URL with progress. XMLHttpRequest is used because
 * `fetch` reports no upload progress.
 */
export function uploadFile(file: File, title: string, actingPartyId: string, onProgress: (fraction: number) => void): Upload {
  let request: XMLHttpRequest | null = null;
  let cancelled = false;
  const promise = (async () => {
    const intent = await send<UploadIntent>('POST', '/api/v1/documents/upload-intents', {
      acting_party_id: actingPartyId,
      title,
      kind: 'evidence',
      media_type: file.type,
      size_bytes: file.size,
    });
    if (cancelled) throw new DOMException('cancelled', 'AbortError');
    await new Promise<void>((resolve, reject) => {
      request = new XMLHttpRequest();
      request.open('PUT', intent.upload_url);
      request.upload.onprogress = (event) => event.lengthComputable && onProgress(event.loaded / event.total);
      request.onload = async () => {
        if (request!.status === 202) return resolve();
        reject(await readFailure(new Response(request!.responseText, { status: request!.status })));
      };
      request.onerror = () => reject(ApiError.unreachable());
      request.onabort = () => reject(new DOMException('cancelled', 'AbortError'));
      request.send(file);
    });
  })();
  return {
    promise,
    cancel: () => {
      cancelled = true;
      request?.abort();
    },
  };
}
