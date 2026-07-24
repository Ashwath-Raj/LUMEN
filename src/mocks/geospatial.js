export const mockHotspots = [
  {
    id: 'HPT-A1',
    label: 'Peenya Industrial Area',
    x: 62,
    y: 38,
    intensity: 'critical',
    probability: 98,
    incidents: 14,
    windowHours: 72,
  },
  {
    id: 'HPT-B4',
    label: 'Mangaluru Port',
    x: 28,
    y: 64,
    intensity: 'high',
    probability: 82,
    incidents: 8,
    windowHours: 72,
  },
  {
    id: 'HPT-C2',
    label: 'Majestic Bus Station',
    x: 74,
    y: 22,
    intensity: 'moderate',
    probability: 65,
    incidents: 4,
    windowHours: 72,
  },
];

export const mockSectorIntel = {
  headline: 'Anomalous density spike detected in Peenya Industrial Area.',
  body: 'Correlates with recent narcotics trafficking routes identified in OP-KAVACHA. Recommend deploying aerial surveillance assets to coordinate with ground units.',
  tags: ['NARCOTICS', 'ELEVATED RISK'],
};

export const mockGeoParameters = {
  activeSession: 'GEO-TRK-882',
  districts: ['Peenya Industrial Area', 'Mangaluru Port', 'KR Market', 'Indiranagar'],
  incidentTypes: ['All Major Felonies', 'Narcotics', 'Property Crime', 'Violent Crime'],
  overlayLayers: [
    { id: 'crime-density', label: 'Crime Density Heatmap', defaultChecked: true },
    { id: 'risk-zones', label: 'Risk Polygon Zones', defaultChecked: true },
    { id: 'cctv', label: 'CCTV Coverage', defaultChecked: false },
    { id: 'patrol-routes', label: 'Patrol Routes', defaultChecked: false },
  ],
};
