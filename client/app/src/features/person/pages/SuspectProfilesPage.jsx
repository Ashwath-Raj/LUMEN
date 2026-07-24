import { UserRoundSearch } from 'lucide-react';
import { useAsyncData } from '@/app/hooks/useAsyncData.js';
import { fetchSuspectProfiles } from '@/api/investigationService.js';
import PageHeader from '@/design/primitives/PageHeader.jsx';
import Skeleton from '@/design/primitives/Skeleton.jsx';
import ErrorState from '@/design/primitives/ErrorState.jsx';
import EmptyState from '@/design/primitives/EmptyState.jsx';
import SuspectDossierCard from '@/features/case/components/SuspectDossierCard.jsx';

export default function SuspectProfilesPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchSuspectProfiles, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Investigation"
        title="Suspect Profiles"
        description="Consolidated dossiers for suspects and persons of interest across every active case."
      />

      {error && <ErrorState onRetry={refetch} message="Suspect profiles could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={UserRoundSearch} title="No suspects on file" />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.map((suspect) => (
              <div key={suspect.id} className="flex flex-col gap-2">
                <SuspectDossierCard
                  referenceId={suspect.id}
                  name={suspect.name}
                  role={suspect.role}
                  tags={suspect.tags}
                  photoUrl={suspect.photoUrl}
                />
                <div className="px-1 text-xs text-ink-muted flex justify-between">
                  <span>Linked: {suspect.linkedCase}</span>
                  <span>Last seen: {suspect.lastSighting}</span>
                </div>
              </div>
            ))}
          </div>
        ))}
    </div>
  );
}
