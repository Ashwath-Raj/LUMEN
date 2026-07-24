import { Outlet } from 'react-router-dom';
import TopNavBar from '@/app/shell/TopNavBar.jsx';

/**
 * Persists across every authenticated route: LUMEN wordmark, primary module
 * nav, global search, notifications, settings, operator avatar.
 * Module-specific sidebars live one level down, in ModuleLayout.
 */
export default function RootLayout() {
  return (
    <div className="min-h-screen bg-surface-0 text-ink-primary flex flex-col">
      <TopNavBar />
      <div className="flex-1 min-h-0">
        <Outlet />
      </div>
    </div>
  );
}
