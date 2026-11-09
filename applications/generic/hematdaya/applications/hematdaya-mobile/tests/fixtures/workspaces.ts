import type { DemoSession } from '@/api/client';
import { attestWorkspace, saveWorkspace, type Workspace } from '@/features/workspace/workspace-store';

/** Install a server-confirmed control record without retesting attestation in each feature suite. */
export async function seedConfirmedWorkspace(workspace: Workspace) {
  const attestation = await attestWorkspace(workspace);
  await saveWorkspace(workspace, attestation);
  return attestation;
}

export function attestedResponse(workspace: Workspace): DemoSession {
  if (workspace.scenarioId === null) throw new Error('A demo fixture needs a scenario');
  return { token: workspace.token, site_id: workspace.siteId, scenario_id: workspace.scenarioId,
    expires_at: workspace.expiresAt, initial_period: workspace.initialPeriod };
}
