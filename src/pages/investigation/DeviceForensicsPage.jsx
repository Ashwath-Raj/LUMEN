import { useParams } from 'react-router-dom';
import { Smartphone, Radio, MapPin } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchDeviceForensics } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import Button from '@/components/common/Button.jsx';

const PACKET_TONE = { decrypted: 'success', 'in progress': 'warning', pending: 'neutral' };

export default function DeviceForensicsPage() {
  const { deviceId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(
    () => fetchDeviceForensics(deviceId),
    [deviceId]
  );

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Investigation / Burner Protocol Reconstruction"
        title={data?.label ?? 'Device Forensics'}
      />

      {error && <ErrorState onRetry={refetch} message="Device forensics could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
          <div className="panel p-6 flex flex-col gap-4">
            <div className="w-full h-52 rounded-sm bg-surface-2 flex items-center justify-center">
              <Smartphone size={36} className="text-ink-muted" strokeWidth={1.25} />
            </div>

            {isLoading || !data ? (
              <Skeleton rows={3} className="h-6 w-full" />
            ) : (
              <>
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1.5 text-ink-muted">
                    <Radio size={14} /> Signal: <span className="text-status-critical">{data.signal}</span>
                  </span>
                  <span className="flex items-center gap-1.5 text-ink-muted">
                    <MapPin size={14} /> GPS: {data.gpsData}
                  </span>
                </div>

                <div>
                  <h3 className="label-eyebrow mb-1">Decryption Progress</h3>
                  <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden">
                    <div
                      className="h-full bg-accent-gold"
                      style={{ width: `${data.decryptionProgress}%` }}
                    />
                  </div>
                  <p className="text-xs text-ink-muted mt-1">{data.decryptionProgress}% complete</p>
                </div>

                <div>
                  <h3 className="label-eyebrow mb-1">Technical Summary</h3>
                  <p className="text-sm text-ink-secondary leading-relaxed">{data.technicalSummary}</p>
                </div>

                <div className="flex gap-3 mt-2">
                  <Button variant="ghost">View Data Packets</Button>
                  <Button>Full Reconstruction</Button>
                </div>
              </>
            )}
          </div>

          <div className="panel p-4 h-fit">
            <h3 className="font-display text-lg mb-3">Data Packets</h3>
            {isLoading || !data ? (
              <Skeleton rows={4} className="h-8 w-full" />
            ) : (
              <ul className="flex flex-col divide-y divide-border-subtle">
                {data.dataPackets.map((packet) => (
                  <li key={packet.id} className="flex items-center justify-between py-2 text-sm">
                    <span className="text-ink-secondary">{packet.label}</span>
                    <span
                      className={`text-xs font-mono ${
                        PACKET_TONE[packet.status] === 'success'
                          ? 'text-status-success'
                          : PACKET_TONE[packet.status] === 'warning'
                          ? 'text-status-warning'
                          : 'text-ink-muted'
                      }`}
                    >
                      {packet.status}
                    </span>
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
