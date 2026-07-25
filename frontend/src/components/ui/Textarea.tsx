import React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          `w-full rounded-lg bg-background border px-4 py-2.5 text-sm
           text-foreground placeholder:text-muted-foreground
           focus:outline-none focus:ring-2 focus:ring-ring transition-all
           resize-none min-h-[80px]`,
          error ? 'border-destructive focus:ring-destructive/50' : 'border-border',
          className,
        )}
        {...props}
      />
    )
  },
)

Textarea.displayName = 'Textarea'
