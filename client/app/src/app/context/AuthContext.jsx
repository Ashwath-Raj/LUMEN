import { useEffect, useMemo, useState } from 'react';
import { loginRequest, logoutRequest, fetchCurrentOperator } from '@/api/authService.js';
import { AuthContext } from './AuthContext.js';

/**
 * Provides: { operator, isAuthenticated, isLoading, login, logout }
 * `operator` shape: { id, name, email } — from Catalyst Authentication
 * (LUMEN_MASTER_SPEC_V3 §20.2), not a FastAPI-issued session.
 *
 * `login` has two outcomes depending on the runtime (see authService.js):
 * under the Catalyst runtime it initiates a full-page redirect to the
 * hosted login (the promise resolves null and the page navigates away);
 * under plain Vite dev it resolves the mock operator directly. This is
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

  const login = async () => {
    const nextOperator = await loginRequest();
    if (nextOperator) setOperator(nextOperator);
    return nextOperator;
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
