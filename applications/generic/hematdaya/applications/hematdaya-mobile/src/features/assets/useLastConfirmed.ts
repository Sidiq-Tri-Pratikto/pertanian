import { useState } from 'react';

type ConfirmedQuery<T> = { data: T | undefined; isPlaceholderData: boolean };

/**
 * The newest data, or the last value the service confirmed. `keepPreviousData` only applies while a query is
 * pending, so a failed period change leaves `data` undefined. Mount the caller under a key for its site, so a
 * kept value never crosses workspaces.
 */
export function useLastConfirmed<T>(query: ConfirmedQuery<T>): T | undefined {
  const [kept, setKept] = useState<T | undefined>(undefined);
  if (query.data !== undefined && !query.isPlaceholderData && query.data !== kept) {
    setKept(query.data);
  }
  return query.data ?? kept;
}
