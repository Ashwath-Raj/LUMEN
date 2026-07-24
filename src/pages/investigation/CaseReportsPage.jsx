import { useParams } from 'react-router-dom';
import { FileText } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchCaseReports } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';

export default function CaseReportsPage() {
  const { caseId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchCaseReports(caseId), [caseId]);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow={`Investigation / ${caseId}`} title="Reports" />

      {error && <ErrorState onRetry={refetch} message="Reports could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <Skeleton rows={3} className="h-14 w-full" />
        ) : data.length === 0 ? (
          <EmptyState icon={FileText} title="No reports filed for this case" />
        ) : (
          <ul className="flex flex-col gap-3">
            {data.map((report) => (
              <li key={report.id} className="panel p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText size={16} className="text-ink-muted" />
                  <div>
                    <p className="text-sm text-ink-primary">{report.title}</p>
                    <p className="text-xs text-ink-muted">{report.author}</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-ink-muted">{report.date}</span>
              </li>
            ))}
          </ul>
        ))}
    </div>
  );
}
