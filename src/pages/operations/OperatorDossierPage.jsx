import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth.js';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchOperatorDossier, updateOperatorPreferences } from '@/services/api/operationsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import Badge from '@/components/common/Badge.jsx';
import Switch from '@/components/common/Switch.jsx';
import { UserRound } from 'lucide-react';

export default function OperatorDossierPage() {
  const { operator } = useAuth();
  const { data, isLoading, error, refetch } = useAsyncData(
    () => fetchOperatorDossier(operator?.id ?? 'me'),
    [operator?.id]
  );
  const [savingKey, setSavingKey] = useState(null);
  const [preferences, setPreferences] = useState(null);

  const activePrefs = preferences ?? data?.preferences;

  const handleToggle = async (key, value) => {
    setSavingKey(key);
    const next = { ...activePrefs, [key]: value };
    setPreferences(next);
    try {
      await updateOperatorPreferences(data.id, next);
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <div className="p-8 max-w-[1200px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Operations"
        title="Operator Dossier"
        description="Confidential personnel record & system preferences."
        actions={data && <Badge tone="info">CLEARANCE: {data.clearance}</Badge>}
      />

      {error && <ErrorState onRetry={refetch} message="Operator dossier could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          <div className="panel p-5">
            {isLoading || !data ? (
              <Skeleton rows={4} className="h-10 w-full" />
            ) : (
              <div className="flex items-start gap-4">
                <div className="w-20 h-20 rounded-sm bg-surface-2 flex items-center justify-center shrink-0">
                  <UserRound size={32} className="text-ink-muted" strokeWidth={1.25} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="font-display text-2xl">{data.name}</p>
                    <Badge tone="success">STATUS: {data.status}</Badge>
                  </div>
                  <p className="text-accent-gold text-sm">{data.rank}</p>

                  <dl className="grid grid-cols-2 gap-x-6 gap-y-3 mt-4 text-sm">
                    <div>
                      <dt className="label-eyebrow">Operator ID</dt>
                      <dd className="text-ink-secondary mt-0.5">{data.operatorId}</dd>
                    </div>
                    <div>
                      <dt className="label-eyebrow">Assigned Unit</dt>
                      <dd className="text-ink-secondary mt-0.5">{data.assignedUnit}</dd>
                    </div>
                    <div>
                      <dt className="label-eyebrow">Date of Entry</dt>
                      <dd className="text-ink-secondary mt-0.5">{data.dateOfEntry}</dd>
                    </div>
                    <div>
                      <dt className="label-eyebrow">Biometric Hash</dt>
                      <dd className="text-ink-secondary mt-0.5 font-mono">{data.biometricHash}</dd>
                    </div>
                  </dl>
                </div>
              </div>
            )}
          </div>

          <div className="panel p-4">
            <h3 className="font-display text-lg mb-4">System Preferences</h3>
            {isLoading || !activePrefs ? (
              <Skeleton rows={2} className="h-10 w-full" />
            ) : (
              <div className="flex flex-col gap-4">
                <Switch
                  id="tactical-mode"
                  label="Tactical Mode (Dark)"
                  description="Force high-contrast UI"
                  checked={activePrefs.tacticalModeDark}
                  onChange={(v) => handleToggle('tacticalModeDark', v)}
                />
                <Switch
                  id="data-stream-alerts"
                  label="Data Stream Alerts"
                  description="Audio ping on match"
                  checked={activePrefs.dataStreamAlerts}
                  onChange={(v) => handleToggle('dataStreamAlerts', v)}
                />
                {savingKey && <p className="text-xs text-ink-muted">Saving...</p>}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
