import { useEffect, useMemo, useState } from 'react';
import { redirectToLogin, logoutRequest, fetchCurrentOperator } from '@/api/authService.js';
import { AuthContext } from './AuthContext.js';

/**
 * Provides: { operator, isAuthenticated, isLoading, login, logout }
 * `operator` shape: { id, name, email } — from Catalyst Authentication
 * (LUMEN_MASTER_SPEC_V3 §20.2), not a FastAPI-issued session.
 *
 * `login` is a full-page redirect to Catalyst's hosted login, not an
 * API call — there is no credential form this app owns. This is
 * intentionally the only place that owns session state — pages and
 * components should consume it via useAuth(), never call authService
 * directly.
 */
export function AuthProvider({ children }) {
  const [operator, setOperator] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCurrentOperator()
      .then(setOperator)
      .catch(() => setOperator(null))
      .finally(() => setIsLoading(false));
  }, []);

  const login = () => {
    redirectToLogin();
  };

  const logout = async () => {
    await logoutRequest();
    setOperator(null);
  };

  const value = useMemo(
    () => ({
      operator,
      isAuthenticated: Boolean(operator),
      isLoading,
      login,
      logout,
    }),
    [operator, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
