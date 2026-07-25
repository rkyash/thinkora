import { create } from 'zustand'
import type { ChatMessage } from '@/types/api'

interface ChatState {
  /** Buffer for streaming assistant message chunks */
  streamingContent: string
  isStreaming: boolean
  /** Error message from the SSE stream, if any */
  streamError: string | null

  // Actions
  startStreaming: () => void
  appendChunk: (chunk: string) => void
  stopStreaming: () => ChatMessage | null
  resetStream: () => void
  setStreamError: (error: string) => void
}

export const useChatStore = create<ChatState>()((set, get) => ({
  streamingContent: '',
  isStreaming: false,
  streamError: null,

  startStreaming: () => set({ isStreaming: true, streamingContent: '', streamError: null }),

  appendChunk: (chunk) => set((state) => ({
    streamingContent: state.streamingContent + chunk,
  })),

  stopStreaming: () => {
    const content = get().streamingContent
    set({ isStreaming: false })
    return content ? null : null
  },

  resetStream: () => set({ streamingContent: '', isStreaming: false, streamError: null }),

  setStreamError: (error) => set({ streamError: error, isStreaming: false }),
}))
