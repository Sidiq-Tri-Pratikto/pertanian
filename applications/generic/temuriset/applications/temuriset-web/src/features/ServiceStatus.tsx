'use client';

import { useEffect, useState } from 'react';

import { getCapabilities, type CapabilityManifest } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';

type State = { kind: 'loading' } | { kind: 'available'; manifest: CapabilityManifest } | { kind: 'failed'; error: ApiError };

/** States whether the service answers, and keeps every screen usable when it does not. */
export function ServiceStatus() {
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getCapabilities().then(
      (manifest) => active && setState({ kind: 'available', manifest }),
      (error: unknown) => active && setState({ kind: 'failed', error: ApiError.from(error) }),
    );
    return () => {
      active = false;
    };
  }, [attempt]);

  if (state.kind === 'loading') {
    return <Status tone="neutral" label="Memeriksa layanan…" live />;
  }

  if (state.kind === 'failed') {
    const { error } = state;
    return (
      <Status tone="warning" icon="alert" label="Layanan belum tersedia" live="alert">
        <p>{error.message}</p>
        {error.requestId ? <p className="tr-muted tr-sys-type-support">ID referensi: {error.requestId}</p> : null}
        {error.recovery.retryable ? (
          <div className="tr-row">
            <Button
              icon="refresh"
              onClick={() => {
                setState({ kind: 'loading' });
                setAttempt((value) => value + 1);
              }}>
              Coba lagi
            </Button>
          </div>
        ) : null}
      </Status>
    );
  }

  return (
    <Status tone="neutral" icon="check" label="Layanan tersedia" live>
      <p>{`Versi ${state.manifest.source_release}. Fitur lainnya segera hadir.`}</p>
    </Status>
  );
}
