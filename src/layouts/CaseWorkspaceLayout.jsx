import { Outlet } from 'react-router-dom';
import CaseWorkspaceSidebar from '@/components/investigation/CaseWorkspaceSidebar.jsx';

/**
 * Nested inside ModuleLayout (investigation). Renders when an operator
 * opens a specific case: /investigation/cases/:caseId/*. Swaps the general
 * Investigation sidebar for the case-scoped one (Suspects/Evidence/
 * Timeline/Network/Reports), matching the Figma's "Reconstruction Board".
 */
export default function CaseWorkspaceLayout() {
  return (
    <div className="flex h-full min-h-0">
      <CaseWorkspaceSidebar />
      <main className="flex-1 min-w-0 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
