import { apiClient } from '@/lib/axios'
import type {
  ApiResponse,
  PaginatedResponse,
  ChatSession,
  ChatMessage,
} from '@/types/api'

/** GET /api/v1/notebooks/:notebookId/chat/sessions */
export async function listChatSessions(
  notebookId: string,
): Promise<PaginatedResponse<ChatSession>> {
  const res = await apiClient.get<PaginatedResponse<ChatSession>>(
    `/api/v1/notebooks/${notebookId}/chat/sessions`,
  )
  return res.data
}

/** POST /api/v1/notebooks/:notebookId/chat/sessions */
export async function createChatSession(
  notebookId: string,
  title?: string,
): Promise<ApiResponse<ChatSession>> {
  const res = await apiClient.post<ApiResponse<ChatSession>>(
    `/api/v1/notebooks/${notebookId}/chat/sessions`,
    { title },
  )
  return res.data
}

/** GET /api/v1/chat/sessions/:sessionId/messages */
export async function listMessages(
  sessionId: string,
  limit = 200,
): Promise<PaginatedResponse<ChatMessage>> {
  const res = await apiClient.get<PaginatedResponse<ChatMessage>>(
    `/api/v1/chat/sessions/${sessionId}/messages`,
    { params: { limit } },
  )
  return res.data
}

/**
 * POST /api/v1/chat/sessions/:sessionId/ask  (SSE streaming)
 *
 * Opens an EventSource and calls onChunk for each streamed token,
 * onCitations when the final citations object arrives, and onDone on completion.
 */
export function streamAsk(
  sessionId: string,
  question: string,
  options: {
    onChunk: (text: string) => void
    onCitations?: (citations: any[]) => void
    onStreamError?: (errorMessage: string) => void
    onDone: () => void
    onError: (err: Error) => void
  },
): () => void {
  const url = new URL(
    `/api/v1/chat/sessions/${sessionId}/ask`,
    import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  )
  url.searchParams.set('question', question)

  const token = localStorage.getItem('access_token')
  const eventSource = new EventSource(
    url.toString() + (token ? `&token=${encodeURIComponent(token)}` : ''),
  )

  eventSource.addEventListener('chunk', (e) => {
    // Backend JSON-encodes chunks to preserve newlines through SSE protocol.
    // Parse to recover the original text with markdown formatting intact.
    try {
      options.onChunk(JSON.parse(e.data))
    } catch {
      // Fallback: use raw data if JSON parsing fails
      options.onChunk(e.data)
    }
  })

  eventSource.addEventListener('citations', (e) => {
    if (options.onCitations) {
      try {
        options.onCitations(JSON.parse(e.data))
      } catch (err) {
        console.error('Failed to parse citations', err)
      }
    }
  })

  eventSource.addEventListener('error', (e: Event) => {
    // Backend emits `event: error` with JSON-encoded error string (MessageEvent).
    // Native EventSource also fires 'error' (Event without data) for connection drops.
    if ('data' in e && e.data !== undefined) {
      if (options.onStreamError) {
        try {
          const errorData = JSON.parse((e as MessageEvent).data)
          options.onStreamError(typeof errorData === 'string' ? errorData : JSON.stringify(errorData))
        } catch {
          options.onStreamError((e as MessageEvent).data || 'Unknown error occurred')
        }
      }
      eventSource.close()
    } else {
      // Connection error
      eventSource.close()
      options.onError(new Error('SSE stream error'))
    }
  })

  eventSource.addEventListener('done', () => {
    eventSource.close()
    options.onDone()
  })

  // Return cleanup function
  return () => eventSource.close()
}

/** DELETE /api/v1/chat/sessions/:sessionId */
export async function deleteChatSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`)
}
