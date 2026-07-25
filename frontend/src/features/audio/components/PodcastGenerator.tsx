import React, { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Mic, Loader2, Sparkles, Settings2 } from 'lucide-react'
import { useGenerateAudio, useDeleteAudio } from '@/hooks/useAudio'
import { cn } from '@/lib/utils'

interface PodcastGeneratorProps {
  notebookId: string
  progress: { step: string; pct: number; status: string; detail?: Record<string, unknown> } | null
  isGenerating: boolean
  hasError?: boolean
  errorMessage?: string
}

export function PodcastGenerator({ notebookId, progress, isGenerating, hasError, errorMessage }: PodcastGeneratorProps) {
  const { mutate: generate, isPending } = useGenerateAudio(notebookId)
  const { mutate: cancelAudio } = useDeleteAudio(notebookId)
  const [ttsBackend, setTtsBackend] = useState('gtts')

  const handleGenerate = () => {
    generate({ tts_backend: ttsBackend })
  }

  const showProgress = isGenerating || isPending
  const currentPct = progress?.pct || (isPending ? 5 : 0)
  const stepText = progress?.step ? progress.step.replace(/_/g, ' ') : 'Starting up...'

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto px-6 py-12 text-center space-y-8 animate-in fade-in zoom-in-95 duration-500">
      <div className="w-24 h-24 bg-gradient-to-br from-primary/20 to-tertiary/20 rounded-3xl flex items-center justify-center shadow-inner mb-2 border border-primary/10">
        <Mic className="w-12 h-12 text-primary" />
      </div>
      
      <div className="space-y-3">
        <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
          AI Podcast Studio
        </h2>
        <p className="text-muted-foreground text-lg max-w-lg mx-auto">
          Transform your notes into an engaging, multi-speaker audio conversation. Perfect for listening on the go.
        </p>
      </div>

      {!showProgress ? (
        <div className="w-full max-w-md bg-card rounded-2xl p-6 border border-border shadow-sm mt-8">
          <div className="flex items-center gap-2 mb-4 text-sm font-semibold text-muted-foreground">
            <Settings2 className="w-4 h-4" />
            <span>Audio Settings</span>
          </div>

          {hasError && (
            <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-xl text-left break-words">
              {errorMessage || (typeof progress?.detail?.error_msg === 'string' ? progress.detail.error_msg : null) || 'An error occurred during generation. Please check your AI provider settings and try again.'}
            </div>
          )}
          
          <div className="space-y-4 text-left">
            <div>
              <label className="text-xs font-medium mb-1.5 block">Voice Engine</label>
              <select 
                value={ttsBackend}
                onChange={(e) => setTtsBackend(e.target.value)}
                className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
              >
                <option value="gtts">Standard (gTTS)</option>
                <option value="elevenlabs">Premium (ElevenLabs)</option>
              </select>
            </div>
          </div>
          
          <Button 
            onClick={handleGenerate} 
            disabled={isPending}
            className="w-full mt-6 h-12 rounded-xl text-base shadow-md group active:scale-[0.98] transition-all duration-150"
          >
            <Sparkles className="w-5 h-5 mr-2 text-primary-foreground/80 group-hover:text-primary-foreground transition-colors" />
            Generate Podcast
          </Button>
        </div>
      ) : (
        <div className="w-full max-w-md bg-card rounded-2xl p-8 border border-border mt-8 relative overflow-hidden">
          {/* Subtle pulse background */}
          <div className="absolute inset-0 bg-primary/5 animate-pulse" />
          
          <div className="relative z-10 flex flex-col items-center">
            <Loader2 className="w-10 h-10 animate-spin text-primary mb-6" />
            
            <h3 className="text-lg font-bold mb-2 capitalize">{stepText}</h3>
            <p className="text-sm text-muted-foreground mb-6">
              This usually takes 1-2 minutes depending on notebook length.
            </p>
            
            <div className="w-full h-2.5 bg-secondary rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-500 ease-out"
                style={{ width: `${currentPct}%` }}
              />
            </div>
            <div className="w-full text-right mt-2 text-xs font-medium text-primary mb-6">
              {currentPct}%
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => cancelAudio()}
              className="text-destructive hover:bg-destructive/10 hover:text-destructive border-destructive/20 transition-all duration-150 active:scale-[0.98]"
            >
              Cancel Generation
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
