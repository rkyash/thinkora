import React, { useState, useEffect } from 'react'
import {
  Search,
  Plus,
  Bold,
  Italic,
  Heading1,
  List,
  Code,
  Link as LinkIcon,
  Brain,
  Sparkles,
  Loader2,
  Trash2,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { cn } from '@/lib/utils'
import { useParams } from 'react-router-dom'
import {
  useNotes,
  useCreateNote,
  useUpdateNote,
  useDeleteNote,
  useSummarizeNote,
} from '@/hooks/useGenerate'
import type { Note } from '@/types/api'

// Debounce hook for auto-save
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debouncedValue
}

export function NotesTab() {
  const { id: notebookId = '' } = useParams<{ id: string }>()

  // ─── Remote data ──────────────────────────────────────────────────────────
  const { data: notes = [], isLoading, isError } = useNotes(notebookId)
  const createNote = useCreateNote(notebookId)
  const updateNote = useUpdateNote(notebookId)
  const deleteNote = useDeleteNote(notebookId)
  const summarizeNote = useSummarizeNote(notebookId)

  // ─── Local state ──────────────────────────────────────────────────────────
  const [activeNoteId, setActiveNoteId] = useState<string | null>(null)
  const [localTitle, setLocalTitle] = useState('')
  const [localContent, setLocalContent] = useState('')
  const [searchVal, setSearchVal] = useState('')
  const [summaryText, setSummaryText] = useState<string | null>(null)

  // Auto-select first note when data loads
  useEffect(() => {
    if (notes.length > 0 && !activeNoteId) {
      setActiveNoteId(notes[0].id)
    }
  }, [notes, activeNoteId])

  // Sync local edit state when active note changes
  useEffect(() => {
    const note = notes.find((n) => n.id === activeNoteId)
    if (note) {
      setLocalTitle(note.title ?? '')
      setLocalContent(note.content ?? '')
      setSummaryText(null)
    }
  }, [activeNoteId, notes])

  const activeNote = notes.find((n) => n.id === activeNoteId) ?? null

  // ─── Debounced auto-save ─────────────────────────────────────────────────
  const debouncedTitle = useDebounce(localTitle, 800)
  const debouncedContent = useDebounce(localContent, 800)

  useEffect(() => {
    if (!activeNoteId || !activeNote) return
    const titleChanged = debouncedTitle !== (activeNote.title ?? '')
    const contentChanged = debouncedContent !== (activeNote.content ?? '')
    if (titleChanged || contentChanged) {
      updateNote.mutate({
        id: activeNoteId,
        title: debouncedTitle,
        content: debouncedContent,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedTitle, debouncedContent])

  // ─── Handlers ─────────────────────────────────────────────────────────────
  const handleAddNote = async () => {
    const res = await createNote.mutateAsync({
      title: 'Untitled Note',
      content: '',
    })
    if (res.data) setActiveNoteId(res.data.id)
  }

  const handleDeleteNote = async () => {
    if (!activeNoteId) return
    await deleteNote.mutateAsync(activeNoteId)
    setActiveNoteId(notes.find((n) => n.id !== activeNoteId)?.id ?? null)
  }

  const handleAiSummarize = async () => {
    if (!activeNoteId || summarizeNote.isPending) return
    const res = await summarizeNote.mutateAsync(activeNoteId)
    if (res.data?.summary) setSummaryText(res.data.summary)
  }

  const filteredNotes = notes.filter((n) =>
    (n.title ?? '').toLowerCase().includes(searchVal.toLowerCase()),
  )

  // ─── Loading / error states ───────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
        Loading notes...
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-destructive text-sm">
        <AlertCircle className="w-4 h-4" />
        Failed to load notes.
      </div>
    )
  }

  return (
    <div className="flex-1 flex h-full bg-background animate-fade-in">
      {/* Left panel: Note list */}
      <div className="w-64 border-r border-border bg-card h-full flex flex-col shrink-0">
        <div className="p-4 space-y-3 shrink-0">
          <Button
            onClick={handleAddNote}
            disabled={createNote.isPending}
            className="w-full btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold flex items-center justify-center gap-2 h-9 text-xs active:scale-[0.98] transition-all duration-150"
          >
            {createNote.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Plus className="w-4 h-4" />
            )}
            Add Note
          </Button>

          <div className="relative">
            <Input
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              placeholder="Search notes..."
              startIcon={<Search className="w-3.5 h-3.5 text-muted-foreground" />}
              className="w-full text-xs bg-background border-border text-foreground h-8"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1 py-1">
          {filteredNotes.length === 0 && (
            <p className="text-center text-xs text-muted-foreground py-6 px-3">
              No notes yet. Click Add Note to start.
            </p>
          )}
          {filteredNotes.map((note) => (
            <button
              key={note.id}
              onClick={() => setActiveNoteId(note.id)}
              className={cn(
                'w-full text-left p-3 rounded-xl transition-all border flex flex-col gap-1',
                activeNoteId === note.id
                  ? 'bg-primary/10 border-primary/30 shadow-[0_0_8px_rgba(189,157,255,0.08)]'
                  : 'border-transparent text-muted-foreground hover:bg-accent hover:text-foreground',
              )}
            >
              <span className="text-xs font-semibold text-foreground truncate block">
                {note.title || 'Untitled Note'}
              </span>
              <span className="text-[10px] text-muted-foreground line-clamp-1">
                {(note.content ?? '').replace(/[#*`_-]/g, '').slice(0, 45)}
              </span>
              <span className="text-[9px] text-muted-foreground font-mono mt-1">
                {new Date(note.updated_at).toLocaleDateString()}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Right panel: Editor */}
      {activeNote ? (
        <div className="flex-1 flex flex-col h-full bg-background relative">
          {/* Toolbar */}
          <div className="px-6 py-2 border-b border-border flex items-center justify-between shrink-0 bg-card/70">
            <div className="flex items-center gap-1">
              {[
                { icon: Bold, label: 'Bold' },
                { icon: Italic, label: 'Italic' },
                { icon: Heading1, label: 'Header' },
                { icon: List, label: 'List' },
                { icon: Code, label: 'Code' },
                { icon: LinkIcon, label: 'Link' },
              ].map((btn, idx) => (
                <Button
                  key={idx}
                  variant="ghost"
                  size="icon-sm"
                  className="text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg"
                  title={btn.label}
                >
                  <btn.icon className="w-3.5 h-3.5" />
                </Button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              {updateNote.isPending && (
                <span className="text-[10px] text-muted-foreground font-mono flex items-center gap-1">
                  <Loader2 className="w-2.5 h-2.5 animate-spin" />
                  Saving...
                </span>
              )}
              <Button
                onClick={handleAiSummarize}
                disabled={summarizeNote.isPending}
                className={cn(
                  'btn-glow h-8 text-xs font-semibold flex items-center gap-1.5 active:scale-[0.98] transition-all duration-150',
                  summarizeNote.isPending
                    ? 'bg-surface border border-primary/20 text-primary'
                    : 'bg-primary hover:bg-violet-primary text-primary-foreground',
                )}
              >
                {summarizeNote.isPending ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Brain className="w-3.5 h-3.5" />
                )}
                {summarizeNote.isPending ? 'Summarizing...' : 'AI Summarize'}
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-muted-foreground hover:text-destructive rounded-lg"
                title="Delete note"
                onClick={handleDeleteNote}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>

          {/* Title editor */}
          <div className="px-8 pt-6 pb-2 shrink-0">
            <input
              type="text"
              value={localTitle}
              onChange={(e) => setLocalTitle(e.target.value)}
              className="w-full bg-transparent border-none outline-none font-headline font-bold text-2xl text-foreground focus:ring-0"
              placeholder="Note Title"
            />
          </div>

          {/* Content TextArea */}
          <div className="flex-1 px-8 pb-4 overflow-y-auto">
            <textarea
              value={localContent}
              onChange={(e) => setLocalContent(e.target.value)}
              className="w-full h-full min-h-[200px] bg-transparent border-none outline-none text-sm text-foreground focus:ring-0 resize-none leading-relaxed font-sans"
              placeholder="Start writing... (supports Markdown)"
            />
          </div>

          {/* AI Summary Panel */}
          {summaryText && (
            <div className="mx-8 mb-4 p-4 rounded-xl bg-primary/5 border border-primary/20">
              <div className="flex items-center gap-1.5 mb-2">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                <span className="text-[10px] font-mono font-bold text-primary uppercase tracking-wider">
                  AI Summary
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{summaryText}</p>
            </div>
          )}

          {/* Backlinks Footer Panel */}
          {activeNote.backlinks && activeNote.backlinks.length > 0 && (
            <div className="p-4 border-t border-border bg-card/70 shrink-0 flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
                Related backlinks:
              </span>
              {activeNote.backlinks.map((link, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    const target = notes.find((n) => n.id === link.note_id)
                    if (target) setActiveNoteId(target.id)
                  }}
                  className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-primary hover:bg-primary/25 transition-all duration-150 active:scale-[0.98] flex items-center gap-1"
                >
                  <Sparkles className="w-2.5 h-2.5" />
                  {link.title}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
          {notes.length === 0
            ? 'No notes yet. Click Add Note to get started.'
            : 'Select a note to start editing.'}
        </div>
      )}
    </div>
  )
}
