import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Theme } from '@/types/common'

interface SettingsState {
  theme: Theme
  sidebarWidth: number

  // Actions
  setTheme: (theme: Theme) => void
  setSidebarWidth: (width: number) => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarWidth: 280,

      setTheme: (theme) => set({ theme }),
      setSidebarWidth: (width) => set({ sidebarWidth: width }),
    }),
    {
      name: 'thinkora_settings',
    },
  ),
)
