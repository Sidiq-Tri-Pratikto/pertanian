'use client';

import { useEffect, useRef, useState } from 'react';

import { newIdempotencyKey } from '@/api/client';
import { ApiError } from '@/api/errors';

type Intent = { key: string; attempts: number };
type Block = { stopped: boolean; retryAt: number };

/** Keep an uncertain write's key until the service confirms that exact payload. */
export function useIntent<Input, Result>(submit: (input: Input, key: string) => Promise<Result>) {
  const intents = useRef(new Map<string, Intent>());
  const running = useRef(false);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<ApiError | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [blocks, setBlocks] = useState<Record<string, Block>>({});

  useEffect(() => {
    const delays = Object.values(blocks).filter((block) => !block.stopped).map((block) => block.retryAt);
    if (!delays.length) return;
    const timer = setTimeout(() => {
      const now = Date.now();
      setBlocks((current) => Object.fromEntries(
        Object.entries(current).filter(([, block]) => block.stopped || block.retryAt > now),
      ));
    }, Math.max(0, Math.min(...delays) - Date.now()));
    return () => clearTimeout(timer);
  }, [blocks]);

  function blocked(input: Input): string | null {
    const block = blocks[JSON.stringify(input)];
    if (!block) return null;
    return block.stopped ? 'Periksa hasil permintaan sebelum mengirim ulang.' : 'Tunggu sebentar sebelum mencoba lagi.';
  }

  async function run(input: Input): Promise<Result | null> {
    if (running.current || blocked(input)) return null;
    const signature = JSON.stringify(input);
    const current = intents.current.get(signature) ?? { key: newIdempotencyKey(), attempts: 0 };
    current.attempts += 1;
    intents.current.set(signature, current);
    running.current = true;
    setBusy(true);
    setFailure(null);
    try {
      const result = await submit(input, current.key);
      intents.current.delete(signature);
      return result;
    } catch (error) {
      const next = ApiError.from(error);
      const stopped = !next.recovery.retryable || current.attempts >= (next.recovery.max_attempts ?? 1);
      const delay = next.recovery.retry_after_seconds ?? 0;
      if (stopped || delay) {
        setBlocks((previous) => ({ ...previous, [signature]: { stopped, retryAt: Date.now() + delay * 1000 } }));
      }
      setFailure(next);
      setAttempt((count) => count + 1);
      return null;
    } finally {
      running.current = false;
      setBusy(false);
    }
  }

  return { run, blocked, busy, failure, attempt };
}
