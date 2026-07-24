export const mockCases = [
  { id: 'case-77', label: 'Case 77', status: 'ACTIVE', updatedAt: '2 hours ago', evidenceCount: 14 },
  { id: 'case-2024-0892', label: 'CASE-2024-0892', status: 'ACTIVE', updatedAt: '1 day ago', evidenceCount: 22 },
  { id: 'case-892', label: 'Case 892', status: 'ACTIVE', updatedAt: '5 hours ago', evidenceCount: 9 },
  { id: 'case-451', label: 'Case 451', status: 'UNSOLVED', updatedAt: '3 days ago', evidenceCount: 6 },
  { id: 'case-330', label: 'Case 330', status: 'CLOSED', updatedAt: '2 weeks ago', evidenceCount: 31 },
];

const primarySuspect = {
  id: 'ID-77A9-PER',
  name: 'Shetty, Rahul',
  role: 'Primary Suspect',
  tags: [
    { label: 'FLIGHT RISK', tone: 'warning' },
    { label: 'ARMED', tone: 'critical' },
  ],
  lastKnownLocation: 'Pier 39 Wharf',
  riskLevel: 'CRITICAL',
  caseStatus: 'ACTIVE',
  associatedEntities: 4,
};

export const mockCaseDetails = {
  'case-77': {
    id: 'case-77',
    label: 'Case 77',
    status: 'ACTIVE',
    inspector: 'Shetty, Rahul',
    suspects: [primarySuspect],
    evidence: [
      { itemId: 'EVD-CV-8701', name: 'Service Weapon — 9mm', serialNo: '3333333337555', caseId: 'case-77' },
      { itemId: 'EVD-CV-8702', name: 'Burned Ledger Fragment', serialNo: '99231-A-2', caseId: 'case-77' },
      { itemId: 'EVD-CV-8703', name: 'Encrypted USB Drive', serialNo: 'SAND256-C78', caseId: 'case-77' },
      { itemId: 'EVD-CV-8704', name: 'Leather Wallet (Found)', serialNo: 'WL-9089', caseId: 'case-77' },
    ],
    timeline: [
      {
        id: 'tl-1',
        timestamp: '03:45 AM · Oct 12',
        title: 'Signal Lost',
        description: "Subject's burner device went offline in Sector 4 grid. Last ping traced to abandoned industrial zone.",
      },
      {
        id: 'tl-2',
        timestamp: '11:20 PM · Oct 11',
        title: 'Vehicle Sighted',
        description: 'ANPR camera flagged a matching vehicle departing Pier 39 Wharf heading north.',
      },
      {
        id: 'tl-3',
        timestamp: '08:05 PM · Oct 11',
        title: 'Witness Statement Logged',
        description: 'Dockworker reported a physical altercation matching the suspect description.',
      },
    ],
    network: {
      nodes: [
        { id: 'vance', label: 'Shetty, Rahul', kind: 'flag' },
        { id: 'silver-syndicate', label: 'Silver Syndicate', kind: 'cluster' },
        { id: 'chen', label: 'Anjali, N.', kind: 'category' },
        { id: 'burner-device', label: 'Burner Device', kind: 'default' },
        { id: 'warehouse-7', label: 'Warehouse 7', kind: 'default' },
      ],
      edges: [
        { source: 'vance', target: 'silver-syndicate' },
        { source: 'vance', target: 'burner-device' },
        { source: 'silver-syndicate', target: 'chen' },
        { source: 'silver-syndicate', target: 'warehouse-7' },
      ],
    },
    reports: [
      { id: 'RPT-1', title: 'Initial Incident Report', author: 'PC R. Ramesh', date: '2026-07-08' },
      { id: 'RPT-2', title: 'Forensic Ballistics Summary', author: 'Lab Unit 3', date: '2026-07-10' },
      { id: 'RPT-3', title: 'Surveillance Correlation Brief', author: 'OP_042', date: '2026-07-11' },
    ],
  },
  'case-2024-0892': {
    id: 'case-2024-0892',
    label: 'CASE-2024-0892',
    status: 'ACTIVE',
    inspector: 'Shetty, Rahul',
    suspects: [primarySuspect],
    evidence: [
      { itemId: 'EVD-0892-01', name: 'CCTV Backup Tape', serialNo: 'TAPE-2-03', caseId: 'case-2024-0892' },
      { itemId: 'EVD-0892-02', name: 'Latent Print Lift', serialNo: 'LP-4471', caseId: 'case-2024-0892' },
    ],
    timeline: [
      {
        id: 'tl-1',
        timestamp: '03:45 AM · Oct 12',
        title: 'Signal Lost',
        description: "Subject's burner device went offline in Sector 4 grid.",
      },
    ],
    network: {
      nodes: [
        { id: 'vance', label: 'Shetty, Rahul', kind: 'flag' },
        { id: 'silver-syndicate', label: 'Silver Syndicate', kind: 'cluster' },
      ],
      edges: [{ source: 'vance', target: 'silver-syndicate' }],
    },
    reports: [{ id: 'RPT-1', title: 'Reconstruction Board Summary', author: 'OP_042', date: '2026-07-09' }],
  },
};

export const mockSuspectProfiles = [
  {
    ...primarySuspect,
    name: 'Shetty, Rahul',
    photoUrl: null,
    linkedCase: 'Case 77',
    dob: '1985-04-11',
    lastSighting: 'Pier 39 Wharf',
  },
  {
    id: 'ID-4402-PER',
    name: 'Anjali, N.',
    role: 'Person of Interest',
    tags: [{ label: 'UNDER SURVEILLANCE', tone: 'info' }],
    linkedCase: 'Case 892',
    dob: '1990-09-02',
    lastSighting: 'Majestic Bus Station',
  },
];

export const mockWatchlist = [
  {
    id: 'WL-2201',
    name: 'Unidentified Suspect (Female)',
    reason: 'Persistent presence near Warehouse 7 during three separate incidents.',
    riskLevel: 'ELEVATED',
    lastSeen: '2026-07-09',
  },
  {
    id: 'WL-2198',
    name: 'M. Reyes',
    reason: 'Prior conviction, financial ties to flagged entity Silver Syndicate.',
    riskLevel: 'MODERATE',
    lastSeen: '2026-07-05',
  },
];

export const mockEvidenceLocker = [
  { itemId: 'EVD-CV-8701', name: 'Service Weapon — 9mm', serialNo: '3333333337555', caseId: 'case-77' },
  { itemId: 'EVD-CV-8702', name: 'Burned Ledger Fragment', serialNo: '99231-A-2', caseId: 'case-77' },
  { itemId: 'EVD-CV-8703', name: 'Encrypted USB Drive', serialNo: 'SAND256-C78', caseId: 'case-2024-0892' },
  { itemId: 'EVD-CV-8704', name: 'Leather Wallet (Found)', serialNo: 'WL-9089', caseId: 'case-892' },
  { itemId: 'EVD-CV-8705', name: 'CCTV Backup Tape', serialNo: 'TAPE-2-03', caseId: 'case-2024-0892' },
];

export const mockFirIntelligence = {
  document: {
    caseId: 'Under Section 154 CR.P.C.',
    district: 'District North Sector',
    year: '2024',
    firNo: '8896',
  },
  extractedEntities: [
    { id: 'ent-1', label: 'Shetty, Rahul', type: 'Person', confidence: 96 },
    { id: 'ent-2', label: 'Abandoned Mall Yard', type: 'Location', confidence: 88 },
    { id: 'ent-3', label: '9mm shell casing', type: 'Object', confidence: 74 },
    { id: 'ent-4', label: 'Sedan, dark colored', type: 'Vehicle', confidence: 61 },
  ],
  linkedNetwork: {
    nodes: [
      { id: 'fir', label: 'FIR-8896', kind: 'flag' },
      { id: 'vance', label: 'Shetty, Rahul', kind: 'cluster' },
      { id: 'sedan', label: 'Dark Sedan', kind: 'default' },
    ],
    edges: [
      { source: 'fir', target: 'vance' },
      { source: 'vance', target: 'sedan' },
    ],
  },
};

export const mockInterviewTranscripts = {
  'subject-4a': {
    id: 'subject-4a',
    title: 'Transcript of Interview: Subject 4A',
    caseId: 'CRC-2023-0938A',
    status: 'ACTIVE ANALYSIS',
    lines: [
      { id: 'l1', speaker: 'INTERVIEWER', timestamp: '14:00:00', text: 'State your name for the record.' },
      {
        id: 'l2',
        speaker: 'Rahul Shetty',
        timestamp: '14:00:12',
        text: "I already told you I wasn't there. That night.",
        highlight: true,
      },
      {
        id: 'l3',
        speaker: 'Rahul Shetty',
        timestamp: '14:03:41',
        text: 'We have manifests showing the "Mariana" departed Pier 4 at 0200 hours.',
      },
      {
        id: 'l4',
        speaker: 'INTERVIEWER',
        timestamp: '14:05:20',
        text: 'Who is Silver Syndicate to you?',
      },
      {
        id: 'l5',
        speaker: 'Rahul Shetty',
        timestamp: '14:06:03',
        text: "The guys from the 'Mariana' cargo. Look, I don't know their names. They communicate through burner phones. I got a text with coordinates, that's it.",
      },
    ],
    extractedEntities: [
      { id: 'ent-1', label: 'Silver Syndicate', type: 'Organization', confidence: 92 },
      { id: 'ent-2', label: '"Mariana" (vessel)', type: 'Asset', confidence: 79 },
      { id: 'ent-3', label: 'Pier 4', type: 'Location', confidence: 85 },
    ],
  },
};

export const mockDeviceForensics = {
  'burn-77291-b': {
    id: 'burn-77291-b',
    label: 'BURN-77291-B',
    decryptionProgress: 68,
    signal: 'OFFLINE',
    gpsData: '90.9% recovered',
    technicalSummary:
      'The device appears to be a relay node for the "Lighthouse" network. Reconstruction of deleted messages is underway using Bureau protocol 7.',
    dataPackets: [
      { id: 'pkt-1', label: 'SMS bundle — 44 messages', status: 'decrypted' },
      { id: 'pkt-2', label: 'Call log — 12 entries', status: 'decrypted' },
      { id: 'pkt-3', label: 'GPS trace history', status: 'in progress' },
      { id: 'pkt-4', label: 'Encrypted media cache', status: 'pending' },
    ],
  },
};

export const mockInvestigationReports = {
  'case-77': [
    { id: 'RPT-1', title: 'Initial Incident Report', author: 'PC R. Ramesh', date: '2026-07-08' },
    { id: 'RPT-2', title: 'Forensic Ballistics Summary', author: 'Lab Unit 3', date: '2026-07-10' },
    { id: 'RPT-3', title: 'Surveillance Correlation Brief', author: 'OP_042', date: '2026-07-11' },
  ],
};
