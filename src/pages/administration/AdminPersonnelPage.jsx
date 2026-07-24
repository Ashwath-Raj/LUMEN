import { Users } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchPersonnelRoster } from '@/services/api/administrationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import DataTable from '@/components/common/DataTable.jsx';
import Badge from '@/components/common/Badge.jsx';

const CLEARANCE_TONE = (clearance) => (clearance === 'REDACTED' ? 'critical' : 'info');
const ASSIGNMENT_TONE = (assignment) => (assignment === 'Active' ? 'success' : 'critical');

const columns = [
  { key: 'operativeId', header: 'Operative ID' },
  { key: 'name', header: 'Name' },
  { key: 'designation', header: 'Designation' },
  {
    key: 'clearance',
    header: 'Clearance',
    render: (row) => <Badge tone={CLEARANCE_TONE(row.clearance)}>{row.clearance}</Badge>,
  },
  {
    key: 'assignment',
    header: 'Assignment',
    render: (row) => <Badge tone={ASSIGNMENT_TONE(row.assignment)}>{row.assignment}</Badge>,
  },
  { key: 'lastAuthenticated', header: 'Last Authenticated' },
];

export default function AdminPersonnelPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchPersonnelRoster, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Administration"
        title="Personnel Roster"
        description="Complete operative directory with clearance level and assignment status."
      />

      {error && <ErrorState onRetry={refetch} message="Personnel roster could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="panel p-4">
            <Skeleton rows={5} className="h-8 w-full" />
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={Users} title="No personnel on file" />
        ) : (
          <div className="panel p-4">
            <DataTable columns={columns} rows={data} getRowKey={(r) => r.operativeId} />
          </div>
        ))}
    </div>
  );
}
