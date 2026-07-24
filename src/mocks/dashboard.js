export const mockCommandCenterSummary = {
  totalCrimes: { value: 1492, trend: '+6.2%', trendTone: 'warning' },
  activeCases: { value: 384, trend: '-1.3%', trendTone: 'success' },
  highRiskAreas: { value: 12, trend: '▲ 2 new', trendTone: 'critical' },
  openFirs: { value: 89, trend: '-4 today', trendTone: 'success' },
};

export const mockCrimeTrend = [
  { label: 'Mon', value: 62 },
  { label: 'Tue', value: 74 },
  { label: 'Wed', value: 58 },
  { label: 'Thu', value: 91 },
  { label: 'Fri', value: 105 },
  { label: 'Sat', value: 88 },
  { label: 'Sun', value: 70 },
];

export const mockRecentAlerts = [
  {
    id: 'ALRT-4471',
    timestamp: '09:44:12',
    message: 'Weapon Detected — South Division',
    detail: 'Camera 3-012 flagged an unregistered object.',
    tone: 'critical',
  },
  {
    id: 'ALRT-4470',
    timestamp: '09:15:03',
    message: 'Pattern Match — Case 892',
    detail: 'Vehicle plate partial match against watchlist entry.',
    tone: 'warning',
  },
  {
    id: 'ALRT-4468',
    timestamp: '08:52:41',
    message: 'FIR Logged — Assault',
    detail: 'Standard protocol initiated by Hoysala Patrol 7.',
    tone: 'neutral',
  },
  {
    id: 'ALRT-4465',
    timestamp: '08:30:00',
    message: 'Geofence Sync Complete',
    detail: 'Federal records synced successfully.',
    tone: 'success',
  },
];

export const mockCommandActions = [
  { id: 'action-initiate', label: 'Initiate Investigation', to: '/investigation' },
  { id: 'action-deploy', label: 'Deploy Resources', to: '/operations' },
  { id: 'action-briefing', label: 'Generate Briefing', to: '/analytics' },
];

export const mockHeatmapHotspots = [
  { id: 'HPT-A1', label: 'Peenya Industrial Area', x: 62, y: 38, intensity: 'critical' },
  { id: 'HPT-B4', label: 'Mangaluru Port', x: 28, y: 64, intensity: 'high' },
  { id: 'HPT-C2', label: 'Majestic Bus Station', x: 74, y: 22, intensity: 'moderate' },
];
