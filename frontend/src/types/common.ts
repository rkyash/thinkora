/**
 * Shared enums, utility types, and common type helpers used across the app.
 */

// ─── Route Paths ─────────────────────────────────────────────────────────────
// Imported from utils/constants.ts — re-exported here for convenience
export type { ROUTES } from '@/utils/constants'

// ─── UI State ────────────────────────────────────────────────────────────────

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export type Theme = 'dark' | 'light' | 'system'

export type SidebarTab = 'sources' | 'notes' | 'chat'

export type NotebookTab = 'chat' | 'notes' | 'flashcards' | 'quiz' | 'graph' | 'audio'

// ─── Generic Helpers ─────────────────────────────────────────────────────────

/** Make all properties of T optional at the top level, but deeply required beneath */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/** Make only the given keys of T required */
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

/** Extract the value type from an object */
export type ValueOf<T> = T[keyof T]

/** Pagination parameters for list requests */
export interface PaginationParams {
  page?: number
  limit?: number
  search?: string
}
