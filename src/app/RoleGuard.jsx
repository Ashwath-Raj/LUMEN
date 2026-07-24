import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth.js';

/**
 * Gates a subtree to specific operator roles (see ROLES in
 * config/navigation.js). Used for /administration, which the Figma
 * org-chart screens (State HQ -> District/Inspector General) imply is
 * restricted to command-level clearance.
 */
export default function RoleGuard({ allowedRoles = [] }) {
  const { operator } = useAuth();

  const isAllowed = allowedRoles.length === 0 || allowedRoles.includes(operator?.role);

  if (!isAllowed) return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}
