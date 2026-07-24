import StatCard from '@/components/common/StatCard.jsx';

/**
 * "Global Security Posture" readout row — active clearances, anomalous
 * access attempts, network integrity, last sync. Built on the shared
 * StatCard rather than a bespoke layout.
 */
export default function SecurityPostureSummary({ posture }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Active Clearances"
        value={posture.activeClearances.value.toLocaleString()}
        trend={posture.activeClearances.footnote}
        trendTone="neutral"
      />
      <StatCard
        label="Anomalous Access Attempts"
        value={posture.anomalousAccessAttempts.value}
        trend={posture.anomalousAccessAttempts.footnote}
        trendTone={posture.anomalousAccessAttempts.tone ?? 'critical'}
      />
      <StatCard
        label="Network Integrity"
        value={posture.networkIntegrity.value}
        trend={posture.networkIntegrity.footnote}
        trendTone="success"
      />
      <StatCard
        label="Last Sync"
        value={posture.lastSync.value}
        trend={posture.lastSync.footnote}
        trendTone="neutral"
      />
    </div>
  );
}
