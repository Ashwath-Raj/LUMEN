export const mockCrimeStatistics = {
  overview: [
    { id: 'total-incidents', label: 'Total Incidents (30d)', value: '2,148', trend: '+3.4%', trendTone: 'warning' },
    { id: 'clearance-rate', label: 'Clearance Rate', value: '61%', trend: '+2.1%', trendTone: 'success' },
    { id: 'repeat-offenders', label: 'Repeat Offenders Flagged', value: '76', trend: '+9', trendTone: 'critical' },
    { id: 'avg-response', label: 'Avg. Response Time', value: '11m', trend: '-1.2m', trendTone: 'success' },
  ],
  behavioralNodes: [
    { id: 'n1', label: 'Nocturnal Pattern', kind: 'cluster' },
    { id: 'n2', label: 'Repeat Location', kind: 'cluster' },
    { id: 'n3', label: 'Vehicle Theft', kind: 'category' },
    { id: 'n4', label: 'Narcotics', kind: 'category' },
    { id: 'n5', label: 'Weapon Involvement', kind: 'flag' },
  ],
  behavioralEdges: [
    { source: 'n1', target: 'n3' },
    { source: 'n1', target: 'n4' },
    { source: 'n2', target: 'n3' },
    { source: 'n4', target: 'n5' },
  ],
  riskIndex: [
    { id: 'sector-7g', label: 'Peenya Industrial Area', score: 92 },
    { id: 'lower-docks', label: 'Mangaluru Port', score: 78 },
    { id: 'transit-north', label: 'Majestic Bus Station', score: 64 },
    { id: 'northside', label: 'Malleshwaram Residential', score: 41 },
    { id: 'old-town', label: 'KR Market', score: 33 },
    { id: 'east-canal', label: 'Indiranagar', score: 22 },
  ],
  categoryBreakdown: [
    { id: 'property', label: 'Property Crimes', count: 812, share: 38 },
    { id: 'narcotics', label: 'Narcotics', count: 501, share: 23 },
    { id: 'assault', label: 'Assault', count: 349, share: 16 },
    { id: 'fraud', label: 'Fraud / Cyber', count: 276, share: 13 },
    { id: 'other', label: 'Other', count: 210, share: 10 },
  ],
  recentFeedInjections: [
    {
      id: 'feed-1',
      timestamp: '09:58:02',
      message: 'CCTV Grid 14 — 3,204 frames ingested',
      detail: 'Auto-tagged 6 vehicles of interest.',
      tone: 'success',
    },
    {
      id: 'feed-2',
      timestamp: '09:41:47',
      message: 'FIR Batch Sync — East Division',
      detail: '18 new First Information Reports normalized.',
      tone: 'neutral',
    },
    {
      id: 'feed-3',
      timestamp: '09:12:15',
      message: 'Anomaly Flagged — Financial Vectors',
      detail: 'Unusual transaction clustering near Warehouse 7.',
      tone: 'warning',
    },
  ],
};

export const mockCaseFiles = [
  { id: 'case-77', label: 'Case 77', status: 'ACTIVE', updatedAt: '2 hours ago', evidenceCount: 14 },
  { id: 'case-892', label: 'Case 892', status: 'ACTIVE', updatedAt: '5 hours ago', evidenceCount: 9 },
  { id: 'case-0892', label: 'Case-2024-0892', status: 'ACTIVE', updatedAt: '1 day ago', evidenceCount: 22 },
  { id: 'case-451', label: 'Case 451', status: 'UNSOLVED', updatedAt: '3 days ago', evidenceCount: 6 },
  { id: 'case-330', label: 'Case 330', status: 'CLOSED', updatedAt: '2 weeks ago', evidenceCount: 31 },
  { id: 'case-119', label: 'Case 119', status: 'CLOSED', updatedAt: '1 month ago', evidenceCount: 18 },
];

export const mockEvidenceVaultItems = [
  { itemId: 'EVD-CV-8701', name: 'Service Weapon — 9mm', serialNo: '3333333337555', caseId: 'case-77' },
  { itemId: 'EVD-CV-8702', name: 'Burned Ledger Fragment', serialNo: '99231-A-2', caseId: 'case-77' },
  { itemId: 'EVD-CV-8703', name: 'Encrypted USB Drive', serialNo: 'SAND256-C78', caseId: 'case-892' },
  { itemId: 'EVD-CV-8704', name: 'Leather Wallet (Found)', serialNo: 'WL-9089', caseId: 'case-892' },
  { itemId: 'EVD-CV-8705', name: 'CCTV Backup Tape', serialNo: 'TAPE-2-03', caseId: 'case-0892' },
  { itemId: 'EVD-CV-8706', name: 'Latent Print Lift', serialNo: 'LP-4471', caseId: 'case-0892' },
];

export const mockFieldReports = [
  {
    id: 'FR-3391',
    title: 'Field Report — Peenya Industrial Area Perimeter Breach',
    caseId: 'case-77',
    officer: 'PC R. Ramesh',
    submittedAt: '2026-07-10 21:45',
    location: 'Peenya Industrial Area, Checkpoint Alpha',
    summary:
      'Responding unit confirmed forced entry at the auxiliary gate. Perimeter secured within 8 minutes; no injuries reported. Evidence markers placed at three points of interest pending forensic sweep.',
    photos: [
      { id: 'ph-1', caption: 'Breached gate lock mechanism' },
      { id: 'ph-2', caption: 'Tire impressions, north access road' },
    ],
  },
  {
    id: 'FR-3388',
    title: 'Field Report — Mangaluru Port Disturbance',
    caseId: 'case-892',
    officer: 'PSI M. Anjali',
    submittedAt: '2026-07-09 14:12',
    location: 'Mangaluru Port, Warehouse 7',
    summary:
      'Anonymous tip led to inspection of Warehouse 7. No occupants present at time of arrival. Financial ledgers and a burned document fragment recovered and logged into evidence.',
    photos: [{ id: 'ph-3', caption: 'Warehouse interior, loading bay' }],
  },
];

export const mockSignalIntercepts = [
  {
    id: 'SIG-2291',
    source: 'Cell Tower — Sector 4 Grid',
    frequency: '850 MHz',
    timestamp: '2026-07-11 09:30:00',
    linkedCase: 'Case-2024-0892',
    confidence: 87,
    tone: 'critical',
    summary: 'Burner device signal triangulated near industrial zone before going dark.',
  },
  {
    id: 'SIG-2288',
    source: 'VoIP Relay — Node 12',
    frequency: 'N/A',
    timestamp: '2026-07-10 22:04:11',
    linkedCase: 'Case 892',
    confidence: 64,
    tone: 'warning',
    summary: 'Encrypted call routed through three relay nodes; endpoint unresolved.',
  },
  {
    id: 'SIG-2280',
    source: 'Maritime Band Scanner',
    frequency: '156.8 MHz',
    timestamp: '2026-07-09 03:12:47',
    linkedCase: 'Case 77',
    confidence: 41,
    tone: 'neutral',
    summary: 'Routine chatter, low correlation with active investigations.',
  },
];

export const mockAnalyticsPersonnel = [
  { id: 'OP-7729', name: 'R. Sunil Kumar', role: 'Inspector General of Police (IGP)', unit: 'Central Division', status: 'Active' },
  { id: 'OP-3312', name: 'N. Anjali', role: 'Deputy Superintendent of Police (DySP)', unit: 'Comms Division', status: 'Active' },
  { id: 'OP-5567', name: 'M. Hutherford', role: 'Police Sub-Inspector (PSI)', unit: 'East Division', status: 'Active' },
  { id: 'OP-1189', name: 'A. Reyes', role: 'Assistant Sub-Inspector (ASI)', unit: 'Central Division', status: 'On Leave' },
];

export const mockArchivedCases = [
  { id: 'case-330', label: 'Case 330', closedAt: '2026-06-28', outcome: 'Convicted', evidenceCount: 31 },
  { id: 'case-119', label: 'Case 119', closedAt: '2026-06-02', outcome: 'Convicted', evidenceCount: 18 },
  { id: 'case-204', label: 'Case 204', closedAt: '2026-05-14', outcome: 'Dismissed', evidenceCount: 7 },
  { id: 'case-088', label: 'Case 088', closedAt: '2026-04-30', outcome: 'Cold Case', evidenceCount: 12 },
];
