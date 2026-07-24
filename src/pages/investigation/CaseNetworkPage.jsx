import { useParams } from 'react-router-dom';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchCaseById } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import NetworkGraph from '@/components/investigation/NetworkGraph.jsx';

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
