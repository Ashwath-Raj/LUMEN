import { NavLink, useParams } from 'react-router-dom';

/**
 * Once an operator opens a specific case (/investigation/cases/:caseId),
 * the sidebar switches from the general Investigation nav (Active Cases,
 * Suspect Profiles, Evidence Locker...) to this case-scoped nav: Suspects,
 * Evidence, Timeline, Network, Reports — matching the "Reconstruction
 * Board" screens in the Figma. Distinct component because its items are
 * relative to a caseId, not a static config entry.
 */
const CASE_TABS = [
  { key: 'board', label: 'Reconstruction Board', segment: '' },
  { key: 'suspects', label: 'Suspects', segment: 'suspects' },
  { key: 'evidence', label: 'Evidence', segment: 'evidence' },
  { key: 'timeline', label: 'Timeline', segment: 'timeline' },
  { key: 'network', label: 'Network', segment: 'network' },
  { key: 'reports', label: 'Reports', segment: 'reports' },
];

export default function CaseWorkspaceSidebar() {
  const { caseId } = useParams();
  const basePath = `/investigation/cases/${caseId}`;

  return (
    <aside className="w-60 shrink-0 border-r border-border-subtle flex flex-col">
      <div className="px-3 py-4 border-b border-border-subtle">
        <p className="label-eyebrow">Investigation</p>
        <p className="font-display text-lg">{caseId}</p>
      </div>

      <nav className="flex-1 px-2 py-3 flex flex-col gap-1">
        {CASE_TABS.map((tab) => (
          <NavLink
            key={tab.key}
            to={tab.segment ? `${basePath}/${tab.segment}` : basePath}
            end
            className={({ isActive }) =>
              `text-sm px-2 py-1.5 rounded-sm ${
                isActive ? 'bg-accent-goldSoft text-accent-gold' : 'text-ink-secondary'
              }`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
