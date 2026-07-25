import { QueryClient } from '@tanstack/react-query'

/**
 * TanStack Query client configuration.
 * - staleTime: 60s — most data is fresh for 1 minute
 * - gcTime: 5min — keep in garbage-collected cache for 5 minutes
 * - retry: 2 — retry failed requests twice before showing error
 * - refetchOnWindowFocus: false — prevent noisy re-fetches on tab switch
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,         // 1 minute
      gcTime: 5 * 60 * 1000,        // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
})
