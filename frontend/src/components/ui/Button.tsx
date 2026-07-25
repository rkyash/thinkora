import React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  `inline-flex items-center justify-center gap-2 rounded-lg text-sm font-medium
   transition-all duration-200 focus-visible:outline-none focus-visible:ring-2
   focus-visible:ring-ring focus-visible:ring-offset-1 disabled:pointer-events-none
   disabled:opacity-50 select-none whitespace-nowrap`,
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground hover:opacity-90 shadow-sm glow-sm',
        destructive:
          'bg-destructive text-destructive-foreground hover:opacity-90',
        outline:
          'border border-border bg-transparent hover:bg-accent hover:text-accent-foreground',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost:
          'hover:bg-accent hover:text-accent-foreground',
        link:
          'text-primary underline-offset-4 hover:underline p-0 h-auto',
        glass:
          'glass hover:bg-accent/50 hover:glow-sm',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-7 px-3 text-xs',
        lg: 'h-11 px-6 text-base',
        icon: 'h-9 w-9 p-0',
        'icon-sm': 'h-7 w-7 p-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /**
   * When true, renders as a Slot — merges props onto the single child element
   * instead of rendering a <button>. Use with <Link> for accessible link-buttons.
   *
   * Example: <Button asChild variant="default"><Link to="/home">Go</Link></Button>
   */
  asChild?: boolean
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, children, ...props }, ref) => {
    const computedClass = cn(buttonVariants({ variant, size }), className)

    // asChild: merge button styles + props onto the single child element
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(
        children as React.ReactElement<React.HTMLAttributes<HTMLElement>>,
        {
          // Spread button props (except ref) onto the child
          ...props,
          className: cn(
            computedClass,
            (children as React.ReactElement<{ className?: string }>).props.className,
          ),
        },
      )
    }

    return (
      <button
        ref={ref}
        className={computedClass}
        {...props}
      >
        {children}
      </button>
    )
  },
)

Button.displayName = 'Button'
