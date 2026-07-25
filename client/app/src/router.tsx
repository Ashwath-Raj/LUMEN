/**
 * Application router — the exact information architecture of arch §C.
 *
 * Public surfaces (PublicLayout): `/` landing, `/login`. Authenticated surfaces
 * (AppShell behind RequireAuth): `/briefing` and the rail order Command → Geo →
 * Cases → Ask → Forecasts → Quality, plus the drill-in routes `/case/:id` and
 * `/person/:id` (never in the rail, §C), `/network`, `/anomalies`, and the
 * bottom `/system` · `/admin` group. Every page is a lazy-loaded TODO
 * placeholder in Session 0; feature sessions replace them one at a time.
 *
 * Routes are code-split (arch §G: "route-level code splitting … so /command
 * doesn't pay for Cytoscape"). Each element is wrapped in a PanelErrorBoundary
 * so a page crash never white-screens the shell (arch §G).
 */
import { Suspense, lazy, type ComponentType } from "react";
import { Route, Routes } from "react-router-dom";

import { PublicLayout } from "@/layouts/PublicLayout";
import { AppShell } from "@/layouts/AppShell";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { RequireRole } from "@/components/auth/RequireRole";
import { PanelErrorBoundary } from "@/components/PanelErrorBoundary";
import { EmptyState } from "@/design/primitives";

const LandingPage = lazy(() => import("@/features/landing/LandingPage"));
const LoginPage = lazy(() => import("@/features/login/LoginPage"));
const BriefingPage = lazy(() => import("@/features/briefing/BriefingPage"));
const CommandPage = lazy(() => import("@/features/command/CommandPage"));
const GeoPage = lazy(() => import("@/features/geo/GeoPage"));
const CaseRegistryPage = lazy(() => import("@/features/cases/CaseRegistryPage"));
const CaseWorkspacePage = lazy(() => import("@/features/case/CaseWorkspacePage"));
const PersonDossierPage = lazy(() => import("@/features/person/PersonDossierPage"));
const NetworkPage = lazy(() => import("@/features/network/NetworkPage"));
const IntelligenceConsolePage = lazy(() => import("@/features/ask/IntelligenceConsolePage"));
const ForecastsPage = lazy(() => import("@/features/forecasts/ForecastsPage"));
const AnomalyRegisterPage = lazy(() => import("@/features/anomalies/AnomalyRegisterPage"));
const DataQualityPage = lazy(() => import("@/features/quality/DataQualityPage"));
const SystemPage = lazy(() => import("@/features/system/SystemPage"));
const AdminPage = lazy(() => import("@/features/admin/AdminPage"));
const NotFoundPage = lazy(() => import("@/features/NotFoundPage"));

/** Wrap a lazy page in its panel error boundary + suspense fallback. */
function page(Component: ComponentType) {
  return (
    <PanelErrorBoundary>
      <Suspense fallback={<EmptyState message="Loading…" />}>
        <Component />
      </Suspense>
    </PanelErrorBoundary>
  );
}

export function AppRouter() {
  return (
    <Routes>
      {/* Public (pre-auth) surfaces — arch §C.1 / §C.2 */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={page(LandingPage)} />
        <Route path="/login" element={page(LoginPage)} />
      </Route>

      {/* Authenticated shell — arch §C / §D */}
      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/briefing" element={page(BriefingPage)} />
        <Route path="/command" element={page(CommandPage)} />
        <Route path="/geo" element={page(GeoPage)} />
        <Route path="/cases" element={page(CaseRegistryPage)} />
        <Route path="/case/:id" element={page(CaseWorkspacePage)} />
        <Route path="/person/:id" element={page(PersonDossierPage)} />
        <Route path="/network" element={page(NetworkPage)} />
        <Route path="/ask" element={page(IntelligenceConsolePage)} />
        <Route path="/forecasts" element={page(ForecastsPage)} />
        <Route path="/anomalies" element={page(AnomalyRegisterPage)} />
        <Route path="/quality" element={page(DataQualityPage)} />
        <Route path="/system" element={page(SystemPage)} />
        <Route
          path="/admin"
          element={
            <RequireRole allow={["auditor", "state_analyst"]}>
              {page(AdminPage)}
            </RequireRole>
          }
        />
      </Route>

      <Route path="*" element={page(NotFoundPage)} />
    </Routes>
  );
}
