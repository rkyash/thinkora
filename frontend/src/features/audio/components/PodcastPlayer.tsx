import React, { useRef, useState, useEffect } from 'react'
import { Play, Pause, SkipBack, SkipForward, Headphones, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'

interface PodcastPlayerProps {
  audioUrl: string
  onDelete: () => void
}

export function PodcastPlayer({ audioUrl, onDelete }: PodcastPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)

  // Sync token to audio URL since backend stream endpoint requires auth.
  // We can just append the token as a query parameter or use the browser's cookies.
  // Actually our API uses the Bearer token header, but audio src can't send headers.
  // So we pass ?token=... just like we did for SSE.
  const token = localStorage.getItem('access_token')
  const srcWithAuth = audioUrl + (token ? `?token=${encodeURIComponent(token)}` : '')

  const togglePlay = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        void audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) setCurrentTime(audioRef.current.currentTime)
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) setDuration(audioRef.current.duration)
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = Number(e.target.value)
    if (audioRef.current) audioRef.current.currentTime = time
    setCurrentTime(time)
  }

  const formatTime = (secs: number) => {
    if (isNaN(secs)) return '0:00'
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-card rounded-2xl shadow-sm border border-border max-w-2xl mx-auto mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mb-6 relative overflow-hidden group">
        <div className={cn("absolute inset-0 bg-primary/20 transition-transform duration-1000", isPlaying ? "scale-150 opacity-0 animate-ping" : "scale-100 opacity-0")} />
        <Headphones className="w-10 h-10 text-primary relative z-10" />
      </div>
      
      <h3 className="text-xl font-bold mb-2">Notebook Podcast</h3>
      <p className="text-muted-foreground text-sm mb-8 text-center max-w-sm">
        Listen to an AI-generated conversation explaining the core concepts of this notebook.
      </p>

      <audio
        ref={audioRef}
        src={srcWithAuth}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
        className="hidden"
      />

      <div className="w-full space-y-4">
        {/* Progress scrub */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground font-medium">
          <span className="w-10 text-right">{formatTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration || 100}
            value={currentTime}
            onChange={handleSeek}
            className="flex-1 h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary hover:h-2.5 transition-all"
          />
          <span className="w-10">{formatTime(duration)}</span>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between mt-6">
          <div className="flex-1" />
          
          <div className="flex items-center gap-4">
            <button
              onClick={() => {
                if (audioRef.current) audioRef.current.currentTime -= 10
              }}
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-full transition-colors"
            >
              <SkipBack className="w-5 h-5" />
            </button>
            
            <button
              onClick={togglePlay}
              className="w-14 h-14 bg-primary text-on-primary rounded-full flex items-center justify-center shadow-lg hover:bg-primary/90 transition-all hover:scale-105 active:scale-95"
            >
              {isPlaying ? <Pause className="w-6 h-6 fill-current" /> : <Play className="w-6 h-6 fill-current ml-1" />}
            </button>
            
            <button
              onClick={() => {
                if (audioRef.current) audioRef.current.currentTime += 10
              }}
              className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary rounded-full transition-colors"
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex-1 flex justify-end">
             <Button variant="ghost" size="icon" onClick={onDelete} className="text-destructive hover:text-destructive hover:bg-destructive/10 active:scale-[0.98] transition-all duration-150">
               <Trash2 className="w-5 h-5" />
             </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
