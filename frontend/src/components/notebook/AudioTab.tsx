import React from 'react'
import { useParams } from 'react-router-dom'
import { useAudioStatus, useDeleteAudio, useAudioProgress } from '@/hooks/useAudio'
import { PodcastGenerator } from '@/features/audio/components/PodcastGenerator'
import { PodcastPlayer } from '@/features/audio/components/PodcastPlayer'
import { Loader2 } from 'lucide-react'

export function AudioTab() {
  const { id } = useParams<{ id: string }>()
  const notebookId = id || ''
  
  const { data: statusResp, isLoading } = useAudioStatus(notebookId)
  const { mutate: deleteAudio } = useDeleteAudio(notebookId)
  
  // Track SSE progress if a generation is in pending/processing state
  const generationId = statusResp?.generation?.id
  const isProcessing = statusResp?.generation?.status === 'pending' || statusResp?.generation?.status === 'processing'
  const hasError = statusResp?.generation?.status === 'error'
  const errorMessage = (statusResp?.generation?.content as Record<string, unknown> | undefined)?.error_msg as string | undefined
  
  // Only subscribe to SSE if we have a valid generation ID and it's not completed
  const shouldStream = isProcessing && generationId ? generationId : null
  const { progress } = useAudioProgress(notebookId, shouldStream)
  
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }
  
  // Completed and has audio URL -> Show Player
  if (statusResp?.generation?.status === 'ready' && statusResp.audio_url) {
    return (
      <div className="flex-1 p-6 overflow-y-auto">
        <PodcastPlayer 
          audioUrl={statusResp.audio_url} 
          onDelete={() => deleteAudio()} 
        />
      </div>
    )
  }
  
  // Otherwise -> Show Generator (with progress state if currently running)
  return (
    <div className="flex-1 overflow-y-auto">
      <PodcastGenerator 
        notebookId={notebookId}
        progress={progress}
        isGenerating={isProcessing}
        hasError={hasError}
        errorMessage={errorMessage}
      />
    </div>
  )
}
