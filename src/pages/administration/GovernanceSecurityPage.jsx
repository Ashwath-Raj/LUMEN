import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchGovernanceOverview } from '@/services/api/administrationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import DataTable from '@/components/common/DataTable.jsx';
import Badge from '@/components/common/Badge.jsx';
import SecurityPostureSummary from '@/components/administration/SecurityPostureSummary.jsx';
import AuditLogEntry from '@/components/administration/AuditLogEntry.jsx';

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

export default function GovernanceSecurityPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchGovernanceOverview, []);

  return (
    <div className="p-8 max-w-[1500px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Administration"
        title="Governance & Security"
        description="Operational clearances, access integrity, and forensic audit trail for all personnel and digital assets."
        actions={<Badge tone="success">DEFCON: NORMAL</Badge>}
      />

      {error && <ErrorState onRetry={refetch} message="Governance data could not be loaded." />}

      {!error && (
        <>
          {isLoading || !data ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : (
            <SecurityPostureSummary posture={data.posture} />
          )}

          <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-6">
            <div className="panel p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-display text-lg">Active Personnel Roster</h3>
                <Link
                  to="/administration/personnel"
                  className="text-xs text-accent-gold flex items-center gap-1 hover:underline"
                >
                  View all <ChevronRight size={13} />
                </Link>
              </div>
              {isLoading || !data ? (
                <Skeleton rows={3} className="h-8 w-full" />
              ) : (
                <DataTable columns={columns} rows={data.personnel.slice(0, 5)} getRowKey={(r) => r.operativeId} />
              )}
            </div>

            <div className="panel p-4">
              <div className="flex items-center justify-between mb-1">
                <h3 className="font-display text-lg">Forensic Audit Log</h3>
                <Link
                  to="/administration/audit-log"
                  className="text-xs text-accent-gold flex items-center gap-1 hover:underline"
                >
                  View all <ChevronRight size={13} />
                </Link>
              </div>
              {isLoading || !data ? (
                <Skeleton rows={3} className="h-12 w-full" />
              ) : (
                <ul>
                  {data.auditLog.slice(0, 4).map((entry) => (
                    <AuditLogEntry key={entry.id} {...entry} />
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
