import { useEffect, useState } from 'react';

import { getCapabilities, type CapabilityManifest } from '@/api/client';
import { ApiError } from '@/api/errors';

type CapabilitiesState =
  | { kind: 'loading' }
  | { kind: 'available'; manifest: CapabilityManifest }
  | { kind: 'failed'; error: ApiError };

/** Reads the service manifest. It explains what is available and never decides what is allowed. */
export function useCapabilities() {
  const [state, setState] = useState<CapabilitiesState>({ kind: 'loading' });
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

  const retry = () => {
    setState({ kind: 'loading' });
    setAttempt((value) => value + 1);
  };

  return { state, retry };
}
