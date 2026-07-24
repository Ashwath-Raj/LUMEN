import { useParams } from 'react-router-dom';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchInterviewTranscript } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import Badge from '@/components/common/Badge.jsx';

export default function InterviewTranscriptPage() {
  const { interviewId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(
    () => fetchInterviewTranscript(interviewId),
    [interviewId]
  );

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow={`Investigation${data ? ` / ${data.caseId}` : ''}`}
        title={data?.title ?? 'Interview Transcript'}
        actions={data && <Badge tone="warning">{data.status}</Badge>}
      />

      {error && <ErrorState onRetry={refetch} message="Transcript could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          <div className="panel p-5">
            {isLoading || !data ? (
              <Skeleton rows={6} className="h-10 w-full" />
            ) : (
              <ol className="flex flex-col gap-4">
                {data.lines.map((line) => (
                  <li key={line.id} className={line.highlight ? 'border-l-2 border-status-critical pl-3' : ''}>
                    <div className="flex items-baseline gap-2">
                      <span className="label-eyebrow">{line.timestamp}</span>
                      <span className="text-xs font-mono text-ink-muted uppercase">{line.speaker}</span>
                    </div>
                    <p className="text-sm text-ink-primary mt-1">{line.text}</p>
                  </li>
                ))}
              </ol>
            )}
          </div>

          <div className="panel p-4 h-fit">
            <h3 className="font-display text-lg mb-3">Extracted Entities</h3>
            {isLoading || !data ? (
              <Skeleton rows={3} className="h-10 w-full" />
            ) : (
              <ul className="flex flex-col gap-3">
                {data.extractedEntities.map((entity) => (
                  <li key={entity.id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-ink-primary">{entity.label}</p>
                      <p className="text-xs text-ink-muted">{entity.type}</p>
                    </div>
                    <Badge tone={entity.confidence >= 80 ? 'success' : 'warning'}>
                      {entity.confidence}%
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
