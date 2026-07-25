import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { ROUTES, LOCAL_STORAGE_KEYS } from '@/utils/constants'
import { PageSpinner } from '@/components/ui/Spinner'
import { env } from '@/config/env'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Redirects unauthenticated users to /login, preserving the intended URL
 * as a `?redirect=` query param so they land back after logging in.
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { accessToken } = useAuthStore()
  const location = useLocation()
  const token = accessToken || localStorage.getItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)

  if (!token && env.VITE_AUTH_ENABLED) {
    return (
      <Navigate
        to={`${ROUTES.LOGIN}?redirect=${encodeURIComponent(location.pathname)}`}
        replace
      />
    )
  }

  return <>{children}</>
}

/**
 * Redirects already-authenticated users away from auth pages (login/register)
 * to the home page.
 */
export function GuestRoute({ children }: ProtectedRouteProps) {
  const { accessToken } = useAuthStore()
  const token = accessToken || localStorage.getItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)

  if (token || !env.VITE_AUTH_ENABLED) {
    return <Navigate to={ROUTES.DASHBOARD} replace />
  }

  return <>{children}</>
}
