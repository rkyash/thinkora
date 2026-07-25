import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ROUTES } from '@/utils/constants'
import { ProtectedRoute, GuestRoute } from '@/components/layout/ProtectedRoute'
import { Home } from '@/pages/Home'
import { Login } from '@/pages/Login'
import { Register } from '@/pages/Register'
import { Dashboard } from '@/pages/Dashboard'
import { Notebook } from '@/pages/Notebook'
import { WorkspaceNotebooks } from '@/pages/WorkspaceNotebooks'
import { Settings } from '@/pages/Settings'
import { Search } from '@/pages/Search'
import { NotFound } from '@/pages/NotFound'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public landing */}
        <Route path={ROUTES.HOME} element={<Home />} />

        {/* Auth pages — redirect away if already logged in */}
        <Route
          path={ROUTES.LOGIN}
          element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          }
        />
        <Route
          path={ROUTES.REGISTER}
          element={
            <GuestRoute>
              <Register />
            </GuestRoute>
          }
        />

        {/* Protected pages — redirect to /login if not authed */}
        <Route
          path={ROUTES.DASHBOARD}
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.NOTEBOOK}
          element={
            <ProtectedRoute>
              <Notebook />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.WORKSPACE}
          element={
            <ProtectedRoute>
              <WorkspaceNotebooks />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.SETTINGS}
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.SEARCH}
          element={
            <ProtectedRoute>
              <Search />
            </ProtectedRoute>
          }
        />

        <Route path={ROUTES.NOT_FOUND} element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
