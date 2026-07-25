import React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Optional icon rendered on the left inside the input */
  startIcon?: React.ReactNode
  /** Optional icon/button rendered on the right inside the input */
  endIcon?: React.ReactNode
  /** Show a red error border and style */
  error?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', startIcon, endIcon, error, ...props }, ref) => {
    if (startIcon ?? endIcon) {
      return (
        <div className="relative flex items-center">
          {startIcon && (
            <span className="absolute left-3 text-muted-foreground pointer-events-none">
              {startIcon}
            </span>
          )}
          <input
            type={type}
            ref={ref}
            className={cn(
              `w-full rounded-lg bg-background border px-4 py-2.5 text-sm
               text-foreground placeholder:text-muted-foreground
               focus:outline-none focus:ring-2 focus:ring-ring transition-all`,
              startIcon && 'pl-9',
              endIcon && 'pr-9',
              error
                ? 'border-destructive focus:ring-destructive/50'
                : 'border-border',
              className,
            )}
            {...props}
          />
          {endIcon && (
            <span className="absolute right-3 text-muted-foreground">
              {endIcon}
            </span>
          )}
        </div>
      )
    }

    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          `w-full rounded-lg bg-background border px-4 py-2.5 text-sm
           text-foreground placeholder:text-muted-foreground
           focus:outline-none focus:ring-2 focus:ring-ring transition-all`,
          error
            ? 'border-destructive focus:ring-destructive/50'
            : 'border-border',
          className,
        )}
        {...props}
      />
    )
  },
)

Input.displayName = 'Input'
