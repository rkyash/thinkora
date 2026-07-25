import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface NotebookState {
  activeNotebookId: string | null
  sidebarOpen: boolean
  activeTab: 'chat' | 'notes' | 'flashcards' | 'quiz' | 'graph' | 'audio'

  // Actions
  setActiveNotebook: (id: string | null) => void
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setActiveTab: (tab: NotebookState['activeTab']) => void
}

export const useNotebookStore = create<NotebookState>()(
  persist(
    (set) => ({
      activeNotebookId: null,
      sidebarOpen: true,
      activeTab: 'chat',

      setActiveNotebook: (id) => set({ activeNotebookId: id }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setActiveTab: (tab) => set({ activeTab: tab }),
    }),
    {
      name: 'thinkora_notebook',
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        activeTab: state.activeTab,
      }),
    },
  ),
)
