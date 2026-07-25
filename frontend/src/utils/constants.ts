/**
 * Application-wide string constants — route paths, query params, etc.
 * Import these instead of inline strings to prevent typos.
 */

export const ROUTES = {
  HOME: '/',
  DASHBOARD: '/dashboard',
  LOGIN: '/login',
  REGISTER: '/register',
  NOTEBOOK: '/notebook/:id',
  WORKSPACE: '/workspaces/:workspaceId',
  SETTINGS: '/settings',
  SEARCH: '/search',
  NOT_FOUND: '*',

  // Helpers
  notebook: (id: string) => `/notebook/${id}`,
  workspace: (id: string) => `/workspaces/${id}`,
} as const

export const LOCAL_STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  THEME: 'thinkora_theme',
  SIDEBAR_WIDTH: 'thinkora_sidebar_width',
} as const

export const API_TAGS = {
  WORKSPACES: 'workspaces',
  NOTEBOOKS: 'notebooks',
  SOURCES: 'sources',
  CHAT_SESSIONS: 'chat_sessions',
  MESSAGES: 'messages',
  NOTES: 'notes',
  FLASHCARDS: 'flashcards',
  QUIZZES: 'quizzes',
  GRAPH: 'graph',
  AUDIO: 'audio',
  SEARCH: 'search',
  SETTINGS: 'settings',
  ME: 'me',
} as const

export const DEFAULT_PAGE_SIZE = 20

export const MAX_FILE_SIZE_MB = 100
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

export const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/csv',
  'text/markdown',
  'text/plain',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
  'application/epub+zip',
  'audio/mpeg',
  'audio/wav',
  'audio/ogg',
  'image/png',
  'image/jpeg',
  'image/webp',
] as const
