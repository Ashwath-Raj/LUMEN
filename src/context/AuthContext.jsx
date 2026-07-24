import { useEffect, useMemo, useState } from 'react';
import { loginRequest, logoutRequest, fetchCurrentOperator } from '@/services/api/authService.js';
import { AuthContext } from './AuthContext.js';

/**
 * Provides: { operator, isAuthenticated, isLoading, login, logout }
 * `operator` shape (from FastAPI /me): { id, name, role, clearance, unit }
 *
 * This is intentionally the only place that owns session state — pages and
 * components should consume it via useAuth(), never call authService directly.
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

  const login = async (credentials) => {
    const nextOperator = await loginRequest(credentials);
    setOperator(nextOperator);
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
