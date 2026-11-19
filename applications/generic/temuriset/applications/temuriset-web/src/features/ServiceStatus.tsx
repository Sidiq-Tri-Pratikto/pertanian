'use client';

import { useEffect, useState } from 'react';

import { getCapabilities } from '@/api/client';
import { ApiError } from '@/api/errors';
import { Button } from '@/components/tr/Button';
import { Status } from '@/components/tr/Status';

type State = { kind: 'loading' } | { kind: 'available' } | { kind: 'failed'; error: ApiError };

/** Says so when the service does not answer, with a retry when one helps; says nothing while it works. */
export function ServiceStatus() {
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getCapabilities().then(
      () => active && setState({ kind: 'available' }),
      (error: unknown) => active && setState({ kind: 'failed', error: ApiError.from(error) }),
    );
    return () => {
      active = false;
    };
  }, [attempt]);

  // A service that answers needs no banner on a business screen; only trouble is worth the reader's attention.
  if (state.kind !== 'failed') return null;

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
