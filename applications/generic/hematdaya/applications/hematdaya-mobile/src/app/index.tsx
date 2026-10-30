import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { getHealth } from '@/api/client';
import { ApiError } from '@/api/errors';

type State = { kind: 'loading' } | { kind: 'ok'; status: string } | { kind: 'failed'; error: ApiError };

/** Proves the stack end to end: app, generated contract, service, failure envelope. Replace with the first feature. */
export default function HealthScreen() {
  const [state, setState] = useState<State>({ kind: 'loading' });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    getHealth().then(
      (health) => active && setState({ kind: 'ok', status: health.status }),
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

  return (
    <View style={styles.screen}>
      <Text accessibilityRole="header" style={styles.title}>
        hematdaya-mobile
      </Text>
      {state.kind === 'loading' && <ActivityIndicator accessibilityLabel="Checking the service" />}
      {state.kind === 'ok' && <Text>Service status: {state.status}</Text>}
      {state.kind === 'failed' && (
        <View accessibilityLiveRegion="polite" style={styles.failure}>
          <Text>{state.error.message}</Text>
          {state.error.requestId && <Text>Reference: {state.error.requestId}</Text>}
          {state.error.recovery.retryable && (
            <Pressable accessibilityRole="button" onPress={retry} style={styles.action}>
              <Text>Try again</Text>
            </Pressable>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 16, padding: 16 },
  title: { fontSize: 24, fontWeight: '600' },
  failure: { alignItems: 'center', gap: 8 },
  action: { minHeight: 48, minWidth: 48, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 16 },
});
