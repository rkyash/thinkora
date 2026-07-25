import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types/api'
import { LOCAL_STORAGE_KEYS } from '@/utils/constants'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null

  // Actions
  login: (user: User, tokens: { access_token: string; refresh_token: string }) => void
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: typeof window !== 'undefined' ? localStorage.getItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN) : null,
      refreshToken: typeof window !== 'undefined' ? localStorage.getItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN) : null,

      login: (user, tokens) => {
        localStorage.setItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token)
        localStorage.setItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token)
        set({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token })
      },

      logout: () => {
        localStorage.removeItem(LOCAL_STORAGE_KEYS.ACCESS_TOKEN)
        localStorage.removeItem(LOCAL_STORAGE_KEYS.REFRESH_TOKEN)
        set({ user: null, accessToken: null, refreshToken: null })
      },

      setUser: (user) => set({ user }),
    }),
    {
      name: 'thinkora_auth',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
)
