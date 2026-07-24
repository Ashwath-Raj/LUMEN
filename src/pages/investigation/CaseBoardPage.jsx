import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { Search } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchCaseById } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import Drawer from '@/components/common/Drawer.jsx';
import Button from '@/components/common/Button.jsx';
import CorkboardCanvas from '@/components/investigation/CorkboardCanvas.jsx';
import SuspectDossierCard from '@/components/investigation/SuspectDossierCard.jsx';

export default function CaseBoardPage() {
  const { caseId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchCaseById(caseId), [caseId]);
  const [focusedSuspectId, setFocusedSuspectId] = useState(null);

  const focusedSuspect =
    data?.suspects.find((s) => s.id === focusedSuspectId) ?? data?.suspects[0] ?? null;

  // Static layout positions for the corkboard demo — a real implementation
  // would persist per-node x/y from drag interactions.
  const nodes = data
    ? [
        { id: data.suspects[0]?.id, x: 30, y: 30, type: 'suspect' },
        { id: 'signal-note', x: 62, y: 68, type: 'note' },
      ]
    : [];
  const connectors = data ? [{ fromId: data.suspects[0]?.id, toId: 'signal-note' }] : [];
  const latestTimelineEvent = data?.timeline[0];

  return (
    <div className="p-8 max-w-[1500px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow={`Investigation / ${caseId}`}
        title="Reconstruction Board"
        description="Visualizing temporal and relational metadata. Map active intelligence nodes to synthesize patterns."
      />

      {error && <ErrorState onRetry={refetch} message="Case data could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <Skeleton className="h-[500px] w-full" />
        ) : (
          <CorkboardCanvas
            nodes={nodes}
            connectors={connectors}
            renderNode={(node) => {
              if (node.type === 'suspect' && focusedSuspect) {
                return (
                  <button type="button" onClick={() => setFocusedSuspectId(focusedSuspect.id)}>
                    <SuspectDossierCard
                      referenceId={focusedSuspect.id}
                      name={focusedSuspect.name}
                      role={focusedSuspect.role}
                      tags={focusedSuspect.tags}
                    />
                  </button>
                );
              }
              if (node.type === 'note' && latestTimelineEvent) {
                return (
                  <div className="panel p-3 w-56 bg-surface-1">
                    <p className="label-eyebrow">{latestTimelineEvent.timestamp}</p>
                    <p className="font-display text-base mt-0.5">{latestTimelineEvent.title}</p>
                    <p className="text-ink-muted text-xs mt-1">{latestTimelineEvent.description}</p>
                  </div>
                );
              }
              return null;
            }}
          />
        ))}

      <Drawer
        isOpen={Boolean(focusedSuspectId)}
        onClose={() => setFocusedSuspectId(null)}
        title="Inspector Details"
      >
        {focusedSuspect && (
          <div className="flex flex-col gap-5">
            <div>
              <p className="label-eyebrow mb-1">Current Focus</p>
              <div className="panel px-3 py-2 flex items-center justify-between">
                <span className="text-sm">{focusedSuspect.name}</span>
                <Search size={14} className="text-accent-gold" />
              </div>
            </div>

            <div>
              <p className="label-eyebrow mb-2">Metadata</p>
              <dl className="flex flex-col gap-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Last Known Loc.</dt>
                  <dd>{focusedSuspect.lastKnownLocation}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Assoc. Entities</dt>
                  <dd>{focusedSuspect.associatedEntities} Verified</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Risk Level</dt>
                  <dd className="text-status-critical">{focusedSuspect.riskLevel}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-muted">Case Status</dt>
                  <dd className="text-status-success">{focusedSuspect.caseStatus}</dd>
                </div>
              </dl>
            </div>

            <div>
              <p className="label-eyebrow mb-2">Quick Actions</p>
              <div className="flex flex-col gap-2">
                <Button variant="ghost">Request Warrant</Button>
                <Button variant="ghost">Log Communication</Button>
                <Button variant="ghost">Update Threat Matrix</Button>
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
