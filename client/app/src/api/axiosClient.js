import axios from 'axios';

/**
 * Single axios instance for the whole app. Base URL points at the FastAPI
 * backend (proxied through Vite in dev — see vite.config.js). All
 * services/api/*Service.js files import this rather than axios directly.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach clearance token if we're storing one client-side (in addition to
// the httpOnly session cookie FastAPI may set on login).
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('lumen_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralized 401 handling — bounce to login on session expiry.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('lumen_token');
      if (window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
