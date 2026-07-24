import { Outlet } from 'react-router-dom';
import ModuleSidebar from '@/app/shell/ModuleSidebar.jsx';

/**
 * Second-level shell used by modules that have their own left sub-nav
 * (Analytics, Investigation, Operations, Administration). Geospatial and
 * Intelligence render straight inside RootLayout since the Figma shows them
 * as single-screen modules with no sidebar.
 *
 * `moduleKey` selects which entry of sidebarConfig (config/navigation.js)
 * to render, and which OPERATOR mini-profile / module title to show.
 */
export default function ModuleLayout({ moduleKey }) {
  return (
    <div className="flex h-full min-h-0">
      <ModuleSidebar moduleKey={moduleKey} />
      <main className="flex-1 min-w-0 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
