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
 *
 * `main` is a flex column that gives each routed page a DEFINITE height
 * (`flex-1 min-h-0`) and is NOT itself the scroll container — each page owns its
 * own scroll (`overflow-auto` where it needs it). This matters for full-bleed
 * pages like the Geo map: a scroll-container parent whose height is
 * content-driven leaves Leaflet unable to measure its container at init, so its
 * absolutely-positioned panes escape and render beneath the shell. A definite
 * flex height fixes that at the layout root — no CSS hacks in the map itself.
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
          <main className="flex min-h-0 flex-1 flex-col">
            <Outlet />
          </main>
        </div>
      </div>
    </>
  );
}
