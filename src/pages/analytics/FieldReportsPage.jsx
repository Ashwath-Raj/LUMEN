import { useState } from 'react';
import { Camera, MapPin, FileText } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchFieldReports } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';

export default function FieldReportsPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchFieldReports, []);
  const [selectedId, setSelectedId] = useState(null);

  const selected = data?.find((r) => r.id === selectedId) ?? data?.[0] ?? null;

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Analytics"
        title="Field Reports"
        description="Officer-submitted field reports with crime scene photos and incident summaries."
      />

      {error && <ErrorState onRetry={refetch} message="Field reports could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-6">
          {isLoading || !data ? (
            <Skeleton rows={4} className="h-16 w-full" />
          ) : data.length === 0 ? (
            <EmptyState icon={FileText} title="No field reports" message="Submitted reports will appear here." />
          ) : (
            <ul className="flex flex-col gap-2">
              {data.map((report) => (
                <li key={report.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(report.id)}
                    className={`w-full text-left panel p-3 transition-colors ${
                      (selected?.id ?? data[0].id) === report.id
                        ? 'border-accent-gold bg-accent-goldSoft'
                        : 'hover:border-border-strong'
                    }`}
                  >
                    <p className="label-eyebrow">{report.id}</p>
                    <p className="text-sm text-ink-primary mt-0.5">{report.title}</p>
                    <p className="text-xs text-ink-muted mt-1">{report.submittedAt}</p>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {!isLoading && selected && (
            <div className="panel p-5 flex flex-col gap-4">
              <div>
                <p className="label-eyebrow">Field Report Details</p>
                <h2 className="font-display text-2xl mt-1">{selected.title}</h2>
              </div>

              <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                <div>
                  <dt className="text-ink-muted flex items-center gap-1.5">
                    <MapPin size={13} /> Location
                  </dt>
                  <dd className="text-ink-secondary mt-0.5">{selected.location}</dd>
                </div>
                <div>
                  <dt className="text-ink-muted">Reporting Officer</dt>
                  <dd className="text-ink-secondary mt-0.5">{selected.officer}</dd>
                </div>
                <div>
                  <dt className="text-ink-muted">Linked Case</dt>
                  <dd className="text-ink-secondary mt-0.5">{selected.caseId}</dd>
                </div>
                <div>
                  <dt className="text-ink-muted">Submitted</dt>
                  <dd className="text-ink-secondary mt-0.5">{selected.submittedAt}</dd>
                </div>
              </dl>

              <div>
                <h3 className="label-eyebrow mb-2 flex items-center gap-1.5">
                  <Camera size={13} /> Crime Scene Reports
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {selected.photos.map((photo) => (
                    <div key={photo.id} className="panel p-2">
                      <div className="h-20 rounded-sm bg-surface-2 flex items-center justify-center">
                        <Camera size={18} className="text-ink-muted" strokeWidth={1.5} />
                      </div>
                      <p className="text-xs text-ink-muted mt-1.5">{photo.caption}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="label-eyebrow mb-2">Summary</h3>
                <p className="text-sm text-ink-secondary leading-relaxed">{selected.summary}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
