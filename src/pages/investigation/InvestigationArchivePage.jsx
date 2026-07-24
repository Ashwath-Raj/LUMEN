import { Inbox } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchInvestigationArchive } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import DataTable from '@/components/common/DataTable.jsx';
import Badge from '@/components/common/Badge.jsx';

export default function InvestigationArchivePage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchInvestigationArchive, []);
  const navigate = useNavigate();

  const columns = [
    { key: 'id', header: 'Case ID' },
    { key: 'label', header: 'Case' },
    { key: 'status', header: 'Status', render: (row) => <Badge tone="neutral">{row.status}</Badge> },
    { key: 'updatedAt', header: 'Closed' },
    { key: 'evidenceCount', header: 'Evidence Items' },
  ];

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow="Investigation" title="Archive" description="Closed cases retained for record and audit." />

      {error && <ErrorState onRetry={refetch} message="Archive could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="panel p-4">
            <Skeleton rows={4} className="h-8 w-full" />
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={Inbox} title="No archived cases" />
        ) : (
          <div className="panel p-4">
            <DataTable
              columns={columns}
              rows={data}
              getRowKey={(row) => row.id}
              onRowClick={(row) => navigate(`/investigation/cases/${row.id}`)}
            />
          </div>
        ))}
    </div>
  );
}
