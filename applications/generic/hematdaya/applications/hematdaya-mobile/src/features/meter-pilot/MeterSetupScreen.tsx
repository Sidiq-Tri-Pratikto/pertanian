import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useFocusEffect, useIsFocused } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError } from '@/api/errors';
import {
  confirmMeterEnrollment, getDeviceCatalog, getMeterEnrollment, PILOT_METER_ID, startMeterEnrollment,
  type MeterEnrollment,
} from '@/api/meter-pilot';
import { retryDelay, shouldRetry } from '@/api/query-client';
import { HDButton } from '@/components/hd/HDButton';
import { HDNotice } from '@/components/hd/HDNotice';
import { HDProgressStatus } from '@/components/hd/HDProgressStatus';
import { HDScreen } from '@/components/hd/HDScreen';
import { HDText } from '@/components/hd/HDText';
import { HDTextField } from '@/components/hd/HDTextField';
import { useScopedSummary } from '@/features/energy/useSummary';
import { errorMessage } from '@/features/localization/error-copy';
import { useCopy, useLabels } from '@/features/localization/messages';
import { useTabNavigation } from '@/features/navigation';
import { isKnownOffline, useConnectivity } from '@/features/offline/useConnectivity';
import { SessionEndedNotice } from '@/features/workspace/SessionEndedNotice';
import { useWorkspace } from '@/features/workspace/WorkspaceProvider';
import { formatDateTime } from '@/lib/format';
import { randomToken } from '@/lib/random';

/** Enrollment starts only after the owner signs in and explicitly requests setup. */
export function MeterSetupScreen() {
  const say = useCopy();
  const labels = useLabels();
  const { back, openImport } = useTabNavigation();
  const { pilot, status, credentialGeneration } = useWorkspace();
  useConnectivity();
  const offline = isKnownOffline();
  const catalog = useQuery({
    queryKey: ['device-catalog'], queryFn: getDeviceCatalog, enabled: !offline,
  });
  const meter = catalog.data?.devices.find((device) => device.id === PILOT_METER_ID);
  const available = catalog.isSuccess && meter?.status === 'available' && !offline;

  return (
    <HDScreen title={labels.connectMeter} onBack={back}>
      <SessionEndedNotice />
      {offline ? (
        <HDNotice tone="attention" title={say('Aplikasi sedang offline', 'The app is offline')} live>
          {say('Sambungkan perangkat ini ke internet untuk memeriksa sambungan alat ukur.',
            'Reconnect this device to check the meter connection.')}
        </HDNotice>
      ) : null}
      <HDProgressStatus
        state={!offline && catalog.isPending ? 'loading' : null}
        label={say('Memuat alat ukur…', 'Loading meters…')}
      />
      <SetupFailure error={catalog.error} label={say('Katalog belum dapat dimuat', 'Could not load the catalog')} />
      {meter ? (
        <>
          <HDText variant="section">{meter.name}</HDText>
          {meter.status === 'planned' ? (
            <HDNotice title={say('Direncanakan', 'Planned')}>
              {say('Model ini belum tersedia untuk disambungkan. Coba demo atau impor riwayat CSV.',
                'This model is not available to connect yet. Try the demo or import CSV history.')}
            </HDNotice>
          ) : (
            <HDText>
              {say('Uji coba ini memakai satu alat ukur yang disiapkan pengelola untuk satu peralatan colok.',
                'This pilot uses one operator-configured meter for one plug-in appliance.')}
            </HDText>
          )}
        </>
      ) : catalog.isSuccess ? <HDText>{say('Belum ada alat ukur dalam katalog.', 'No meters in the catalog yet.')}</HDText> : null}
      {available && status === 'ready' && !pilot ? <PilotSignIn /> : null}
      {pilot ? <PilotEnrollment key={credentialGeneration} available={available} offline={offline} /> : null}
      <HDButton variant="text" onPress={openImport}>{labels.importHistory}</HDButton>
    </HDScreen>
  );
}

function PilotSignIn() {
  const say = useCopy();
  const { openPilot } = useWorkspace();
  const [code, setCode] = useState('');
  const access = useRef<AbortController | null>(null);
  useFocusEffect(useCallback(() => () => access.current?.abort(), []));
  const signIn = useMutation({
    mutationFn: (request: AbortController) => openPilot(code.trim(), () => !request.signal.aborted),
    gcTime: 0,
    networkMode: 'always',
  });
  const update = (text: string) => {
    if (signIn.isError) signIn.reset();
    setCode(text);
  };
  return (
    <>
      <HDTextField label={say('Kode akses uji coba', 'Pilot access code')} value={code} onChange={update}
        help={say('Gunakan kode dari pengelola lokasi Anda.', 'Use the code from your site operator.')}
        editable={!signIn.isPending} secureTextEntry />
      <HDButton variant="primary" disabledReason={!code.trim() ? say('Masukkan kode akses.', 'Enter the access code.') : null} loading={signIn.isPending}
        onPress={() => {
          const request = new AbortController();
          access.current = request;
          signIn.mutate(request);
        }}>{say('Masuk ke uji coba', 'Sign in to the pilot')}</HDButton>
      <SetupFailure error={signIn.error} label={say('Belum dapat masuk', 'Could not sign in')} />
    </>
  );
}

function PilotEnrollment({ available, offline }: { available: boolean; offline: boolean }) {
  const say = useCopy();
  const labels = useLabels();
  const { openAsset } = useTabNavigation();
  const { workspace, credential, credentialGeneration, advanceScope, closePilot } = useWorkspace();
  const client = useQueryClient();
  const focused = useIsFocused();
  const [assetName, setAssetName] = useState('');
  const siteId = workspace!.siteId;
  const key = ['meter-enrollment', siteId, credentialGeneration] as const;
  const startKey = [...key, 'start-intent'] as const;
  const confirmKey = [...key, 'confirm-intent'] as const;
  const refreshed = useRef<string | null>(null);

  const enrollment = useQuery<MeterEnrollment>({
    queryKey: key,
    queryFn: () => {
      const id = client.getQueryData<MeterEnrollment>(key)?.id;
      if (!id || !credential) throw ApiError.revoked();
      return getMeterEnrollment(id, credential);
    },
    enabled: (query) => available && focused && query.state.data !== undefined,
    refetchInterval: (query) => available && focused && query.state.status !== 'error' &&
      (query.state.data?.status === 'waiting' || query.state.data?.status === 'ready') ? 5_000 : false,
  });

  const summary = useScopedSummary({ kind: 'all-active' }, enrollment.data?.status === 'connected', focused);
  const freshness = summary.data?.source_freshness?.find((source) => source.origin === 'live' &&
    source.asset_id === enrollment.data?.asset_id);
  const publish = async (result: MeterEnrollment) => {
    if (!credential?.current()) return;
    await client.cancelQueries({ queryKey: key, exact: true });
    if (!credential.current()) return;
    client.setQueryData(key, result);
  };

  // A recovered status response can be the first evidence that confirmation committed.
  const connectedId = enrollment.data?.status === 'connected' ? enrollment.data.id : null;
  useEffect(() => {
    if (!connectedId || connectedId === refreshed.current || !credential?.current()) return;
    refreshed.current = connectedId;
    void advanceScope().then(() => {
      if (!credential.current()) return;
      return client.invalidateQueries({
        predicate: ({ queryKey }) => queryKey[1] === siteId && queryKey[2] === credentialGeneration &&
          ['assets', 'summary', 'asset-summary', 'asset-history', 'scope-selection', 'insights'].includes(String(queryKey[0])),
      });
    });
  }, [advanceScope, client, connectedId, credential, credentialGeneration, siteId]);

  const start = useMutation({
    mutationFn: (operation: string) => startMeterEnrollment(siteId, operation, credential!),
    onSuccess: (result) => {
      client.removeQueries({ queryKey: startKey, exact: true });
      return publish(result);
    },
    retry: shouldRetry,
    retryDelay,
    networkMode: 'always',
  });
  const confirm = useMutation({
    mutationFn: ({ id, name, operation }: { id: string; name: string; operation: string }) =>
      confirmMeterEnrollment(id, name, operation, credential!),
    onSuccess: (result) => {
      client.removeQueries({ queryKey: confirmKey, exact: true });
      return publish(result);
    },
    retry: shouldRetry,
    retryDelay,
    networkMode: 'always',
  });
  const current = enrollment.data;
  const busy = start.isPending || confirm.isPending;
  const changeName = (name: string) => {
    if (confirm.isError) confirm.reset();
    setAssetName(name);
  };
  const canStart = available && (!current || current.status === 'expired');
  const canConfirm = available && current?.status === 'ready';
  return (
    <>
      {canStart ? (
        <HDButton variant="primary" loading={start.isPending} onPress={() => {
          const operation = client.getQueryData<string>(startKey) ?? randomToken(16);
          client.setQueryData(startKey, operation);
          start.mutate(operation);
        }}>
          {current?.status === 'expired' ? say('Mulai sambungan baru', 'Start a new connection') : say('Mulai penyambungan', 'Start connecting')}
        </HDButton>
      ) : null}
      {current?.status === 'waiting' ? (
        <HDNotice tone="info" title={say('Menunggu pembacaan pertama', 'Waiting for the first reading')} live>
          {say('Nyalakan alat ukur yang sudah disiapkan pengelola. Status diperbarui setelah pembacaan diterima.',
            'Power on the operator-configured meter. The status updates when a reading arrives.')}
        </HDNotice>
      ) : null}
      {current?.status === 'ready' ? (
        <HDNotice tone="info" title={say('Pembacaan pertama diterima', 'First reading received')} live>
          {say('Beri nama peralatan yang diukur untuk mengonfirmasi sambungan.',
            'Name the appliance to confirm the connection.')}
        </HDNotice>
      ) : null}
      {canConfirm ? (
        <>
          <HDTextField label={say('Nama peralatan', 'Appliance name')} value={assetName} onChange={changeName}
            editable={!busy} required maxLength={60} />
          <HDButton variant="primary" loading={confirm.isPending} disabledReason={!assetName.trim() ? say('Masukkan nama peralatan.', 'Enter an appliance name.') : null}
            onPress={() => {
              const name = assetName.trim();
              const before = client.getQueryData<{ id: string; name: string; operation: string }>(confirmKey);
              const operation = before?.id === current.id && before.name === name ? before.operation : randomToken(16);
              const intent = { id: current.id, name, operation };
              client.setQueryData(confirmKey, intent);
              confirm.mutate(intent);
            }}>{say('Konfirmasi sambungan', 'Confirm connection')}</HDButton>
        </>
      ) : null}
      {current?.status === 'expired' ? (
        <HDNotice tone="attention" title={say('Penyambungan kedaluwarsa', 'Setup expired')} live>
          {say('Mulai sambungan baru saat alat ukur siap.', 'Start a new connection when the meter is ready.')}
        </HDNotice>
      ) : null}
      {current?.status === 'connected' && current.asset_id ? (
        <HDNotice tone={freshness?.state === 'stale' ? 'attention' : 'success'}
          title={freshness?.state === 'stale' ? say('Pembacaan alat ukur terlambat', 'Meter readings are delayed')
            : say('Alat ukur terhubung', 'Meter connected')}
          live action={<HDButton onPress={() => openAsset(current.asset_id!)}>{say('Lihat riwayat peralatan', 'View appliance history')}</HDButton>}>
          {freshness?.last_capture_at && summary.data
            ? say(`Pembacaan terakhir: ${formatDateTime(freshness.last_capture_at, summary.data.window.timezone)}.`,
              `Last reading: ${formatDateTime(freshness.last_capture_at, summary.data.window.timezone)}.`)
            : say('Pembacaan pertama sudah dikonfirmasi.', 'The first reading has been confirmed.')}
        </HDNotice>
      ) : null}
      {available && current && current.status !== 'expired' && !enrollment.isError ? (
        <HDButton variant="text" icon="refresh" loading={enrollment.isFetching} disabledReason={busy ? say('Tunggu permintaan selesai.', 'Wait for the request to finish.') : null}
          onPress={() => { void enrollment.refetch(); if (current.status === 'connected') summary.refresh(); }}>
          {labels.checkStatus}
        </HDButton>
      ) : null}
      <SetupFailure error={start.error ?? confirm.error ?? enrollment.error}
        label={say('Sambungan belum dapat diperbarui', 'Could not update the connection')} />
      <HDButton variant="text" onPress={() => { void closePilot(); }}>
        {say('Keluar dari uji coba', 'Sign out of the pilot')}
      </HDButton>
      {(offline || enrollment.isError) && current ? <HDText tone="secondary">
        {say('Ini status terakhir yang berhasil diperiksa.',
          'This is the last confirmed status.')}
      </HDText> : null}
    </>
  );
}

/** Render the public error and its reference, never the transport or input. */
function SetupFailure({ error, label }: { error: unknown; label: string }) {
  const say = useCopy();
  if (!error) return null;
  const failure = ApiError.from(error);
  return <HDProgressStatus state="failure" label={label} detail={[
    errorMessage(failure),
    failure.requestId ? say(`ID referensi: ${failure.requestId}.`, `Reference ID: ${failure.requestId}.`) : null,
  ].filter(Boolean).join(' ')} />;
}
