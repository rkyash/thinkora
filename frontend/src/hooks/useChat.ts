import { useCallback, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as chatApi from '@/api/chat'
import { chatKeys } from '@/utils/queryKeys'
import { useChatStore } from '@/store/chatStore'

/** List all chat sessions for a notebook */
export function useChatSessions(notebookId: string) {
  return useQuery({
    queryKey: chatKeys.sessions(notebookId),
    queryFn: () => chatApi.listChatSessions(notebookId),
    select: (data) => data.data,
    enabled: Boolean(notebookId),
  })
}

/** List messages in a session */
export function useMessages(sessionId: string) {
  return useQuery({
    queryKey: chatKeys.messages(sessionId),
    queryFn: () => chatApi.listMessages(sessionId),
    select: (data) => data.data,
    enabled: Boolean(sessionId),
  })
}

/** Create a new chat session */
export function useCreateChatSession(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (title?: string) => chatApi.createChatSession(notebookId, title),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.sessions(notebookId) })
    },
  })
}

/**
 * useStreamAsk — sends a question and streams the response via SSE.
 *
 * Returns:
 * - `ask(question)` — initiates the stream
 * - `cancel()` — aborts an in-flight stream
 * - `isStreaming` from the chat store
 * - `streamingContent` the current buffer
 */
export function useStreamAsk(sessionId: string) {
  const queryClient = useQueryClient()
  const cleanupRef = useRef<(() => void) | null>(null)
  const { startStreaming, appendChunk, stopStreaming, resetStream, isStreaming, streamingContent } =
    useChatStore()

  const ask = useCallback(
    (question: string) => {
      if (isStreaming) return
      startStreaming()

      const cleanup = chatApi.streamAsk(sessionId, question, {
        onChunk: appendChunk,
        onDone: () => {
          stopStreaming()
          // Refetch messages to include the persisted assistant reply
          void queryClient.invalidateQueries({ queryKey: chatKeys.messages(sessionId) })
          cleanupRef.current = null
        },
        onError: (err) => {
          console.error('SSE error:', err)
          resetStream()
          cleanupRef.current = null
        },
      })

      cleanupRef.current = cleanup
    },
    [sessionId, isStreaming, startStreaming, appendChunk, stopStreaming, resetStream, queryClient],
  )

  const cancel = useCallback(() => {
    cleanupRef.current?.()
    cleanupRef.current = null
    resetStream()
  }, [resetStream])

  return { ask, cancel, isStreaming, streamingContent }
}

/** Delete a chat session */
export function useDeleteChatSession(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => chatApi.deleteChatSession(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chatKeys.sessions(notebookId) })
    },
  })
}
