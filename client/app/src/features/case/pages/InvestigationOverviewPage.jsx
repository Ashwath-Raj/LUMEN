import { useNavigate } from 'react-router-dom';
import { FolderSearch } from 'lucide-react';
import { useAsyncData } from '@/app/hooks/useAsyncData.js';
import { fetchCases } from '@/api/investigationService.js';
import PageHeader from '@/design/primitives/PageHeader.jsx';
import Skeleton from '@/design/primitives/Skeleton.jsx';
import ErrorState from '@/design/primitives/ErrorState.jsx';
import EmptyState from '@/design/primitives/EmptyState.jsx';
import CaseFolderCard from '@/features/case/components/CaseFolderCard.jsx';

export default function InvestigationOverviewPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchCases, []);
  const navigate = useNavigate();

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Investigation"
        title="Active Cases"
        description="Open case files across all active investigations. Select a case to enter its Reconstruction Board."
      />

      {error && <ErrorState onRetry={refetch} message="Cases could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-28 w-full" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={FolderSearch} title="No active cases" message="Start a new investigation to see it here." />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {data.map((c) => (
              <CaseFolderCard
                key={c.id}
                caseId={c.id}
                label={c.label}
                status={c.status}
                meta={`${c.evidenceCount} items · ${c.updatedAt}`}
                onClick={() => navigate(`/investigation/cases/${c.id}`)}
              />
            ))}
          </div>
        ))}
    </div>
  );
}
