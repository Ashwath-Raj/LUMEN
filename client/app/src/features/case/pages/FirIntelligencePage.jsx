import { useState } from 'react';
import { FileText, UploadCloud } from 'lucide-react';
import { useAsyncData } from '@/app/hooks/useAsyncData.js';
import { fetchFirIntelligence, submitFirDocument } from '@/api/investigationService.js';
import PageHeader from '@/design/primitives/PageHeader.jsx';
import Skeleton from '@/design/primitives/Skeleton.jsx';
import ErrorState from '@/design/primitives/ErrorState.jsx';
import UploadDropzone from '@/design/primitives/UploadDropzone.jsx';
import Badge from '@/design/primitives/Badge.jsx';
import NetworkGraph from '@/components/graph/NetworkGraph.jsx';

export default function FirIntelligencePage() {
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchFirIntelligence(), []);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handleFiles = async (files) => {
    if (!files?.length) return;
    setIsUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append('file', files[0]);
      await submitFirDocument(formData);
      refetch();
    } catch (err) {
      setUploadError(err?.message ?? 'Upload failed. Try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Investigation"
        title="FIR Intelligence"
        description="Upload a First Information Report for automated entity extraction and network correlation."
      />

      {error && <ErrorState onRetry={refetch} message="FIR intelligence could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="panel p-4 flex flex-col gap-4">
            <h3 className="font-display text-lg flex items-center gap-2">
              <FileText size={17} /> Document
            </h3>
            {isLoading || !data ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <div className="bg-surface-2 rounded-sm p-4 text-sm flex flex-col gap-1.5">
                <p className="label-eyebrow">First Information Report</p>
                <p className="text-ink-secondary">{data.document.caseId}</p>
                <p className="text-ink-muted text-xs">District: {data.document.district}</p>
                <p className="text-ink-muted text-xs">
                  FIR No. {data.document.firNo} / {data.document.year}
                </p>
              </div>
            )}
            <UploadDropzone
              onFiles={handleFiles}
              accept=".pdf,.jpg,.png"
              label={isUploading ? 'Processing document...' : 'Drop a FIR document here, or click to upload'}
            />
            {uploadError && <p className="text-status-critical text-sm">{uploadError}</p>}
          </div>

          <div className="panel p-4">
            <h3 className="font-display text-lg mb-3 flex items-center gap-2">
              <UploadCloud size={17} /> Extracted Entities
            </h3>
            {isLoading || !data ? (
              <Skeleton rows={4} className="h-10 w-full" />
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

          <div className="panel p-4">
            <h3 className="font-display text-lg mb-3">Linked Network</h3>
            {isLoading || !data ? (
              <Skeleton className="h-56 w-full" />
            ) : (
              <NetworkGraph nodes={data.linkedNetwork.nodes} edges={data.linkedNetwork.edges} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
