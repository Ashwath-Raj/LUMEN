import { useParams } from 'react-router-dom';
import { UserRoundSearch } from 'lucide-react';
import { useAsyncData } from '@/app/hooks/useAsyncData.js';
import { fetchCaseById } from '@/api/investigationService.js';
import PageHeader from '@/design/primitives/PageHeader.jsx';
import Skeleton from '@/design/primitives/Skeleton.jsx';
import ErrorState from '@/design/primitives/ErrorState.jsx';
import EmptyState from '@/design/primitives/EmptyState.jsx';
import SuspectDossierCard from '@/features/case/components/SuspectDossierCard.jsx';

export default function CaseSuspectsPage() {
  const { caseId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchCaseById(caseId), [caseId]);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow={`Investigation / ${caseId}`} title="Suspects" />

      {error && <ErrorState onRetry={refetch} message="Suspects could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <Skeleton rows={2} className="h-32 w-full" />
        ) : data.suspects.length === 0 ? (
          <EmptyState icon={UserRoundSearch} title="No suspects linked to this case" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.suspects.map((s) => (
              <SuspectDossierCard
                key={s.id}
                referenceId={s.id}
                name={s.name}
                role={s.role}
                tags={s.tags}
                photoUrl={s.photoUrl}
              />
            ))}
          </div>
        ))}
    </div>
  );
}
