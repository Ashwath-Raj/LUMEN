import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import RootLayout from '@/app/shell/RootLayout.jsx';
import AuthLayout from '@/app/shell/AuthLayout.jsx';
import ModuleLayout from '@/app/shell/ModuleLayout.jsx';
import CaseWorkspaceLayout from '@/app/shell/CaseWorkspaceLayout.jsx';
import ProtectedRoute from '@/app/ProtectedRoute.jsx';
import FullScreenLoader from '@/design/primitives/FullScreenLoader.jsx';

// Every page is lazy-loaded so a module's bundle only downloads when an
// operator actually navigates there — relevant here since Investigation
// alone has ~15 screens once fully built out.
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage.jsx'));

const DashboardPage = lazy(() => import('@/features/command-center/pages/DashboardPage.jsx'));

const GeospatialPage = lazy(() => import('@/features/geo/pages/GeospatialPage.jsx'));

const InvestigationOverviewPage = lazy(() => import('@/features/case/pages/InvestigationOverviewPage.jsx'));
const SuspectProfilesPage = lazy(() => import('@/features/person/pages/SuspectProfilesPage.jsx'));
const EvidenceLockerPage = lazy(() => import('@/features/case/pages/EvidenceLockerPage.jsx'));
const WatchlistPage = lazy(() => import('@/features/case/pages/WatchlistPage.jsx'));
const FirIntelligencePage = lazy(() => import('@/features/case/pages/FirIntelligencePage.jsx'));
const InvestigationArchivePage = lazy(() => import('@/features/case/pages/InvestigationArchivePage.jsx'));
const InterviewTranscriptPage = lazy(() => import('@/features/case/pages/InterviewTranscriptPage.jsx'));
const DeviceForensicsPage = lazy(() => import('@/features/case/pages/DeviceForensicsPage.jsx'));
const CaseBoardPage = lazy(() => import('@/features/case/pages/CaseBoardPage.jsx'));
const CaseSuspectsPage = lazy(() => import('@/features/case/pages/CaseSuspectsPage.jsx'));
const CaseEvidencePage = lazy(() => import('@/features/case/pages/CaseEvidencePage.jsx'));
const CaseTimelinePage = lazy(() => import('@/features/case/pages/CaseTimelinePage.jsx'));
const CaseNetworkPage = lazy(() => import('@/features/case/pages/CaseNetworkPage.jsx'));
const CaseReportsPage = lazy(() => import('@/features/case/pages/CaseReportsPage.jsx'));

const AIWorkbenchPage = lazy(() => import('@/features/intelligence/pages/AIWorkbenchPage.jsx'));

const NotFoundPage = lazy(() => import('@/app/pages/NotFoundPage.jsx'));

export default function AppRouter() {
  return (
    <Suspense fallback={<FullScreenLoader />}>
      <Routes>
        {/* ---- Public / auth ---- */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
        </Route>

        {/* ---- Authenticated app ---- */}
        <Route element={<ProtectedRoute />}>
          <Route element={<RootLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />

            {/* Geospatial — single screen, no sidebar, sits straight in RootLayout */}
            <Route path="/geospatial" element={<GeospatialPage />} />

            {/* Investigation — general sidebar, plus a nested case workspace */}
            <Route path="/investigation" element={<ModuleLayout moduleKey="investigation" />}>
              <Route index element={<InvestigationOverviewPage />} />
              <Route path="suspects" element={<SuspectProfilesPage />} />
              <Route path="evidence" element={<EvidenceLockerPage />} />
              <Route path="watchlist" element={<WatchlistPage />} />
              <Route path="fir-intelligence" element={<FirIntelligencePage />} />
              <Route path="archive" element={<InvestigationArchivePage />} />
              <Route path="interviews/:interviewId" element={<InterviewTranscriptPage />} />
              <Route path="forensics/:deviceId" element={<DeviceForensicsPage />} />

              <Route path="cases/:caseId" element={<CaseWorkspaceLayout />}>
                <Route index element={<CaseBoardPage />} />
                <Route path="suspects" element={<CaseSuspectsPage />} />
                <Route path="evidence" element={<CaseEvidencePage />} />
                <Route path="timeline" element={<CaseTimelinePage />} />
                <Route path="network" element={<CaseNetworkPage />} />
                <Route path="reports" element={<CaseReportsPage />} />
              </Route>
            </Route>

            {/* Intelligence — single screen, no sidebar */}
            <Route path="/intelligence" element={<AIWorkbenchPage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
