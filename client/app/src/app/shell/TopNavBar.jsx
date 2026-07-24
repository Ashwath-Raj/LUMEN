import { NavLink, Link } from 'react-router-dom';
import { ShieldCheck, Settings, LogOut } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { primaryModules } from '@/app/config/navigation.js';
import { useAuth } from '@/app/hooks/useAuth.js';
import SearchInput from '@/design/primitives/SearchInput.jsx';
import NotificationBell from '@/design/primitives/NotificationBell.jsx';

/**
 * Global top nav: LUMEN wordmark, primary module links, search, bell,
 * settings, operator avatar. Filters `primaryModules` by the current
 * operator's role so e.g. Administration only appears for command staff.
 */
export default function TopNavBar() {
  const { operator, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const visibleModules = primaryModules.filter(
    (m) => !m.roles || m.roles.includes(operator?.role)
  );

  const initials = (operator?.name ?? 'OP')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="h-14 shrink-0 border-b border-border-subtle flex items-center gap-6 px-5 bg-surface-0">
      <Link to="/dashboard" className="flex items-center gap-2 shrink-0">
        <ShieldCheck size={18} className="text-accent-gold" strokeWidth={1.75} />
        <span className="font-display text-lg text-accent-gold tracking-wide">LUMEN</span>
      </Link>

      <nav className="flex items-center gap-5 overflow-x-auto">
        {visibleModules.map((m) => (
          <NavLink
            key={m.key}
            to={m.path}
            className={({ isActive }) =>
              `text-sm whitespace-nowrap pb-1 border-b-2 transition-colors ${
                isActive
                  ? 'text-accent-gold border-accent-gold'
                  : 'text-ink-secondary border-transparent hover:text-ink-primary'
              }`
            }
          >
            {m.label}
          </NavLink>
        ))}
      </nav>

      <div className="ml-auto flex items-center gap-4">
        <SearchInput placeholder="Search records..." />
        <NotificationBell count={3} />
        <Link to="/operations/dossier" aria-label="Settings" className="text-ink-secondary hover:text-ink-primary">
          <Settings size={17} strokeWidth={1.75} />
        </Link>

        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="w-8 h-8 rounded-full bg-surface-2 border border-border-subtle flex items-center justify-center text-xs font-mono text-ink-secondary"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
          >
            {initials}
          </button>
          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 mt-2 w-56 bg-surface-1 border border-border-subtle rounded-md shadow-panel py-2 z-50"
            >
              <div className="px-3 pb-2 mb-1 border-b border-border-subtle">
                <p className="text-sm text-ink-primary">{operator?.name ?? 'Operator'}</p>
                <p className="text-xs text-ink-muted">{operator?.rank}</p>
              </div>
              <Link
                to="/operations/dossier"
                role="menuitem"
                className="block px-3 py-1.5 text-sm text-ink-secondary hover:bg-surface-2"
                onClick={() => setMenuOpen(false)}
              >
                Operator Dossier
              </Link>
              <button
                type="button"
                role="menuitem"
                onClick={logout}
                className="w-full text-left flex items-center gap-2 px-3 py-1.5 text-sm text-status-critical hover:bg-surface-2"
              >
                <LogOut size={14} />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
