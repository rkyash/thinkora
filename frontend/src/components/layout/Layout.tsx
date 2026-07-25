import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import type { Notebook, Workspace } from '@/types/api'
import { useWorkspaces } from '@/hooks/useWorkspaces'
import { useNotebooks, useCreateNotebook, useNotebook } from '@/hooks/useNotebooks'
import { ROUTES } from '@/utils/constants'
import { Modal, ModalFooter } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Button } from '@/components/ui/Button'

interface LayoutProps {
  /** Page title shown in TopBar */
  title?: string
  /** Whether TopBar shows the search input */
  showSearch?: boolean
  /** Extra actions rendered in the TopBar right slot */
  topBarActions?: React.ReactNode
  /** Page content */
  children: React.ReactNode
  className?: string

  // Sidebar data (optional — provided internally if not supplied)
  workspaces?: Workspace[]
  notebooks?: Notebook[]
  activeWorkspaceId?: string | null
  isLoadingNotebooks?: boolean
  onCreateNotebook?: () => void
  onSelectWorkspace?: (id: string) => void
}

/**
 * Main authenticated layout — sidebar on the left, TopBar at the top,
 * scrollable content area on the right.
 */
export function Layout({
  title,
  showSearch,
  topBarActions,
  children,
  className,
  workspaces: propsWorkspaces,
  notebooks: propsNotebooks,
  activeWorkspaceId: propsActiveWorkspaceId,
  isLoadingNotebooks: propsIsLoadingNotebooks,
  onCreateNotebook: propsOnCreateNotebook,
  onSelectWorkspace,
}: LayoutProps) {
  const { workspaceId } = useParams<{ workspaceId?: string }>()
  const { id: notebookId } = useParams<{ id?: string }>()
  const navigate = useNavigate()

  // Fetch workspaces & notebooks internally for global sidebar synchronization
  const { data: workspaces = [] } = useWorkspaces()
  const { data: activeNotebook } = useNotebook(notebookId || '')

  const activeWorkspaceId =
    propsActiveWorkspaceId !== undefined
      ? propsActiveWorkspaceId
      : (workspaceId || activeNotebook?.workspace_id || null)
  
  const { data: notebooks = [], isLoading: isLoadingNotebooks } = useNotebooks(activeWorkspaceId || '')
  const createNotebookMutation = useCreateNotebook(activeWorkspaceId || '')

  const handleSelectWorkspace = (id: string) => {
    navigate(ROUTES.workspace(id))
  }

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createDescription, setCreateDescription] = useState('')
  const [createEmoji, setCreateEmoji] = useState('📚')

  const PRESET_EMOJIS = ['📚', '🧬', '💻', '🎯', '📊', '🔬', '🧠', '💡', '🎨', '🪐', '🧪', '🖋️']

  const handleCreateNotebook = () => {
    setCreateName('')
    setCreateDescription('')
    const emojis = ['📚', '🧬', '💻', '🎯', '📊', '🔬', '🧠', '💡', '🎨']
    const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)]
    setCreateEmoji(randomEmoji)
    setIsCreateOpen(true)
  }

  const submitCreateNotebook = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!createName.trim()) return
    try {
      await createNotebookMutation.mutateAsync({
        name: createName,
        description: createDescription,
        emoji: createEmoji,
      })
      setIsCreateOpen(false)
    } catch (err) {
      console.error('Failed to create notebook:', err)
    }
  }

  const finalWorkspaces = propsWorkspaces ?? workspaces
  const finalNotebooks = propsNotebooks ?? notebooks
  const finalActiveWorkspaceId = propsActiveWorkspaceId !== undefined ? propsActiveWorkspaceId : activeWorkspaceId
  const finalIsLoadingNotebooks = propsIsLoadingNotebooks ?? isLoadingNotebooks
  const finalOnCreateNotebook = propsOnCreateNotebook ?? handleCreateNotebook

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar
        workspaces={finalWorkspaces}
        notebooks={finalNotebooks}
        activeWorkspaceId={finalActiveWorkspaceId}
        isLoadingNotebooks={finalIsLoadingNotebooks}
        onCreateNotebook={finalOnCreateNotebook}
        onSelectWorkspace={onSelectWorkspace ?? handleSelectWorkspace}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar
          title={title}
          showSearch={showSearch}
          actions={topBarActions}
        />

        {/* Scrollable content */}
        <main
          className={cn('flex-1 overflow-y-auto', className)}
          id="main-content"
        >
          {children}
        </main>
      </div>

      {/* Create Notebook Modal */}
      <Modal
        open={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create Notebook"
        description="Add a new notebook to set up study sessions and store references."
      >
        <form onSubmit={submitCreateNotebook} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Notebook Name
            </label>
            <Input
              required
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="e.g. Machine Learning Basics, Organic Chemistry"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Description (optional)
            </label>
            <Textarea
              value={createDescription}
              onChange={(e) => setCreateDescription(e.target.value)}
              placeholder="What topics will this notebook focus on?"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
              Notebook Icon
            </label>
            <div className="flex flex-wrap gap-2 pt-1">
              {PRESET_EMOJIS.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => setCreateEmoji(emoji)}
                  className={cn(
                    "w-9 h-9 text-lg rounded-lg flex items-center justify-center transition-all duration-150 active:scale-[0.98] border shrink-0",
                    createEmoji === emoji
                      ? "bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/25 scale-105"
                      : "bg-surface/50 border-outline/10 hover:bg-accent text-foreground hover:border-outline/20"
                  )}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createNotebookMutation.isPending}
              className="bg-primary hover:bg-violet-primary text-primary-foreground font-semibold"
            >
              {createNotebookMutation.isPending ? 'Creating...' : 'Create Notebook'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  )
}

/**
 * Bare full-page layout — no sidebar/TopBar.
 * Used for auth pages (login, register) and landing.
 */
export function PageLayout({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('min-h-screen bg-background', className)}>
      {children}
    </div>
  )
}
