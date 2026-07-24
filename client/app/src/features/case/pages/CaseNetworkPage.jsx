import { useParams } from 'react-router-dom';
import { useAsyncData } from '@/app/hooks/useAsyncData.js';
import { fetchCaseById } from '@/api/investigationService.js';
import PageHeader from '@/design/primitives/PageHeader.jsx';
import Skeleton from '@/design/primitives/Skeleton.jsx';
import ErrorState from '@/design/primitives/ErrorState.jsx';
import NetworkGraph from '@/components/graph/NetworkGraph.jsx';

export default function CaseNetworkPage() {
  const { caseId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchCaseById(caseId), [caseId]);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow={`Investigation / ${caseId}`} title="Network" />

      {error && <ErrorState onRetry={refetch} message="Network could not be loaded." />}

      {!error && (
        <div className="panel p-5">
          {isLoading || !data ? (
            <Skeleton className="h-72 w-full" />
          ) : (
            <NetworkGraph nodes={data.network.nodes} edges={data.network.edges} />
          )}
        </div>
      )}
    </div>
  );
}
