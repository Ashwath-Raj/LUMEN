/**
 * `AppShell` — the authenticated layout (arch §D shell, §F three-column
 * workspaces sit inside this). Left rail + top bar + routed outlet. Wrapped by
 * `RequireAuth` in the router. Each routed page supplies its own regions; the
 * shell owns only rail + bar + the scroll container.
 *
 * Responsive (§F): desktop-first, supported ≥ 1280. Below 1024 the
 * `WorkstationNotice` covers the viewport instead of a broken small-screen
 * layout. Right-column collapse below 1280 is a per-page concern (the shell does
 * not know a page's columns), handled where each workspace defines them.
 */
import { Outlet } from "react-router-dom";

import { LeftRail } from "@/components/shell/LeftRail";
import { TopBar } from "@/components/shell/TopBar";
import { WorkstationNotice } from "@/components/shell/WorkstationNotice";

export function AppShell() {
  return (
    <>
      <WorkstationNotice />
      <div className="flex h-screen w-screen overflow-hidden bg-void">
        <LeftRail />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main className="min-h-0 flex-1 overflow-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
}
