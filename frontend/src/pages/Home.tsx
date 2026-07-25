import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { ROUTES, LOCAL_STORAGE_KEYS } from '@/utils/constants'
import { env } from '@/config/env'

/**
 * Dynamic Home redirector.
 * - Redirects already logged-in users straight to the Dashboard.
 * - Redirects guests straight to the Login page.
 */
export function Home() {
  const { accessToken } = useAuthStore()
  const token = accessToken || localStorage.getItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)

  if (token || !env.VITE_AUTH_ENABLED) {
    return <Navigate to={ROUTES.DASHBOARD} replace />
  }

  return <Navigate to={ROUTES.LOGIN} replace />
}
