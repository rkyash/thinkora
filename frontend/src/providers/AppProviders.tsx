import React from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { ToastContainer, useToast } from '@/components/ui/Toast'
import { ThemeProvider } from './ThemeProvider'

interface AppProvidersProps {
  children: React.ReactNode
}

/**
 * Root provider tree.
 * - QueryClientProvider: TanStack server state
 * - ToastContainer: global notification system
 */
function ToastLayer({ children }: { children: React.ReactNode }) {
  const { toasts, dismiss } = useToast()
  return (
    <>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </>
  )
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ToastLayer>
          {children}
        </ToastLayer>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
