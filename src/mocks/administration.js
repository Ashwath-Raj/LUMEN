export const mockSecurityPosture = {
  activeClearances: { value: 1204, footnote: '+12 since last sync' },
  anomalousAccessAttempts: { value: 3, footnote: '2 investigations pending', tone: 'critical' },
  networkIntegrity: { value: '99.9%', footnote: 'All nodes secure' },
  lastSync: { value: '14:02:45 UTC', footnote: 'Automated sync' },
};

export const mockPersonnelRoster = [
  {
    operativeId: 'OPR-004',
    name: 'J. Vance',
    designation: 'Signal Intelligence',
    clearance: 'TS/SCI',
    assignment: 'Active',
    lastAuthenticated: '09:14 PST',
  },
  {
    operativeId: 'OPR-127',
    name: 'S. Chen',
    designation: 'Signal Intelligence Co.',
    clearance: 'SECRET',
    assignment: 'Active',
    lastAuthenticated: '07:18 PST',
  },
  {
    operativeId: 'OPR-089',
    name: 'REDACTED',
    designation: 'Unknown',
    clearance: 'REDACTED',
    assignment: 'Suspended',
    lastAuthenticated: '10hrs ago',
  },
];

export const mockForensicAuditLog = [
  {
    id: 'AUD-4471',
    title: 'Unauthorized Geospatial Access Attempt',
    timestamp: '09:44:12',
    detail: 'Multiple failed authentication attempts originating from an unlisted node. Vector points to Sector 7. Automated lockout initiated.',
    tone: 'critical',
    origin: 'OPR-042',
  },
  {
    id: 'AUD-4468',
    title: 'Routine Access — Case Files',
    timestamp: '08:20:45',
    detail: 'OPR-042 downloaded Case_File_77.pdf.',
    tone: 'neutral',
    origin: 'OPR-042',
  },
  {
    id: 'AUD-4460',
    title: 'Session Timeout',
    timestamp: '07:05:11',
    detail: 'OPR-089 session expired after 30 minutes of inactivity.',
    tone: 'neutral',
    origin: 'OPR-089',
  },
];
