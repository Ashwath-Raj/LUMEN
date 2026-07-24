import { ShieldAlert } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchAuditLog } from '@/services/api/administrationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import AuditLogEntry from '@/components/administration/AuditLogEntry.jsx';

export default function AuditLogPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchAuditLog, []);

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Administration"
        title="Forensic Audit Log"
        description="Complete, timestamped record of system and personnel activity. Every action is logged and immutable."
      />

      {error && <ErrorState onRetry={refetch} message="Audit log could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="panel p-4">
            <Skeleton rows={5} className="h-12 w-full" />
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={ShieldAlert} title="No audit entries" message="System activity will be logged here." />
        ) : (
          <div className="panel p-4">
            <ul>
              {data.map((entry) => (
                <AuditLogEntry key={entry.id} {...entry} />
              ))}
            </ul>
          </div>
        ))}
    </div>
  );
}
