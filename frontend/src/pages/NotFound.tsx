import React from 'react'
import { Link } from 'react-router-dom'
import { ROUTES } from '@/utils/constants'

export function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6 text-center px-4">
      <div className="text-8xl font-bold gradient-text">404</div>
      <h1 className="text-2xl font-semibold text-foreground">Page not found</h1>
      <p className="text-muted-foreground max-w-sm">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link
        to={ROUTES.HOME}
        className="px-6 py-2.5 rounded-lg bg-primary text-primary-foreground font-medium
                   hover:opacity-90 active:scale-[0.98] transition-all duration-150"
      >
        Back to home
      </Link>
    </div>
  )
}
