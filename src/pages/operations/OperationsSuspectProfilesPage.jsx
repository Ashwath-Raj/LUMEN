import { Link } from 'react-router-dom';
import { UserRoundSearch } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchOperationsSuspects } from '@/services/api/operationsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import SuspectDossierCard from '@/components/investigation/SuspectDossierCard.jsx';

export default function OperationsSuspectProfilesPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchOperationsSuspects, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Operations"
        title="Suspect Profiles"
        description="Field-relevant suspect dossiers surfaced for active deployment planning."
      />

      {error && <ErrorState onRetry={refetch} message="Suspect profiles could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={UserRoundSearch} title="No suspects flagged for operations" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.map((suspect) => (
              <Link key={suspect.id} to="/investigation/suspects" className="block">
                <SuspectDossierCard
                  referenceId={suspect.id}
                  name={suspect.name}
                  role={suspect.role}
                  tags={suspect.tags}
                />
              </Link>
            ))}
          </div>
        ))}
    </div>
  );
}
