import axios from 'axios'
import { env } from '@/config/env'

/**
 * Shared Axios instance used by all API call functions.
 * - Automatically attaches JWT from localStorage
 * - Redirects to /login on 401 responses
 */
export const apiClient = axios.create({
  baseURL: env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
})

// ─── Request Interceptor ────────────────────────────────────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ─── Response Interceptor ───────────────────────────────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401 && env.VITE_AUTH_ENABLED) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      // Redirect to login, preserving intended destination
      const currentPath = window.location.pathname
      if (currentPath !== '/login' && currentPath !== '/register') {
        window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
      }
    }
    return Promise.reject(error)
  },
)
