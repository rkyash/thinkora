import React, { useEffect, useRef, memo } from 'react'
import { MessageItem } from './MessageItem'
import type { ChatMessage } from '@/types/api'

interface MessageListProps {
  messages: ChatMessage[]
  streamingContent?: string
  streamingCitations?: any[]
  isStreaming?: boolean
  suggestedQuestions?: string[]
  onQuestionClick?: (question: string) => void
  onRegenerate?: () => void
  onEdit?: (content: string) => void
}

interface HistoricalMessageProps {
  msg: ChatMessage
  isLastAssistant?: boolean
  suggestedQuestions?: string[]
  onQuestionClick?: (question: string) => void
  onRegenerate?: () => void
  onEdit?: (content: string) => void
}

// Memoize each historical message so it doesn't re-render during streaming.
// The last assistant message additionally receives follow-up chips and quick-action props.
const HistoricalMessage = memo(function HistoricalMessage({
  msg,
  isLastAssistant,
  suggestedQuestions,
  onQuestionClick,
  onRegenerate,
  onEdit,
}: HistoricalMessageProps) {
  return (
    <MessageItem
      message={msg}
      suggestedQuestions={isLastAssistant ? suggestedQuestions : undefined}
      onQuestionClick={isLastAssistant ? onQuestionClick : undefined}
      onRegenerate={isLastAssistant ? onRegenerate : undefined}
      onEdit={msg.role === 'user' ? onEdit : undefined}
    />
  )
})

export function MessageList({
  messages,
  streamingContent,
  streamingCitations,
  isStreaming,
  suggestedQuestions,
  onQuestionClick,
  onRegenerate,
  onEdit,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  // Find the index of the last assistant message (for follow-up chips / regenerate)
  const lastAssistantIdx = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant') return i
    }
    return -1
  })()

  // Auto-scroll: only scroll if already near the bottom
  useEffect(() => {
    const list = listRef.current
    if (!list) return
    const threshold = 120 // px from bottom
    const isNearBottom = list.scrollHeight - list.scrollTop - list.clientHeight < threshold
    if (isNearBottom || isStreaming) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [messages.length, streamingContent, isStreaming])

  return (
    <div
      ref={listRef}
      className="flex-1 overflow-y-auto px-4 sm:px-8 py-6 space-y-5 scroll-smooth"
    >
      {messages.map((msg, idx) => (
        <HistoricalMessage
          key={msg.id}
          msg={msg}
          isLastAssistant={!isStreaming && idx === lastAssistantIdx}
          suggestedQuestions={suggestedQuestions}
          onQuestionClick={onQuestionClick}
          onRegenerate={onRegenerate}
          onEdit={onEdit}
        />
      ))}

      {/* Live streaming bubble */}
      {isStreaming && (
        <MessageItem
          message={{
            id: '__streaming__',
            session_id: '',
            role: 'assistant',
            content: streamingContent || '',
            created_at: new Date().toISOString(),
            sources: [],
          }}
          isStreaming
          citations={streamingCitations}
        />
      )}

      <div ref={bottomRef} className="h-2" />
    </div>
  )
}
