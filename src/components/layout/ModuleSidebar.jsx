import { NavLink } from 'react-router-dom';
import { sidebarConfig, sidebarPrimaryAction } from '@/config/navigation.js';
import OperatorMiniProfile from '@/components/layout/OperatorMiniProfile.jsx';

/**
 * Renders the sub-nav for whichever module is active, sourced from
 * sidebarConfig[moduleKey]. Also hosts the operator mini-profile card and
 * the module's primary action (e.g. "+ New Investigation"), matching the
 * Figma sidebars.
 */
export default function ModuleSidebar({ moduleKey }) {
  const items = sidebarConfig[moduleKey] ?? [];
  const primaryAction = sidebarPrimaryAction[moduleKey];

  return (
    <aside className="w-60 shrink-0 border-r border-border-subtle flex flex-col bg-surface-0">
      <OperatorMiniProfile primaryAction={primaryAction} />

      <nav className="flex-1 px-2 py-3 flex flex-col gap-1">
        {items.map((item) => (
          <NavLink
            key={item.key}
            to={item.path}
            end={item.path === `/${moduleKey}`}
            className={({ isActive }) =>
              `text-sm px-2.5 py-2 rounded-sm transition-colors ${
                isActive
                  ? 'bg-accent-goldSoft text-accent-gold'
                  : 'text-ink-secondary hover:bg-surface-2 hover:text-ink-primary'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
