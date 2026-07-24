import { Users } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchPersonnel } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import DataTable from '@/components/common/DataTable.jsx';
import Badge from '@/components/common/Badge.jsx';

const columns = [
  { key: 'id', header: 'Operative ID' },
  { key: 'name', header: 'Name' },
  { key: 'role', header: 'Role' },
  { key: 'unit', header: 'Unit' },
  {
    key: 'status',
    header: 'Status',
    render: (row) => <Badge tone={row.status === 'Active' ? 'success' : 'neutral'}>{row.status}</Badge>,
  },
];

export default function PersonnelPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchPersonnel, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Analytics"
        title="Personnel"
        description="Analysts and field operatives currently assigned to active analytics workstreams."
      />

      {error && <ErrorState onRetry={refetch} message="Personnel roster could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="panel p-4">
            <Skeleton rows={4} className="h-8 w-full" />
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={Users} title="No personnel assigned" />
        ) : (
          <div className="panel p-4">
            <DataTable columns={columns} rows={data} getRowKey={(row) => row.id} />
          </div>
        ))}
    </div>
  );
}
