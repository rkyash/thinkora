import React, { useEffect, useCallback } from 'react'
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastVariant = 'success' | 'error' | 'info' | 'warning'

export interface ToastMessage {
  id: string
  message: string
  variant?: ToastVariant
  duration?: number
}

// ─── Single Toast ─────────────────────────────────────────────────────────────

interface ToastProps extends ToastMessage {
  onDismiss: (id: string) => void
}

const icons: Record<ToastVariant, React.ReactNode> = {
  success: <CheckCircle2 className="w-4 h-4 text-terminal-green shrink-0" />,
  error:   <AlertCircle  className="w-4 h-4 text-terminal-red shrink-0" />,
  info:    <Info         className="w-4 h-4 text-primary shrink-0" />,
  warning: <AlertTriangle className="w-4 h-4 text-terminal-yellow shrink-0" />,
}

const toastStyles: Record<ToastVariant, string> = {
  success: 'border-terminal-green/20 bg-terminal-green/10',
  error:   'border-terminal-red/20 bg-terminal-red/10',
  info:    'border-primary/20 bg-primary/10',
  warning: 'border-terminal-yellow/20 bg-terminal-yellow/10',
}

function Toast({ id, message, variant = 'info', duration = 4000, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), duration)
    return () => clearTimeout(timer)
  }, [id, duration, onDismiss])

  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 px-4 py-3 rounded-xl border glass shadow-lg animate-slide-in-right',
        toastStyles[variant],
      )}
    >
      {icons[variant]}
      <p className="text-sm text-foreground flex-1">{message}</p>
      <button
        onClick={() => onDismiss(id)}
        aria-label="Dismiss notification"
        className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}

// ─── Toast Container ──────────────────────────────────────────────────────────

interface ToastContainerProps {
  toasts: ToastMessage[]
  onDismiss: (id: string) => void
}

export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div
      aria-live="polite"
      aria-label="Notifications"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]"
    >
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

// ─── useToast hook ────────────────────────────────────────────────────────────

import { useState } from 'react'

function generateId() {
  return `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toast = useCallback(
    (message: string, variant: ToastVariant = 'info', duration = 4000) => {
      const id = generateId()
      setToasts((prev) => [...prev, { id, message, variant, duration }])
      return id
    },
    [],
  )

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const success = (msg: string, dur?: number) => toast(msg, 'success', dur)
  const error   = (msg: string, dur?: number) => toast(msg, 'error', dur)
  const info    = (msg: string, dur?: number) => toast(msg, 'info', dur)
  const warning = (msg: string, dur?: number) => toast(msg, 'warning', dur)

  return { toasts, toast, dismiss, success, error, info, warning }
}
