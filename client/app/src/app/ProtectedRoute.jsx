import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/app/hooks/useAuth.js';
import FullScreenLoader from '@/design/primitives/FullScreenLoader.jsx';

/**
 * Wraps the entire authenticated app tree. Unauthenticated operators are
 * redirected to /login, preserving the intended destination so we can send
 * them back after a successful "Initialize Session".
 */
export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <FullScreenLoader label="Verifying clearance..." />;

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
}
