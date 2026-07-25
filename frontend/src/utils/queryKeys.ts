/**
 * Centralized TanStack Query key factories.
 * Using factory functions ensures keys are typed and consistent.
 */

export const workspaceKeys = {
  all: ['workspaces'] as const,
  lists: () => [...workspaceKeys.all, 'list'] as const,
  list: (params?: object) => [...workspaceKeys.lists(), params ?? {}] as const,
  details: () => [...workspaceKeys.all, 'detail'] as const,
  detail: (id: string) => [...workspaceKeys.details(), id] as const,
}

export const notebookKeys = {
  all: ['notebooks'] as const,
  lists: () => [...notebookKeys.all, 'list'] as const,
  list: (workspaceId?: string, params?: object) =>
    [...notebookKeys.lists(), workspaceId ?? 'all', params ?? {}] as const,
  details: () => [...notebookKeys.all, 'detail'] as const,
  detail: (id: string) => [...notebookKeys.details(), id] as const,
}

export const sourceKeys = {
  all: ['sources'] as const,
  lists: () => [...sourceKeys.all, 'list'] as const,
  list: (notebookId: string, params?: object) =>
    [...sourceKeys.lists(), notebookId, params ?? {}] as const,
  details: () => [...sourceKeys.all, 'detail'] as const,
  detail: (id: string) => [...sourceKeys.details(), id] as const,
}

export const chatKeys = {
  all: ['chat'] as const,
  sessions: (notebookId: string) => [...chatKeys.all, 'sessions', notebookId] as const,
  session: (sessionId: string) => [...chatKeys.all, 'session', sessionId] as const,
  messages: (sessionId: string) => [...chatKeys.all, 'messages', sessionId] as const,
}

export const noteKeys = {
  all: ['notes'] as const,
  list: (notebookId: string) => [...noteKeys.all, 'list', notebookId] as const,
  detail: (id: string) => [...noteKeys.all, 'detail', id] as const,
}

export const flashcardKeys = {
  all: ['flashcards'] as const,
  list: (notebookId: string) => [...flashcardKeys.all, 'list', notebookId] as const,
}

export const quizKeys = {
  all: ['quizzes'] as const,
  list: (notebookId: string) => [...quizKeys.all, 'list', notebookId] as const,
  detail: (id: string) => [...quizKeys.all, 'detail', id] as const,
}

export const graphKeys = {
  all: ['graph'] as const,
  detail: (notebookId: string) => [...graphKeys.all, notebookId] as const,
}

export const searchKeys = {
  all: ['search'] as const,
  results: (query: string, params?: object) =>
    [...searchKeys.all, query, params ?? {}] as const,
}

export const settingsKeys = {
  all: ['settings'] as const,
}

export const meKeys = {
  all: ['me'] as const,
}

export const audioKeys = {
  all: ['audio'] as const,
  status: (notebookId: string) => [...audioKeys.all, 'status', notebookId] as const,
}
