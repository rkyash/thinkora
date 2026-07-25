import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQueryClient, useMutation } from '@tanstack/react-query'
import {
  Plus,
  Edit2,
  Trash2,
  Clock,
  ArrowRight,
  ChevronLeft,
} from 'lucide-react'
import { Layout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Modal, ModalFooter } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { useWorkspace } from '@/hooks/useWorkspaces'
import { useNotebooks, useCreateNotebook } from '@/hooks/useNotebooks'
import * as notebooksApi from '@/api/notebooks'
import { notebookKeys } from '@/utils/queryKeys'
import { ROUTES } from '@/utils/constants'
import { cn } from '@/lib/utils'

export function WorkspaceNotebooks() {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const activeWorkspaceId = workspaceId || ''

  // Fetch workspace and its notebooks
  const { data: workspace, isLoading: isLoadingWorkspace } = useWorkspace(activeWorkspaceId)
  const { data: notebooks = [], isLoading: isLoadingNotebooks } = useNotebooks(activeWorkspaceId)

  // Mutations
  const createNotebookMutation = useCreateNotebook(activeWorkspaceId)

  // Flexible update mutation to handle any notebook ID dynamically
  const updateNotebookMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { name: string; description?: string; emoji?: string } }) =>
      notebooksApi.updateNotebook(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notebookKeys.list(activeWorkspaceId) })
    },
  })

  // Flexible delete mutation to handle any notebook ID dynamically
  const deleteNotebookMutation = useMutation({
    mutationFn: (id: string) => notebooksApi.deleteNotebook(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notebookKeys.list(activeWorkspaceId) })
    },
  })

  // Filter state
  const [filter, setFilter] = useState<'all' | 'recent' | 'favorites'>('all')

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createDescription, setCreateDescription] = useState('')
  const [createEmoji, setCreateEmoji] = useState('📚')

  const [editingNotebook, setEditingNotebook] = useState<{ id: string; name: string; description: string; emoji: string } | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')
  const [editEmoji, setEditEmoji] = useState('📚')

  const [deletingNotebook, setDeletingNotebook] = useState<{ id: string; name: string } | null>(null)

  const PRESET_EMOJIS = ['📚', '🧬', '💻', '🎯', '📊', '🔬', '🧠', '💡', '🎨', '🪐', '🧪', '🖋️']

  // Handlers
  const handleCreateNotebook = () => {
    setCreateName('')
    setCreateDescription('')
    const emojis = ['📚', '🧬', '💻', '🎯', '📊', '🔬', '🧠', '💡', '🎨']
    const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)]
    setCreateEmoji(randomEmoji)
    setIsCreateOpen(true)
  }

  const handleEditNotebook = (
    e: React.MouseEvent,
    id: string,
    currentName: string,
    currentDesc?: string | null,
    currentEmoji?: string | null
  ) => {
    e.stopPropagation() // Prevent navigating to single notebook
    setEditName(currentName)
    setEditDescription(currentDesc ?? '')
    setEditEmoji(currentEmoji ?? '📚')
    setEditingNotebook({ id, name: currentName, description: currentDesc ?? '', emoji: currentEmoji ?? '📚' })
  }

  const handleDeleteNotebook = (e: React.MouseEvent, id: string, name: string) => {
    e.stopPropagation() // Prevent navigating to single notebook
    setDeletingNotebook({ id, name })
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

  const submitEditNotebook = (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingNotebook || !editName.trim()) return
    updateNotebookMutation.mutate({
      id: editingNotebook.id,
      data: { name: editName, description: editDescription, emoji: editEmoji },
    }, {
      onSuccess: () => {
        setEditingNotebook(null)
      }
    })
  }

  const submitDeleteNotebook = () => {
    if (!deletingNotebook) return
    deleteNotebookMutation.mutate(deletingNotebook.id, {
      onSuccess: () => {
        setDeletingNotebook(null)
      }
    })
  }

  if (isLoadingWorkspace) {
    return (
      <Layout title="Notebooks" activeWorkspaceId={activeWorkspaceId}>
        <div className="flex items-center justify-center min-h-[60vh] text-muted-foreground text-sm">
          Loading workspace...
        </div>
      </Layout>
    )
  }

  return (
    <Layout
      title={workspace ? `${workspace.name} — Notebooks` : "Notebooks"}
      activeWorkspaceId={activeWorkspaceId}
      showSearch={false}
    >
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-8 animate-fade-in">
        {/* Back navigation & Workspace Details */}
        <div className="space-y-4">
          <button
            onClick={() => navigate(ROUTES.DASHBOARD)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            Back to Dashboard
          </button>
          
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-headline font-bold text-foreground tracking-tight">
                {workspace?.name}
              </h1>
              <p className="text-muted-foreground text-sm mt-1">
                {workspace?.description || 'Manage your study notebooks for this workspace context.'}
              </p>
            </div>
            <Button
              onClick={handleCreateNotebook}
              className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold flex items-center gap-2 h-10 shadow-sm active:scale-[0.98] transition-all duration-150"
            >
              <Plus className="w-4 h-4" />
              New Notebook
            </Button>
          </div>
        </div>

        {/* Notebooks Grid & Filters */}
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-headline font-semibold text-foreground flex items-center gap-2">
              Notebooks
              <span className="text-xs font-mono text-muted-foreground font-normal border border-border rounded px-1.5 py-0.5 bg-background">
                {notebooks.length}
              </span>
            </h2>

            <div className="flex gap-1 bg-background p-1 rounded-lg border border-border text-xs">
              {(['all', 'recent', 'favorites'] as const).map((opt) => (
                <button
                  key={opt}
                  onClick={() => setFilter(opt)}
                  className={cn(
                    "px-2.5 py-1 rounded-md capitalize transition-colors font-medium",
                    filter === opt ? "bg-primary/20 text-primary" : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {isLoadingNotebooks ? (
              <div className="col-span-full py-12 flex justify-center text-muted-foreground text-sm">
                Loading notebooks...
              </div>
            ) : notebooks.length === 0 ? (
              <div className="col-span-full py-12 text-center text-muted-foreground">
                <p>No notebooks found in this workspace yet. Create one to get started!</p>
              </div>
            ) : (
              notebooks.map((nb, idx) => (
                <div
                  key={nb.id}
                  onClick={() => navigate(ROUTES.notebook(nb.id))}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(ROUTES.notebook(nb.id));
                    }
                  }}
                  className="glass-panel rounded-xl p-5 hover:border-primary/20 hover:glow-sm hover:-translate-y-0.5 transition-all duration-200 cursor-pointer flex flex-col justify-between group relative"
                  style={{ animationDelay: `${idx * 0.05}s` }}
                >
                  <div className="space-y-3">
                    <div className="flex justify-between items-start">
                      <span className="text-3xl filter drop-shadow-sm select-none">
                        {nb.emoji || '📓'}
                      </span>
                      
                      {/* Action buttons */}
                      <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          type="button"
                          aria-label="Edit notebook"
                          onClick={(e) => handleEditNotebook(e, nb.id, nb.name, nb.description, nb.emoji)}
                          className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          aria-label="Delete notebook"
                          onClick={(e) => handleDeleteNotebook(e, nb.id, nb.name)}
                          className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-headline font-bold text-base text-foreground group-hover:text-primary transition-colors truncate">
                        {nb.name}
                      </h3>
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-2 leading-relaxed h-8">
                        {nb.description || 'No description provided.'}
                      </p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center border-t border-border pt-3 mt-4 text-[10px] text-muted-foreground font-mono">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-primary" />
                      Recently updated
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-primary opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </div>
              ))
            )}

            {/* Create Notebook Card Placeholder */}
            <div
              onClick={handleCreateNotebook}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleCreateNotebook();
                }
              }}
              className="rounded-xl border border-dashed border-border hover:border-primary/50 bg-background hover:bg-accent flex flex-col items-center justify-center p-6 text-center cursor-pointer transition-all duration-200 group hover:glow-sm min-h-[160px] hover:-translate-y-0.5"
            >
              <div className="w-10 h-10 rounded-full bg-card flex items-center justify-center mb-3 border border-border group-hover:bg-primary/10 group-hover:border-primary/20 transition-colors">
                <Plus className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              <span className="font-semibold text-sm text-foreground">Create Notebook</span>
              <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
                Add a new notebook to this workspace and begin your AI study journey.
              </p>
            </div>
          </div>
        </div>
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
                    "w-9 h-9 text-lg rounded-lg flex items-center justify-center transition-all border shrink-0",
                    createEmoji === emoji
                      ? "bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/25 scale-105"
                      : "bg-background border-border hover:bg-accent text-foreground"
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
              className="bg-primary hover:bg-violet-primary text-primary-foreground font-semibold active:scale-[0.98] transition-all duration-150"
            >
              {createNotebookMutation.isPending ? 'Creating...' : 'Create Notebook'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Edit Notebook Modal */}
      <Modal
        open={Boolean(editingNotebook)}
        onClose={() => setEditingNotebook(null)}
        title="Edit Notebook"
        description="Update notebook metadata and configuration."
      >
        <form onSubmit={submitEditNotebook} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Notebook Name
            </label>
            <Input
              required
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="Notebook Name"
              autoFocus
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Description (optional)
            </label>
            <Textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Notebook Description"
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
                  onClick={() => setEditEmoji(emoji)}
                  className={cn(
                    "w-9 h-9 text-lg rounded-lg flex items-center justify-center transition-all border shrink-0",
                    editEmoji === emoji
                      ? "bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/25 scale-105"
                      : "bg-background border-border hover:bg-accent text-foreground"
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
              onClick={() => setEditingNotebook(null)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateNotebookMutation.isPending}
              className="bg-primary hover:bg-violet-primary text-primary-foreground font-semibold active:scale-[0.98] transition-all duration-150"
            >
              {updateNotebookMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>

      {/* Delete Notebook Confirmation Modal */}
      <Modal
        open={Boolean(deletingNotebook)}
        onClose={() => setDeletingNotebook(null)}
        title="Delete Notebook"
        description={`Are you sure you want to delete the notebook "${deletingNotebook?.name}"?`}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground leading-relaxed">
            This action is permanent and will delete all associated study sources, chats, flashcards, quizzes, and notes inside this notebook.
          </p>
          <ModalFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setDeletingNotebook(null)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={submitDeleteNotebook}
              disabled={deleteNotebookMutation.isPending}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground font-semibold active:scale-[0.98] transition-all duration-150"
            >
              {deleteNotebookMutation.isPending ? 'Deleting...' : 'Delete Notebook'}
            </Button>
          </ModalFooter>
        </div>
      </Modal>
    </Layout>
  )
}
