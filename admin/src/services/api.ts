import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

const ACCESS_TOKEN_KEY = "sarmaan_access_token";
const REFRESH_TOKEN_KEY = "sarmaan_refresh_token";

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On a 401 (expired/invalid access token), try exactly once to refresh via
// the stored refresh token and replay the original request. If refresh also
// fails, clear tokens and let the 401 propagate — AuthProvider's loadCurrentUser
// (or ProtectedRoute) is what actually redirects to /login.
let refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original._retried) {
      throw error;
    }
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw error;
    }
    original._retried = true;
    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post(`${api.defaults.baseURL}/auth/refresh`, { refresh_token: refreshToken })
          .then((resp) => {
            const newToken = resp.data.access_token;
            localStorage.setItem(ACCESS_TOKEN_KEY, newToken);
            return newToken;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }
      const newToken = await refreshPromise;
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    } catch (refreshError) {
      localStorage.removeItem(ACCESS_TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      throw error;
    }
  },
);
