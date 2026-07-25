import React, { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  MessageSquare,
  FileText,
  Layers,
  HelpCircle,
  Network,
  Mic,
  Loader2,
} from 'lucide-react'
import { Layout } from '@/components/layout/Layout'
import { useNotebookStore } from '@/store/notebookStore'
import { useNotebook } from '@/hooks/useNotebooks'
import { cn } from '@/lib/utils'

// Import notebook panel & tab components
import { SourcesPanel } from '@/components/notebook/SourcesPanel'
import { ChatTab } from '@/components/notebook/ChatTab'
import { NotesTab } from '@/components/notebook/NotesTab'
import { FlashcardsTab } from '@/components/notebook/FlashcardsTab'
import { QuizTab } from '@/components/notebook/QuizTab'
import { GraphTab } from '@/components/notebook/GraphTab'
import { AudioTab } from '@/components/notebook/AudioTab'

export function Notebook() {
  const { id } = useParams<{ id: string }>()
  
  const { activeTab, setActiveTab, setActiveNotebook } = useNotebookStore()
  
  // Fetch actual notebook data if database has it
  const { data: notebook, isLoading } = useNotebook(id || '')

  useEffect(() => {
    if (id) {
      setActiveNotebook(id)
    }
    return () => {
      setActiveNotebook(null)
    }
  }, [id, setActiveNotebook])

  // Realistic mock data fallback if notebook is not in DB (e.g. demo)
  const mockNotebooks: Record<string, { name: string; emoji: string }> = {
    'demo-1': { name: 'ML Research', emoji: '📚' },
    'demo-2': { name: 'Biology Notes', emoji: '🧬' },
    'demo-3': { name: 'System Design', emoji: '💻' },
    'demo-4': { name: 'Product Strategy', emoji: '🎯' },
    'demo-5': { name: 'Data Analysis', emoji: '📊' },
    'demo-6': { name: 'Physics 101', emoji: '🔬' },
  }

  const notebookDetails = notebook || (id && mockNotebooks[id]) || {
    name: 'Study Notebook',
    emoji: '📓',
  }

  // Render correct tab view component
  const renderTabContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatTab notebookId={id || ''} />
      case 'notes':
        return <NotesTab />
      case 'flashcards':
        return <FlashcardsTab />
      case 'quiz':
        return <QuizTab />
      case 'graph':
        return <GraphTab />
      case 'audio':
        return <AudioTab />
      default:
        return <ChatTab notebookId={id || ''} />
    }
  }

  const tabs = [
    { id: 'chat', label: 'AI Chat', icon: MessageSquare },
    { id: 'notes', label: 'Notes', icon: FileText },
    { id: 'flashcards', label: 'Flashcards', icon: Layers },
    { id: 'quiz', label: 'Quiz', icon: HelpCircle },
    { id: 'graph', label: 'Graph', icon: Network },
    { id: 'audio', label: 'Audio Summary', icon: Mic },
  ] as const

  if (isLoading) {
    return (
      <Layout title="Notebook" showSearch>
        <div className="flex items-center justify-center h-full min-h-[60vh] text-muted-foreground text-sm gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
          <span>Loading study workspace...</span>
        </div>
      </Layout>
    )
  }

  return (
    <Layout
      title={`${notebookDetails.emoji} ${notebookDetails.name}`}
      showSearch={false}
      className="p-0 overflow-hidden"
    >
      <div className="flex h-[calc(100vh-56px)] overflow-hidden bg-background">
        {/* Left column sources sidebar panel */}
        <SourcesPanel />

        {/* Right column main content area with tabs & views */}
        <div className="flex-1 flex flex-col h-full overflow-hidden bg-background">
          {/* Tab bar header */}
          <div className="flex px-4 border-b border-border bg-card/70 shrink-0 select-none overflow-x-auto scrollbar-none">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all duration-200 whitespace-nowrap",
                    isActive
                      ? "tab-active border-primary text-foreground"
                      : "tab-inactive border-transparent text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon className={cn("w-4 h-4", isActive ? "text-primary" : "text-muted-foreground")} />
                  {tab.label}
                </button>
              )
            })}
          </div>

          {/* Active Tab viewport panel */}
          <div className="flex-1 overflow-hidden flex flex-col">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </Layout>
  )
}
