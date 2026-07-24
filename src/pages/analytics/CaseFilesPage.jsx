import { useState } from 'react';
import { FileSearch } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchCaseFiles } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import CaseFolderCard from '@/components/investigation/CaseFolderCard.jsx';

export default function CaseFilesPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchCaseFiles, []);
  const [selectedId, setSelectedId] = useState(null);

  const selected = data?.find((c) => c.id === selectedId) ?? data?.[0] ?? null;

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow="Analytics" title="Case Files" description="Browse case folders across every active and closed investigation." />

      {error && <ErrorState onRetry={refetch} message="Case files could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          {isLoading || !data ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-28 w-full" />
              ))}
            </div>
          ) : data.length === 0 ? (
            <EmptyState icon={FileSearch} title="No case files" message="Cases will appear here once created." />
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 content-start">
              {data.map((file) => (
                <CaseFolderCard
                  key={file.id}
                  caseId={file.id}
                  label={file.label}
                  status={file.status}
                  meta={`${file.evidenceCount} items`}
                  isSelected={selected?.id === file.id}
                  onClick={() => setSelectedId(file.id)}
                />
              ))}
            </div>
          )}

          <div className="panel p-4 h-fit sticky top-4">
            <h3 className="font-display text-lg mb-3">Preview</h3>
            {!selected ? (
              <p className="text-ink-muted text-sm">Select a case folder to preview details.</p>
            ) : (
              <div className="flex flex-col gap-3">
                <div>
                  <p className="label-eyebrow">{selected.id}</p>
                  <p className="font-display text-xl">{selected.label}</p>
                </div>
                <dl className="text-sm flex flex-col gap-1.5">
                  <div className="flex justify-between">
                    <dt className="text-ink-muted">Status</dt>
                    <dd className="text-ink-secondary">{selected.status}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-ink-muted">Last updated</dt>
                    <dd className="text-ink-secondary">{selected.updatedAt}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-ink-muted">Evidence items</dt>
                    <dd className="text-ink-secondary">{selected.evidenceCount}</dd>
                  </div>
                </dl>
                <Link
                  to={`/investigation/cases/${selected.id}`}
                  className="w-full mt-2 text-center px-4 py-2 text-sm font-medium rounded-sm border border-border-strong text-ink-primary hover:bg-surface-2 transition-colors"
                >
                  Open Case Board
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
