import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import RootLayout from '@/layouts/RootLayout.jsx';
import AuthLayout from '@/layouts/AuthLayout.jsx';
import ModuleLayout from '@/layouts/ModuleLayout.jsx';
import CaseWorkspaceLayout from '@/layouts/CaseWorkspaceLayout.jsx';
import ProtectedRoute from '@/app/ProtectedRoute.jsx';
import RoleGuard from '@/app/RoleGuard.jsx';
import FullScreenLoader from '@/components/common/FullScreenLoader.jsx';
import { ROLES } from '@/config/navigation.js';

// Every page is lazy-loaded so a module's bundle only downloads when an
// operator actually navigates there — relevant here since Investigation
// alone has ~15 screens once fully built out.
const LoginPage = lazy(() => import('@/pages/auth/LoginPage.jsx'));

const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage.jsx'));

const AnalyticsOverviewPage = lazy(() => import('@/pages/analytics/AnalyticsOverviewPage.jsx'));
const CaseFilesPage = lazy(() => import('@/pages/analytics/CaseFilesPage.jsx'));
const EvidenceVaultPage = lazy(() => import('@/pages/analytics/EvidenceVaultPage.jsx'));
const FieldReportsPage = lazy(() => import('@/pages/analytics/FieldReportsPage.jsx'));
const SignalIntelligencePage = lazy(() => import('@/pages/analytics/SignalIntelligencePage.jsx'));
const PersonnelPage = lazy(() => import('@/pages/analytics/PersonnelPage.jsx'));
const ArchivedPage = lazy(() => import('@/pages/analytics/ArchivedPage.jsx'));

const GeospatialPage = lazy(() => import('@/pages/geospatial/GeospatialPage.jsx'));

const InvestigationOverviewPage = lazy(() => import('@/pages/investigation/InvestigationOverviewPage.jsx'));
const SuspectProfilesPage = lazy(() => import('@/pages/investigation/SuspectProfilesPage.jsx'));
const EvidenceLockerPage = lazy(() => import('@/pages/investigation/EvidenceLockerPage.jsx'));
const WatchlistPage = lazy(() => import('@/pages/investigation/WatchlistPage.jsx'));
const FirIntelligencePage = lazy(() => import('@/pages/investigation/FirIntelligencePage.jsx'));
const InvestigationArchivePage = lazy(() => import('@/pages/investigation/InvestigationArchivePage.jsx'));
const InterviewTranscriptPage = lazy(() => import('@/pages/investigation/InterviewTranscriptPage.jsx'));
const DeviceForensicsPage = lazy(() => import('@/pages/investigation/DeviceForensicsPage.jsx'));
const CaseBoardPage = lazy(() => import('@/pages/investigation/CaseBoardPage.jsx'));
const CaseSuspectsPage = lazy(() => import('@/pages/investigation/CaseSuspectsPage.jsx'));
const CaseEvidencePage = lazy(() => import('@/pages/investigation/CaseEvidencePage.jsx'));
const CaseTimelinePage = lazy(() => import('@/pages/investigation/CaseTimelinePage.jsx'));
const CaseNetworkPage = lazy(() => import('@/pages/investigation/CaseNetworkPage.jsx'));
const CaseReportsPage = lazy(() => import('@/pages/investigation/CaseReportsPage.jsx'));

const AIWorkbenchPage = lazy(() => import('@/pages/intelligence/AIWorkbenchPage.jsx'));

const TacticalDeploymentPage = lazy(() => import('@/pages/operations/TacticalDeploymentPage.jsx'));
const FirUploadPage = lazy(() => import('@/pages/operations/FirUploadPage.jsx'));
const OperationsSuspectProfilesPage = lazy(() => import('@/pages/operations/OperationsSuspectProfilesPage.jsx'));
const OperatorDossierPage = lazy(() => import('@/pages/operations/OperatorDossierPage.jsx'));

const GovernanceSecurityPage = lazy(() => import('@/pages/administration/GovernanceSecurityPage.jsx'));
const AdminPersonnelPage = lazy(() => import('@/pages/administration/AdminPersonnelPage.jsx'));
const AuditLogPage = lazy(() => import('@/pages/administration/AuditLogPage.jsx'));

const NotFoundPage = lazy(() => import('@/pages/NotFoundPage.jsx'));

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

            {/* Analytics — has its own sidebar */}
            <Route path="/analytics" element={<ModuleLayout moduleKey="analytics" />}>
              <Route index element={<AnalyticsOverviewPage />} />
              <Route path="case-files" element={<CaseFilesPage />} />
              <Route path="evidence-vault" element={<EvidenceVaultPage />} />
              <Route path="field-reports" element={<FieldReportsPage />} />
              <Route path="signal-intelligence" element={<SignalIntelligencePage />} />
              <Route path="personnel" element={<PersonnelPage />} />
              <Route path="archived" element={<ArchivedPage />} />
            </Route>

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

            {/* Operations — has its own sidebar */}
            <Route path="/operations" element={<ModuleLayout moduleKey="operations" />}>
              <Route index element={<TacticalDeploymentPage />} />
              <Route path="fir-upload" element={<FirUploadPage />} />
              <Route path="suspect-profiles" element={<OperationsSuspectProfilesPage />} />
              <Route path="dossier" element={<OperatorDossierPage />} />
            </Route>

            {/* Administration — has its own sidebar, command/admin roles only */}
            <Route element={<RoleGuard allowedRoles={[ROLES.ADMIN, ROLES.COMMAND]} />}>
              <Route path="/administration" element={<ModuleLayout moduleKey="administration" />}>
                <Route index element={<GovernanceSecurityPage />} />
                <Route path="personnel" element={<AdminPersonnelPage />} />
                <Route path="audit-log" element={<AuditLogPage />} />
              </Route>
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
