import React, { useState, useEffect, useRef, useCallback } from 'react'
import { flushSync } from 'react-dom'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { streamAsk, listMessages, createChatSession, listChatSessions, deleteChatSession } from '@/api/chat'
import type { ChatMessage, ChatSession } from '@/types/api'
import { Loader2, Plus, MessageSquare, Trash2, StopCircle, AlertTriangle, RotateCcw, ClipboardCopy } from 'lucide-react'
import { useToast } from '@/components/ui'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

interface ChatLayoutProps {
  notebookId: string
}

const SUGGESTIONS = [
  "What are the major applications mentioned?",
  "Explain the core mechanism in simple terms.",
  "Summarize the key achievements.",
  "Generate a study outline based on all loaded sources.",
]

const isValidUUID = (id: string) =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)

// ─── Follow-up parser ────────────────────────────────────────────────────────

/**
 * Looks for a section like:
 *   ## Follow-up Questions
 *   - How does X work?
 *   - What is Y?
 *
 * OR:
 *   **Suggested Questions:**
 *   - How does X work?
 *
 * Returns up to 4 extracted question strings (empty array if none found).
 */
function parseSuggestedQuestions(content: string): string[] {
  const lines = content.split('\n')
  const questions: string[] = []
  let inSection = false

  for (const raw of lines) {
    const line = raw.trim()
    // Detect section heading
    if (
      /^#{1,3}\s+(follow.?up|suggested\s+questions?)/i.test(line) ||
      /^\*{1,2}(follow.?up|suggested\s+questions?)[:*]{0,2}/i.test(line)
    ) {
      inSection = true
      continue
    }
    if (inSection) {
      // A list item line
      const match = line.match(/^[-*]\s+(.+)$/)
      if (match) {
        const q = match[1].replace(/^\*{1,2}|\*{1,2}$/g, '').trim()
        if (q) questions.push(q)
        if (questions.length >= 4) break
      } else if (line && !/^#{1,6}/.test(line)) {
        // Non-list, non-heading line ends the section
        if (questions.length > 0) break
      }
    }
  }
  return questions
}

/**
 * Maps raw backend error strings to user-friendly messages.
 * Returns an object with a user-facing message and the raw technical detail.
 */
function parseStreamError(raw: string): {
  title: string
  message: string
  suggestions: string[]
  technical: string
  isRecoverable: boolean
} {
  const lower = raw.toLowerCase()

  if (lower.includes('authenticationerror') || lower.includes('api_key')) {
    return {
      title: 'Authentication Failed',
      message: 'The AI provider API key is missing or invalid.',
      suggestions: [
        'Verify that the required API key is configured.',
        'Check your environment variables.',
        'Contact the administrator if the issue persists.',
      ],
      technical: raw,
      isRecoverable: false,
    }
  }

  if (lower.includes('ratelimit') || lower.includes('rate_limit') || lower.includes('429')) {
    return {
      title: 'Rate Limit Exceeded',
      message: 'Too many requests. Please wait a moment and try again.',
      suggestions: [
        'Wait a few seconds before retrying.',
        'Reduce the frequency of your requests.',
      ],
      technical: raw,
      isRecoverable: true,
    }
  }

  if (lower.includes('timeout') || lower.includes('timed out')) {
    return {
      title: 'Request Timed Out',
      message: 'The AI provider took too long to respond.',
      suggestions: [
        'Try again — this is usually temporary.',
        'Try a shorter or simpler question.',
      ],
      technical: raw,
      isRecoverable: true,
    }
  }

  if (lower.includes('connection') || lower.includes('network') || lower.includes('econnrefused')) {
    return {
      title: 'Connection Error',
      message: 'Could not connect to the AI service.',
      suggestions: [
        'Check your internet connection.',
        'The AI service may be temporarily unavailable.',
        'Try again in a few moments.',
      ],
      technical: raw,
      isRecoverable: true,
    }
  }

  if (lower.includes('context') && (lower.includes('length') || lower.includes('window') || lower.includes('too long'))) {
    return {
      title: 'Context Too Long',
      message: 'The conversation or source material exceeds the AI model\'s context limit.',
      suggestions: [
        'Try a shorter question.',
        'Start a new chat session.',
        'Reduce the number of sources in your notebook.',
      ],
      technical: raw,
      isRecoverable: true,
    }
  }

  if (lower.includes('model') && (lower.includes('not found') || lower.includes('does not exist'))) {
    return {
      title: 'Model Not Available',
      message: 'The configured AI model could not be found.',
      suggestions: [
        'Check the model name in your settings.',
        'The model may have been deprecated or renamed.',
        'Contact the administrator to update the configuration.',
      ],
      technical: raw,
      isRecoverable: false,
    }
  }

  // Default
  return {
    title: 'Unable to Generate Response',
    message: 'An unexpected error occurred while processing your request.',
    suggestions: [
      'Try again — this may be a temporary issue.',
      'If the problem persists, contact the administrator.',
    ],
    technical: raw,
    isRecoverable: true,
  }
}

export function ChatLayout({ notebookId }: ChatLayoutProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingCitations, setStreamingCitations] = useState<any[]>([])
  const [showSessions, setShowSessions] = useState(false)
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([])
  const [streamError, setStreamError] = useState<ReturnType<typeof parseStreamError> | null>(null)
  // ─── Edit message state ────────────────────────────────────────────────────
  const [editingMessage, setEditingMessage] = useState<{ id: string; content: string } | null>(null)

  // Fix #3 — store EventSource cleanup so we can cancel on unmount or Stop click
  const streamCleanupRef = useRef<(() => void) | null>(null)
  // Track streaming content in a ref so onDone closure always has the latest value
  const streamingContentRef = useRef('')

  const { toast } = useToast()

  // Cancel any ongoing stream on unmount
  useEffect(() => {
    return () => {
      streamCleanupRef.current?.()
    }
  }, [])

  const loadSession = useCallback(async (session: ChatSession) => {
    setActiveSession(session)
    setMessages([])
    try {
      // Load up to 100 messages (pagination handled server-side)
      const msgsRes = await listMessages(session.id)
      setMessages(msgsRes.data)
    } catch {
      toast('Failed to load messages', 'error')
    }
  }, [toast])

  useEffect(() => {
    async function init() {
      if (!isValidUUID(notebookId)) {
        setIsLoading(false)
        return
      }
      setIsLoading(true)
      try {
        const sessionsRes = await listChatSessions(notebookId)
        if (sessionsRes.data.length > 0) {
          setSessions(sessionsRes.data)
          await loadSession(sessionsRes.data[0])
        } else {
          const newSessionRes = await createChatSession(notebookId, 'Study Session')
          setSessions([newSessionRes.data])
          setActiveSession(newSessionRes.data)
          setMessages([])
        }
      } catch {
        toast('Failed to load chat session', 'error')
      } finally {
        setIsLoading(false)
      }
    }
    if (notebookId) init()
  }, [notebookId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleNewSession = async () => {
    try {
      const res = await createChatSession(notebookId, 'New Chat')
      setSessions(prev => [res.data, ...prev])
      await loadSession(res.data)
      setShowSessions(false)
    } catch {
      toast('Failed to create session', 'error')
    }
  }

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await deleteChatSession(sessionId)
      const remaining = sessions.filter(s => s.id !== sessionId)
      setSessions(remaining)
      if (activeSession?.id === sessionId) {
        if (remaining.length > 0) {
          await loadSession(remaining[0])
        } else {
          setActiveSession(null)
          setMessages([])
        }
      }
    } catch {
      toast('Failed to delete session', 'error')
    }
  }

  // Fix #6 — stop the stream
  const handleStop = () => {
    streamCleanupRef.current?.()
    streamCleanupRef.current = null
    const stoppedContent = streamingContentRef.current
    streamingContentRef.current = ''
    setIsStreaming(false)
    if (stoppedContent.trim() && activeSession) {
      const stoppedMsg: ChatMessage = {
        id: Date.now().toString(),
        session_id: activeSession.id,
        role: 'assistant',
        content: stoppedContent + ' *(stopped)*',
        created_at: new Date().toISOString(),
        sources: [],
      }
      setMessages(prev => [...prev, stoppedMsg])
      setStreamingContent('')
      setStreamingCitations([])
    }
  }

  // ─── Core send logic (used by both handleSend and handleRegenerate) ────────────────
  const handleSendCore = useCallback((text: string) => {
    if (!activeSession || isStreaming) return

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: activeSession.id,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
      sources: [],
    }
    setMessages(prev => [...prev, tempUserMsg])
    setIsStreaming(true)
    setStreamingContent('')
    setStreamingCitations([])

    // Fix #3 — store cleanup ref
    streamCleanupRef.current = streamAsk(activeSession.id, text, {
      onChunk: (chunk) => {
        streamingContentRef.current += chunk
        setStreamingContent(prev => prev + chunk)
      },
      onCitations: (citations) => {
        setStreamingCitations(citations)
      },
      onStreamError: (errorMessage) => {
        // Parse the error into a user-friendly format
        const parsedError = parseStreamError(errorMessage)
        console.error('SSE stream error:', errorMessage)

        // Preserve any partial content that was streamed before the error
        const partialContent = streamingContentRef.current
        streamCleanupRef.current = null
        streamingContentRef.current = ''

        flushSync(() => {
          // If there was partial content, add it as an incomplete assistant message
          if (partialContent.trim()) {
            const partialMsg: ChatMessage = {
              id: `partial-${Date.now()}`,
              session_id: activeSession.id,
              role: 'assistant',
              content: partialContent + '\n\n*(Response interrupted due to an error)*',
              created_at: new Date().toISOString(),
              sources: [],
            }
            setMessages(prev => [...prev, partialMsg])
          }

          setIsStreaming(false)
          setStreamingContent('')
          setStreamingCitations([])
          setStreamError(parsedError)
        })
      },
      onDone: () => {
        const finalContent = streamingContentRef.current
        streamCleanupRef.current = null
        streamingContentRef.current = ''
        const followUps = parseSuggestedQuestions(finalContent)
        flushSync(() => {
          setMessages(prev => {
            const assistantMsg: ChatMessage = {
              id: `assistant-${Date.now()}`,
              session_id: activeSession.id,
              role: 'assistant',
              content: finalContent,
              created_at: new Date().toISOString(),
              sources: [],
            }
            return [...prev, assistantMsg]
          })
          setIsStreaming(false)
          setStreamingContent('')
          setStreamingCitations([])
          setSuggestedQuestions(followUps)
          setStreamError(null)
        })
      },
      onError: (err) => {
        console.error('SSE connection error:', err)
        const partialContent = streamingContentRef.current
        streamCleanupRef.current = null
        streamingContentRef.current = ''

        flushSync(() => {
          if (partialContent.trim()) {
            const partialMsg: ChatMessage = {
              id: `partial-${Date.now()}`,
              session_id: activeSession.id,
              role: 'assistant',
              content: partialContent + '\n\n*(Response interrupted — connection lost)*',
              created_at: new Date().toISOString(),
              sources: [],
            }
            setMessages(prev => [...prev, partialMsg])
          }

          setIsStreaming(false)
          setStreamingContent('')
          setStreamingCitations([])
          setStreamError(parseStreamError(err.message || 'Connection to server lost'))
        })
      },
    })
  }, [activeSession, isStreaming]) // eslint-disable-line react-hooks/exhaustive-deps

  // ─── Regenerate last response ───────────────────────────────────────────────
  const handleRegenerate = useCallback(() => {
    if (!activeSession || isStreaming) return
    // Find the last user message to re-send
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
    if (!lastUserMsg) return
    // Remove the last assistant message and re-trigger
    setMessages(prev => {
      const lastAssistantIdx = [...prev].map((m, i) => ({ m, i })).reverse().find(({ m }) => m.role === 'assistant')?.i
      if (lastAssistantIdx !== undefined) return prev.slice(0, lastAssistantIdx)
      return prev
    })
    setSuggestedQuestions([])
    setStreamError(null)
    handleSendCore(lastUserMsg.content)
  }, [activeSession, isStreaming, messages, handleSendCore])

  const handleSend = (text: string) => {
    setSuggestedQuestions([])
    setStreamError(null)
    handleSendCore(text)
  }

  const handleRetry = useCallback(() => {
    if (!activeSession || isStreaming) return
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
    if (!lastUserMsg) return
    setStreamError(null)
    handleSendCore(lastUserMsg.content)
  }, [activeSession, isStreaming, messages, handleSendCore])

  // ─── Edit message handlers ──────────────────────────────────────────────────
  /** Called when user clicks "Edit" on a user message bubble */
  const handleEdit = useCallback((msgId: string, content: string) => {
    setEditingMessage({ id: msgId, content })
  }, [])

  /** Called when user submits the edited text in ChatInput */
  const handleEditSend = useCallback((newText: string) => {
    if (!editingMessage) return
    // Remove the edited message and everything after it from local state
    setMessages(prev => {
      const idx = prev.findIndex(m => m.id === editingMessage.id)
      return idx >= 0 ? prev.slice(0, idx) : prev
    })
    setSuggestedQuestions([])
    setEditingMessage(null)
    // Re-send with the new text
    handleSendCore(newText)
  }, [editingMessage, handleSendCore])

  const handleCancelEdit = useCallback(() => {
    setEditingMessage(null)
  }, [])

  // (handleSendCore and its streaming body are now above handleRegenerate)

  if (!isValidUUID(notebookId)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-background text-muted-foreground p-6 text-center">
        <div className="w-12 h-12 bg-card rounded-xl border border-border flex items-center justify-center mb-4">
          <Loader2 className="w-6 h-6 text-muted-foreground" />
        </div>
        <h3 className="text-foreground font-medium mb-2">Demo Notebook</h3>
        <p className="text-sm max-w-sm">
          Chat features are disabled for demo notebooks. Please create a real notebook to chat with your documents.
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-background">
        <Loader2 className="w-6 h-6 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-background relative overflow-hidden">
      {/* ── Session bar ── */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border shrink-0 bg-card/70 backdrop-blur-sm">
        <button
          onClick={() => setShowSessions(v => !v)}
          className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span className="truncate max-w-[160px] font-medium">{activeSession?.title ?? 'Chat'}</span>
        </button>
        <button
          onClick={handleNewSession}
          className="ml-auto flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
          title="New chat session"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Fix #9 — Session switcher dropdown */}
      {showSessions && sessions.length > 0 && (
        <div className="absolute top-10 left-0 z-20 w-64 bg-card border border-border rounded-xl shadow-xl overflow-hidden">
          <div className="p-2 max-h-64 overflow-y-auto space-y-1">
            {sessions.map(s => (
              <div
                key={s.id}
                onClick={async () => { await loadSession(s); setShowSessions(false) }}
                onKeyDown={async (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); await loadSession(s); setShowSessions(false) } }}
                role="button"
                tabIndex={0}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm group transition-colors active:scale-[0.98]',
                  s.id === activeSession?.id
                    ? 'bg-primary/10 text-primary'
                    : 'hover:bg-accent text-foreground',
                )}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                <span className="flex-1 truncate">{s.title ?? 'Untitled'}</span>
                <button
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-400 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <MessageList
        messages={messages}
        isStreaming={isStreaming}
        streamingContent={streamingContent}
        streamingCitations={streamingCitations}
        suggestedQuestions={suggestedQuestions}
        onQuestionClick={handleSend}
        onRegenerate={handleRegenerate}
        onEdit={(content) => {
          const msg = messages.find(m => m.role === 'user' && m.content === content)
          if (msg) handleEdit(msg.id, content)
        }}
      />

      {/* ── Error Card ── */}
      {streamError && (
        <div className="mx-4 sm:mx-8 mb-4 animate-fade-in">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-start mr-auto max-w-[90%] w-full">
              {/* Error Avatar */}
              <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold shadow-sm mt-0.5 bg-red-500/10 text-red-500 border border-red-500/20">
                <AlertTriangle className="w-4 h-4" />
              </div>

              {/* Error Content */}
              <div className="flex flex-col gap-2 items-start w-full">
                <div className="relative text-foreground shadow-sm bg-card border border-red-500/20 rounded-2xl rounded-tl-sm px-5 py-4 w-full backdrop-blur-sm">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-red-500 font-semibold text-sm">⚠️ {streamError.title}</span>
                  </div>

                  {/* Message */}
                  <div className="mb-3">
                    <p className="text-sm text-foreground/80 mb-2">{streamError.message}</p>
                    <p className="text-[12px] text-red-400/90 font-mono bg-red-500/5 p-2.5 rounded-lg border border-red-500/10 break-all whitespace-pre-wrap">
                      {streamError.technical}
                    </p>
                  </div>

                  {/* Suggestions */}
                  {streamError.suggestions.length > 0 && (
                    <div className="mb-2">
                      <p className="text-xs font-medium text-muted-foreground mb-1.5">Suggested actions:</p>
                      <ul className="space-y-1">
                        {streamError.suggestions.map((s, i) => (
                          <li key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                            <span className="text-primary mt-0.5">•</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-2 ml-1">
                  {streamError.isRecoverable && (
                    <button
                      onClick={handleRetry}
                      className="flex items-center gap-1.5 text-[11px] font-medium text-primary hover:text-primary/80 bg-primary/10 hover:bg-primary/15 border border-primary/20 rounded-full px-3 py-1.5 transition-all active:scale-[0.98]"
                    >
                      <RotateCcw className="w-3 h-3" />
                      Retry
                    </button>
                  )}
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(streamError.technical)
                      toast('Error details copied to clipboard', 'success')
                    }}
                    className="flex items-center gap-1.5 text-[11px] text-muted-foreground hover:text-foreground border border-border rounded-full px-3 py-1.5 transition-all active:scale-[0.98]"
                  >
                    <ClipboardCopy className="w-3 h-3" />
                    Copy Error
                  </button>
                  <button
                    onClick={() => setStreamError(null)}
                    className="text-[11px] text-muted-foreground hover:text-foreground transition-colors px-2 py-1.5"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Suggested prompts on empty state */}
      {messages.length === 0 && !isStreaming && (
        <div className="px-6 pb-4 grid grid-cols-1 md:grid-cols-2 gap-3 max-w-4xl mx-auto w-full z-10">
          {SUGGESTIONS.map((s, idx) => (
            <div
              key={idx}
              onClick={() => handleSend(s)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleSend(s) } }}
              role="button"
              tabIndex={0}
              className="glass-panel p-3.5 rounded-xl text-xs bg-background border border-border hover:border-primary/30 hover:bg-accent cursor-pointer transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.98] text-foreground text-center font-medium"
            >
              {s}
            </div>
          ))}
        </div>
      )}

      {/* Fix #6 — Stop button during streaming */}
      {isStreaming && (
        <div className="flex justify-center pb-2 z-10">
          <button
            onClick={handleStop}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground border border-border rounded-full px-3 py-1.5 bg-card hover:bg-accent backdrop-blur-sm transition-all duration-150 active:scale-[0.98]"
          >
            <StopCircle className="w-3.5 h-3.5" />
            Stop generating
          </button>
        </div>
      )}

      <ChatInput
        onSend={editingMessage ? handleEditSend : handleSend}
        disabled={isStreaming}
        editValue={editingMessage?.content}
        onCancelEdit={handleCancelEdit}
      />
    </div>
  )
}
