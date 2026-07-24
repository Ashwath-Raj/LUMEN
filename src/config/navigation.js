/**
 * Single source of truth for app navigation.
 *
 * TopNavBar renders `primaryModules`.
 * ModuleSidebar renders the `sidebar` array belonging to the active module.
 * Route guards read `roles` to decide who can see a module at all
 * (e.g. Administration is DG/IG only per the Figma org-chart screens).
 *
 * Keeping this in one config file means adding a new module/screen is a
 * data change here + one route entry, not a hunt through JSX.
 */

export const ROLES = {
  ADMIN: 'admin',
  ANALYST: 'analyst',
  FIELD_OPERATOR: 'field_operator',
  COMMAND: 'command',
};

export const primaryModules = [
  { key: 'dashboard', label: 'Dashboard', path: '/dashboard' },
  { key: 'analytics', label: 'Analytics', path: '/analytics' },
  { key: 'geospatial', label: 'Geospatial', path: '/geospatial' },
  { key: 'investigation', label: 'Investigation', path: '/investigation' },
  { key: 'intelligence', label: 'Intelligence', path: '/intelligence' },
  { key: 'operations', label: 'Operations', path: '/operations' },
  {
    key: 'administration',
    label: 'Administration',
    path: '/administration',
    roles: [ROLES.ADMIN, ROLES.COMMAND],
  },
];

/**
 * Per-module sidebar navigation. Matches the left-rail sub-nav seen per
 * module in the Figma (e.g. Analytics: Case Files / Evidence Vault / Field
 * Reports / Signal Intelligence / Personnel / Archived).
 */
/**
 * Optional primary call-to-action shown above the sidebar nav for a
 * module (e.g. "+ New Investigation" on Investigation/Operations).
 */
export const sidebarPrimaryAction = {
  investigation: { label: 'New Investigation', to: '/investigation' },
  operations: { label: 'New Investigation', to: '/operations' },
};

export const sidebarConfig = {
  analytics: [
    { key: 'overview', label: 'Pattern Analysis', path: '/analytics' },
    { key: 'case-files', label: 'Case Files', path: '/analytics/case-files' },
    { key: 'evidence-vault', label: 'Evidence Vault', path: '/analytics/evidence-vault' },
    { key: 'field-reports', label: 'Field Reports', path: '/analytics/field-reports' },
    { key: 'signal-intelligence', label: 'Signal Intelligence', path: '/analytics/signal-intelligence' },
    { key: 'personnel', label: 'Personnel', path: '/analytics/personnel' },
    { key: 'archived', label: 'Archived', path: '/analytics/archived' },
  ],
  investigation: [
    { key: 'all-cases', label: 'Active Cases', path: '/investigation' },
    { key: 'suspects', label: 'Suspect Profiles', path: '/investigation/suspects' },
    { key: 'evidence-locker', label: 'Evidence Locker', path: '/investigation/evidence' },
    { key: 'watchlist', label: 'Watchlist', path: '/investigation/watchlist' },
    { key: 'fir-intelligence', label: 'FIR Intelligence', path: '/investigation/fir-intelligence' },
    { key: 'archive', label: 'Archive', path: '/investigation/archive' },
  ],
  operations: [
    { key: 'deployment', label: 'Tactical Deployment', path: '/operations' },
    { key: 'fir-upload', label: 'FIR Upload', path: '/operations/fir-upload' },
    { key: 'suspect-profiles', label: 'Suspect Profiles', path: '/operations/suspect-profiles' },
    { key: 'dossier', label: 'Operator Dossier', path: '/operations/dossier' },
  ],
  administration: [
    { key: 'governance', label: 'Governance & Security', path: '/administration' },
    { key: 'personnel', label: 'Personnel Roster', path: '/administration/personnel' },
    { key: 'audit-log', label: 'Forensic Audit Log', path: '/administration/audit-log' },
  ],
  // Geospatial and Intelligence are single-screen modules in the current
  // Figma (no left sub-nav) — omitted intentionally, ModuleSidebar falls
  // back to a slim variant when a module has no entry here.
};
