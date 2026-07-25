// Typed wrappers around import.meta.env for all Vite env variables.

export const env = {
  /** Backend API base URL, e.g. http://localhost:8000 */
  VITE_API_URL: import.meta.env.VITE_API_URL as string ?? 'http://localhost:8000',

  /** Application name shown in the UI */
  VITE_APP_NAME: import.meta.env.VITE_APP_NAME as string ?? 'Thinkora',

  /** Whether the app is running in development mode */
  DEV: import.meta.env.DEV as boolean,

  /** Whether the app is running in production mode */
  PROD: import.meta.env.PROD as boolean,

  /** Current mode: 'development' | 'production' | 'test' */
  MODE: import.meta.env.MODE as string,

  /** Enable/disable authentication flow */
  VITE_AUTH_ENABLED: import.meta.env.VITE_AUTH_ENABLED !== 'false',
} as const
