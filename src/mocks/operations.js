export const mockIncidentQueue = [
  {
    id: 'INC-8992',
    priority: 'CRITICAL',
    timestamp: '09:42:11 PST',
    title: 'Unauthorized Perimeter Breach',
    zone: 'Peenya Industrial Area, Checkpoint Alpha',
    requiredTeam: 'ASSAULT TM',
    assignment: 'UNASSIGNED',
  },
  {
    id: 'INC-8991',
    priority: 'HIGH',
    timestamp: '09:15:00 PST',
    title: 'Anomalous Signal Detected',
    zone: 'Grid coordinates 47.6062° N, 122.3321° W. Triangulating origin.',
    requiredTeam: 'SURVEILLANCE',
    assignment: 'U1 U4',
  },
  {
    id: 'INC-8988',
    priority: 'ROUTINE',
    timestamp: '08:30:45 PST',
    title: 'Perimeter Patrol Complete',
    zone: 'Northern quadrant secure. No anomalies reported by Unit 7.',
    requiredTeam: null,
    assignment: 'LOGGED',
  },
];

export const mockResourceMetrics = {
  fieldOperatives: { deployed: 84, total: 120, reserves: 36, deployedPct: 70 },
  tacticalVehicles: { active: 12, total: 15, maintenance: 3 },
};

export const mockCoordinationLog = [
  {
    id: 'log-1',
    timestamp: '14:01:22Z',
    message: 'DISPATCH QRF Team 2',
    detail: 'Sector 7 — Grid Alfa',
    tone: 'critical',
  },
  {
    id: 'log-2',
    timestamp: '13:58:05Z',
    message: 'ELEVATE THREAT LEVEL',
    detail: 'Global — pending authorization',
    tone: 'warning',
  },
  {
    id: 'log-3',
    timestamp: '13:45:50Z',
    message: 'TRANSMIT VISUAL DATA',
    detail: 'Transit Corridor D — completed',
    tone: 'success',
  },
  {
    id: 'log-4',
    timestamp: '13:30:00Z',
    message: 'ROUTINE COMMS CHECK',
    detail: 'All channels — verified',
    tone: 'neutral',
  },
];

export const mockTheatreHotspots = [
  { id: 'ZONE-A', label: 'Incident Alfa · Containment', x: 58, y: 42, intensity: 'critical' },
  { id: 'CORR-D', label: 'Transit Corridor D', x: 30, y: 24, intensity: 'moderate' },
];

export const mockOperatorDossier = {
  id: 'OP-7729',
  name: 'R. Sunil Kumar',
  rank: 'Inspector General of Police (IGP)',
  operatorId: 'LMN-OP-7729-X',
  assignedUnit: 'Central Division (Counter-Intel)',
  dateOfEntry: '2018-11-04',
  biometricHash: '8F92...A1B4',
  clearance: 'TS/SCI',
  status: 'ACTIVE',
  preferences: {
    tacticalModeDark: true,
    dataStreamAlerts: false,
  },
};

export const mockFirUploadLookup = {
  suspectPreviousRecords: [
    { id: 'REC-2291', date: '2022-03-14', charge: 'Possession — Class B', outcome: 'Convicted' },
    { id: 'REC-1187', date: '2019-08-02', charge: 'Trespassing', outcome: 'Dismissed' },
  ],
};

export const mockOperationsSuspects = [
  {
    id: 'ID-77A9-PER',
    name: 'Shetty, Rahul',
    role: 'Primary Suspect',
    tags: [
      { label: 'FLIGHT RISK', tone: 'warning' },
      { label: 'ARMED', tone: 'critical' },
    ],
    linkedCase: 'Case 77',
  },
];
