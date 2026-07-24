import { Inbox } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchArchived } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import DataTable from '@/components/common/DataTable.jsx';
import Badge from '@/components/common/Badge.jsx';

const OUTCOME_TONE = {
  Convicted: 'success',
  Dismissed: 'neutral',
  'Cold Case': 'warning',
};

const columns = [
  { key: 'id', header: 'Case ID' },
  { key: 'label', header: 'Case' },
  { key: 'closedAt', header: 'Closed' },
  {
    key: 'outcome',
    header: 'Outcome',
    render: (row) => <Badge tone={OUTCOME_TONE[row.outcome] ?? 'neutral'}>{row.outcome}</Badge>,
  },
  { key: 'evidenceCount', header: 'Evidence Items' },
];

export default function ArchivedPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchArchived, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Analytics"
        title="Archived"
        description="Closed, dismissed, and cold cases retained for record and audit purposes."
      />

      {error && <ErrorState onRetry={refetch} message="Archived cases could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="panel p-4">
            <Skeleton rows={4} className="h-8 w-full" />
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={Inbox} title="No archived cases" message="Closed cases will appear here." />
        ) : (
          <div className="panel p-4">
            <DataTable columns={columns} rows={data} getRowKey={(row) => row.id} />
          </div>
        ))}
    </div>
  );
}
