import { useState } from 'react';
import { Archive } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchEvidenceVault } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import EvidenceCard from '@/components/investigation/EvidenceCard.jsx';

export default function EvidenceVaultPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchEvidenceVault, []);
  const [selectedId, setSelectedId] = useState(null);

  const selected = data?.find((item) => item.itemId === selectedId) ?? data?.[0] ?? null;

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Analytics"
        title="Evidence Vault"
        description="Cross-case evidence of crime scenes, catalogued with serial reference and chain-of-custody status."
      />

      {error && <ErrorState onRetry={refetch} message="Evidence vault could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          {isLoading || !data ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-40 w-full" />
              ))}
            </div>
          ) : data.length === 0 ? (
            <EmptyState icon={Archive} title="No evidence logged" message="Evidence items will appear here once catalogued." />
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 content-start">
              {data.map((item) => (
                <EvidenceCard
                  key={item.itemId}
                  {...item}
                  isSelected={selected?.itemId === item.itemId}
                  onClick={() => setSelectedId(item.itemId)}
                />
              ))}
            </div>
          )}

          <div className="panel p-4 h-fit sticky top-4">
            <h3 className="font-display text-lg mb-3">Evidence Of Crime Scene</h3>
            {!selected ? (
              <p className="text-ink-muted text-sm">Select an evidence item to preview details.</p>
            ) : (
              <div className="flex flex-col gap-3">
                <div className="w-full h-40 rounded-sm bg-surface-2 flex items-center justify-center">
                  <Archive size={28} className="text-ink-muted" strokeWidth={1.25} />
                </div>
                <div>
                  <p className="label-eyebrow">{selected.itemId}</p>
                  <p className="font-display text-lg">{selected.name}</p>
                </div>
                <dl className="text-sm flex flex-col gap-1.5">
                  <div className="flex justify-between">
                    <dt className="text-ink-muted">Serial number</dt>
                    <dd className="text-ink-secondary">{selected.serialNo}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-ink-muted">Linked case</dt>
                    <dd className="text-ink-secondary">{selected.caseId}</dd>
                  </div>
                </dl>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
