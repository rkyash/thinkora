import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as audioApi from '@/api/audio'
import { audioKeys } from '@/utils/queryKeys'
import type { AudioGenerateRequest } from '@/types/api'

/** Poll or get status of podcast generation */
export function useAudioStatus(notebookId: string) {
  return useQuery({
    queryKey: audioKeys.status(notebookId),
    queryFn: () => audioApi.getAudioStatus(notebookId),
    select: (data) => data.data,
    enabled: Boolean(notebookId),
    retry: false, // Do not retry if 404 (no generation exists)
  })
}

/** Trigger podcast generation */
export function useGenerateAudio(notebookId: string) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (payload: AudioGenerateRequest) => audioApi.generateAudio(notebookId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: audioKeys.status(notebookId) })
    },
  })
}

/** Delete podcast */
export function useDeleteAudio(notebookId: string) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => audioApi.deleteAudio(notebookId),
    onSuccess: () => {
      // Remove query data to reset UI
      queryClient.removeQueries({ queryKey: audioKeys.status(notebookId) })
    },
  })
}

/** 
 * Custom hook to subscribe to SSE progress of a running generation.
 * Yields progress { step, pct, status } and error states.
 */
export function useAudioProgress(notebookId: string, generationId?: string | null) {
  const [progress, setProgress] = useState<{ step: string; pct: number; status: string; detail?: Record<string, unknown> } | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!generationId) {
      setProgress(null)
      setError(null)
      return
    }

    const cleanup = audioApi.streamAudioProgress(generationId, {
      onMessage: (data) => {
        setProgress({ step: data.step, pct: data.pct, status: data.status, detail: data.detail })
        
        // If terminal state reached, invalidate status query to fetch final audio URL
        if (data.status === 'ready' || data.status === 'error') {
          // Add a small delay to ensure backend transaction committed
          setTimeout(() => {
            void queryClient.invalidateQueries({ queryKey: audioKeys.status(notebookId) })
          }, 500)
        }
      },
      onError: (err) => {
        setError(err)
      },
      onDone: () => {
        // SSE closed normally
      }
    })

    return cleanup
  }, [generationId, queryClient])

  return { progress, error }
}
