import { apiClient } from '@/lib/axios'
import type { ApiResponse, Generation, AudioGenerateRequest, AudioStatusResponse } from '@/types/api'

/** Trigger podcast generation */
export async function generateAudio(
  notebookId: string,
  payload: AudioGenerateRequest
): Promise<ApiResponse<Generation>> {
  const res = await apiClient.post<ApiResponse<Generation>>(
    `/api/v1/notebooks/${notebookId}/audio`,
    payload
  )
  return res.data
}

/** Check status of podcast generation */
export async function getAudioStatus(
  notebookId: string
): Promise<ApiResponse<AudioStatusResponse>> {
  const res = await apiClient.get<ApiResponse<AudioStatusResponse>>(
    `/api/v1/notebooks/${notebookId}/audio/status`
  )
  return res.data
}

/** Delete podcast generation and audio file */
export async function deleteAudio(notebookId: string): Promise<void> {
  await apiClient.delete(`/api/v1/notebooks/${notebookId}/audio`)
}

/**
 * Open SSE stream for podcast generation progress
 */
export function streamAudioProgress(
  generationId: string,
  options: {
    onMessage: (data: any) => void
    onError: (err: Error) => void
    onDone: () => void
  }
): () => void {
  const url = new URL(
    `/api/v1/events/${generationId}`,
    import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
  )
  const token = localStorage.getItem('access_token')
  const eventSource = new EventSource(
    url.toString() + (token ? `?token=${encodeURIComponent(token)}` : '')
  )

  eventSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      options.onMessage(data)
      if (data.status === 'ready' || data.status === 'error') {
        eventSource.close()
        options.onDone()
      }
    } catch (err) {
      console.error('Failed to parse SSE', err)
    }
  }

  eventSource.onerror = () => {
    eventSource.close()
    options.onError(new Error('SSE stream error'))
  }

  return () => eventSource.close()
}
