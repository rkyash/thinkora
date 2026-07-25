import React, { useEffect, useCallback } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './Button'

export interface ModalProps {
  /** Whether the modal is visible */
  open: boolean
  /** Called when the user dismisses the modal (Escape key, backdrop click, × button) */
  onClose: () => void
  /** Modal title displayed in the header */
  title?: string
  /** Optional description below the title */
  description?: string
  /** Modal body content */
  children: React.ReactNode
  /** Additional class names for the panel */
  className?: string
  /** Prevent closing when clicking the backdrop */
  disableBackdropClose?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-3xl',
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  className,
  disableBackdropClose = false,
  size = 'md',
}: ModalProps) {
  // Close on Escape
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    },
    [onClose],
  )

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [open, handleKeyDown])

  if (!open) return null

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* Dim overlay */}
      <div
        className="absolute inset-0 bg-background/70 backdrop-blur-sm animate-fade-in"
        onClick={disableBackdropClose ? undefined : onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className={cn(
          'relative z-10 w-full glass rounded-2xl shadow-2xl animate-fade-in',
          sizeClasses[size],
          className,
        )}
      >
        {/* Header */}
        {(title ?? description) && (
          <div className="flex items-start justify-between gap-4 p-6 pb-4">
            <div className="space-y-1">
              {title && (
                <h2 id="modal-title" className="text-lg font-semibold text-foreground">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-sm text-muted-foreground">{description}</p>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onClose}
              aria-label="Close modal"
              className="shrink-0 -mt-1 -mr-1"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        )}

        {/* Body */}
        <div className={cn('px-6 pb-6', !(title ?? description) && 'pt-6')}>
          {children}
        </div>
      </div>
    </div>
  )
}

/** Footer utility for modal action buttons */
export function ModalFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('flex items-center justify-end gap-3 pt-4 mt-4 border-t border-border', className)}>
      {children}
    </div>
  )
}
