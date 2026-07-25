import React from 'react'
import { cn } from '@/lib/utils'

interface SpinnerProps {
  /** Tailwind size class override, e.g. 'w-8 h-8' */
  className?: string
  /** Accessible label for screen readers */
  label?: string
}

/**
 * Animated ring spinner. Uses a CSS-only border-top trick so it doesn't
 * require any additional dependencies.
 */
export function Spinner({ className, label = 'Loading…' }: SpinnerProps) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn(
        'inline-block rounded-full border-2 border-current border-t-transparent animate-spin text-primary',
        'w-5 h-5',
        className,
      )}
    />
  )
}

/** Full-page centered spinner overlay */
export function PageSpinner() {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm z-50">
      <div className="flex flex-col items-center gap-3">
        <Spinner className="w-10 h-10" />
        <p className="text-sm text-muted-foreground animate-pulse">Loading…</p>
      </div>
    </div>
  )
}

/** Inline centered spinner for content areas */
export function InlineSpinner({ text }: { text?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
      <Spinner />
      {text && <span className="text-sm">{text}</span>}
    </div>
  )
}
