import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { Archive } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchCaseById } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import EvidenceCard from '@/components/investigation/EvidenceCard.jsx';

export default function CaseEvidencePage() {
  const { caseId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchCaseById(caseId), [caseId]);
  const [selectedId, setSelectedId] = useState(null);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow={`Investigation / ${caseId}`} title="Evidence" />

      {error && <ErrorState onRetry={refetch} message="Evidence could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <Skeleton rows={2} className="h-40 w-full" />
        ) : data.evidence.length === 0 ? (
          <EmptyState icon={Archive} title="No evidence logged for this case" />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {data.evidence.map((item) => (
              <EvidenceCard
                key={item.itemId}
                {...item}
                isSelected={selectedId === item.itemId}
                onClick={() => setSelectedId(item.itemId)}
              />
            ))}
          </div>
        ))}
    </div>
  );
}
