import { useState } from 'react';
import { BrainCircuit } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchWorkbenchData, submitIntelligenceQuery } from '@/services/api/intelligenceService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import QueryWorkspace from '@/components/intelligence/QueryWorkspace.jsx';
import GeneratedLeadCard from '@/components/intelligence/GeneratedLeadCard.jsx';
import ActionableDirectiveCard from '@/components/intelligence/ActionableDirectiveCard.jsx';

const METRIC_LABEL = {
  neuralPatternMatch: 'Neural Pattern Match',
  geospatialCorrelation: 'Geospatial Correlation',
  temporalAlignment: 'Temporal Alignment',
};

export default function AIWorkbenchPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchWorkbenchData, []);
  const [queryHistory, setQueryHistory] = useState([]);
  const [isSubmittingQuery, setIsSubmittingQuery] = useState(false);

  const handleQuerySubmit = async (query) => {
    setIsSubmittingQuery(true);
    try {
      const result = await submitIntelligenceQuery(query);
      setQueryHistory((prev) => [result, ...prev]);
    } finally {
      setIsSubmittingQuery(false);
    }
  };

  const combinedHistory = [...queryHistory, ...(data?.queryHistory ?? [])];

  return (
    <div className="p-8 max-w-[1500px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Intelligence"
        title="AI Intelligence Workbench"
        description="Synthesizes case data across every module into correlated leads and recommended directives."
      />

      {error && <ErrorState onRetry={refetch} message="Workbench data could not be loaded." />}

      {!error && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
            <QueryWorkspace
              history={combinedHistory}
              onSubmit={handleQuerySubmit}
              isSubmitting={isSubmittingQuery}
            />

            <div className="panel p-4">
              <h3 className="font-display text-lg mb-3 flex items-center gap-2">
                <BrainCircuit size={17} /> Analysis Engine
              </h3>
              {isLoading || !data ? (
                <Skeleton rows={3} className="h-6 w-full" />
              ) : (
                <div className="flex flex-col gap-3">
                  {Object.entries(data.analysisEngine).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-ink-muted">{METRIC_LABEL[key] ?? key}</span>
                        <span className="font-mono text-accent-gold">{value}%</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden">
                        <div className="h-full bg-accent-gold" style={{ width: `${value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="panel p-4">
              <h3 className="font-display text-lg mb-3">Generated Leads</h3>
              {isLoading || !data ? (
                <Skeleton rows={2} className="h-24 w-full" />
              ) : data.generatedLeads.length === 0 ? (
                <EmptyState title="No leads generated yet" message="Submit a query to surface new leads." />
              ) : (
                <div className="flex flex-col gap-3">
                  {data.generatedLeads.map((lead) => (
                    <GeneratedLeadCard key={lead.id} {...lead} />
                  ))}
                </div>
              )}
            </div>

            <div className="panel p-4">
              <h3 className="font-display text-lg mb-3">Temporal Alignment</h3>
              {isLoading || !data ? (
                <Skeleton rows={3} className="h-14 w-full" />
              ) : (
                <ul className="flex flex-col gap-3">
                  {data.temporalAlignment.map((item) => (
                    <li key={item.id}>
                      <p className="text-sm text-ink-primary">{item.title}</p>
                      <p className="text-xs text-ink-muted mt-0.5">{item.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="flex flex-col gap-6">
              <div className="panel p-4">
                <h3 className="font-display text-lg mb-1">Actionable Directives</h3>
                {isLoading || !data ? (
                  <Skeleton rows={3} className="h-8 w-full" />
                ) : (
                  <ul>
                    {data.actionableDirectives.map((dir) => (
                      <ActionableDirectiveCard key={dir.id} label={dir.label} />
                    ))}
                  </ul>
                )}
              </div>

              <div className="panel p-4">
                <h3 className="font-display text-lg mb-3">Evidence Nexus</h3>
                {isLoading || !data ? (
                  <Skeleton rows={2} className="h-6 w-full" />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {data.evidenceNexus.map((item) => (
                      <span
                        key={item.id}
                        className="font-mono text-xs px-2 py-1 rounded-sm bg-surface-2 text-ink-secondary"
                      >
                        {item.label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
