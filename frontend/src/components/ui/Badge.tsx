import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  `inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium
   transition-colors select-none`,
  {
    variants: {
      variant: {
        default:
          'bg-primary/15 text-primary border border-primary/20',
        secondary:
          'bg-secondary text-secondary-foreground',
        destructive:
          'bg-terminal-red/15 text-terminal-red border border-terminal-red/20',
        outline:
          'border border-border text-foreground bg-transparent',
        success:
          'bg-terminal-green/15 text-terminal-green border border-terminal-green/20',
        warning:
          'bg-terminal-yellow/15 text-terminal-yellow border border-terminal-yellow/20',
        muted:
          'bg-muted text-muted-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}
