import React, { useState } from 'react'
import {
  ChevronLeft,
  ChevronRight,
  RotateCw,
  Shuffle,
  BookOpen,
  Sparkles,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import { useParams } from 'react-router-dom'
import { useFlashcards, useGenerateFlashcards, useDeleteFlashcard } from '@/hooks/useGenerate'
import type { Flashcard, FlashcardGenerateRequest, Difficulty } from '@/types/api'

const difficultyColors: Record<Difficulty, string> = {
  easy: 'text-terminal-green',
  medium: 'text-terminal-yellow',
  hard: 'text-terminal-red',
}

export function FlashcardsTab() {
  const { id: notebookId = '' } = useParams<{ id: string }>()

  // ─── Remote data ──────────────────────────────────────────────────────────
  const { data: cards = [], isLoading, isError } = useFlashcards(notebookId)
  const generateFlashcards = useGenerateFlashcards(notebookId)
  const deleteFlashcard = useDeleteFlashcard(notebookId)

  // ─── Local state ──────────────────────────────────────────────────────────
  const [displayCards, setDisplayCards] = useState<Flashcard[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)
  const [studyMode, setStudyMode] = useState(true)
  const [selfRatings, setSelfRatings] = useState<Record<string, Difficulty>>({})
  const [genCount, setGenCount] = useState(10)
  const [genDifficulty, setGenDifficulty] = useState<Difficulty | ''>('')

  // Sync display cards when remote data updates
  React.useEffect(() => {
    setDisplayCards(cards)
    setCurrentIndex(0)
    setIsFlipped(false)
  }, [cards])

  const activeCard = displayCards[currentIndex] ?? null
  const progressPercent = displayCards.length
    ? ((currentIndex + 1) / displayCards.length) * 100
    : 0

  // ─── Navigation ───────────────────────────────────────────────────────────
  const handleNext = () => {
    setIsFlipped(false)
    setTimeout(() => setCurrentIndex((i) => (i + 1) % displayCards.length), 200)
  }
  const handlePrev = () => {
    setIsFlipped(false)
    setTimeout(
      () => setCurrentIndex((i) => (i - 1 + displayCards.length) % displayCards.length),
      200,
    )
  }
  const handleShuffle = () => {
    setIsFlipped(false)
    setTimeout(() => {
      setDisplayCards((prev) => [...prev].sort(() => Math.random() - 0.5))
      setCurrentIndex(0)
    }, 200)
  }

  const handleRateSelf = (difficulty: Difficulty) => {
    if (!activeCard) return
    setSelfRatings((prev) => ({ ...prev, [activeCard.id]: difficulty }))
    handleNext()
  }

  // ─── Generation ───────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    const payload: FlashcardGenerateRequest = {
      count: genCount,
      difficulty: genDifficulty || undefined,
    }
    await generateFlashcards.mutateAsync(payload)
    setCurrentIndex(0)
    setIsFlipped(false)
    setStudyMode(true)
  }

  // ─── Loading / error ──────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-muted-foreground text-sm">
        <Loader2 className="w-4 h-4 animate-spin text-primary" />
        Loading flashcards...
      </div>
    )
  }
  if (isError) {
    return (
      <div className="flex-1 flex items-center justify-center gap-2 text-destructive text-sm">
        <AlertCircle className="w-4 h-4" />
        Failed to load flashcards.
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-surface/5 px-8 py-6 space-y-6 overflow-y-auto animate-fade-in">
      {/* Progress Bar & Header Controls */}
      <div className="max-w-xl mx-auto w-full flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider">
            Progress
          </span>
          <div className="text-sm font-headline font-bold text-foreground mt-0.5">
            {displayCards.length === 0 ? 'No cards' : `Card ${currentIndex + 1} of ${displayCards.length}`}
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleShuffle}
            disabled={displayCards.length === 0}
            className="border-outline/20 bg-surface/30 hover:bg-surface/50 text-foreground flex items-center gap-1 text-xs active:scale-[0.98] transition-all duration-150"
          >
            <Shuffle className="w-3.5 h-3.5" />
            Shuffle
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setStudyMode((v) => !v)}
            className={cn(
              'border-outline/20 text-xs flex items-center gap-1 active:scale-[0.98] transition-all duration-150',
              studyMode
                ? 'bg-primary/20 text-primary border-primary/30'
                : 'bg-surface/30 hover:bg-surface/50 text-foreground',
            )}
          >
            <BookOpen className="w-3.5 h-3.5" />
            {studyMode ? 'Study Mode' : 'All Cards'}
          </Button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="max-w-xl mx-auto w-full h-1 bg-surface/50 rounded-full overflow-hidden shrink-0 border border-outline/5">
        <div
          className="h-full bg-gradient-violet transition-all duration-300 shadow-[0_0_10px_rgba(189,157,255,0.4)]"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Empty state — no cards yet */}
      {displayCards.length === 0 && (
        <div className="max-w-xl mx-auto w-full glass-panel p-6 rounded-2xl space-y-5">
          <h3 className="text-base font-headline font-bold text-foreground flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            Generate Flashcards
          </h3>
          <p className="text-xs text-muted-foreground">
            No flashcards yet. Generate a set from your notebook's source material.
          </p>

          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider">
              <span>Number of cards</span>
              <span className="text-primary font-bold font-sans">{genCount}</span>
            </div>
            <input
              type="range"
              min="5"
              max="30"
              value={genCount}
              onChange={(e) => setGenCount(parseInt(e.target.value))}
              className="w-full h-1 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>

          <div className="grid grid-cols-4 gap-2">
            {(['', 'easy', 'medium', 'hard'] as const).map((d) => (
              <button
                key={d}
                onClick={() => setGenDifficulty(d as Difficulty | '')}
                className={cn(
                  'py-1.5 px-2 text-xs rounded-xl border text-center font-medium transition-all active:scale-[0.98] duration-150',
                  genDifficulty === d
                    ? 'bg-primary/10 border-primary text-primary font-bold'
                    : 'border-outline/20 bg-surface/20 text-muted-foreground hover:text-foreground',
                )}
              >
                {d === '' ? 'All' : d.charAt(0).toUpperCase() + d.slice(1)}
              </button>
            ))}
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generateFlashcards.isPending}
            className="w-full btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold h-10 flex items-center justify-center gap-2 active:scale-[0.98] transition-all duration-150"
          >
            {generateFlashcards.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {generateFlashcards.isPending ? 'Generating...' : 'Generate from sources'}
          </Button>
        </div>
      )}

      {/* Study mode — flip cards */}
      {displayCards.length > 0 && studyMode && activeCard && (
        <div className="flex-1 flex flex-col items-center justify-center py-4">
          {/* Regenerate button */}
          <div className="max-w-lg w-full flex justify-end mb-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleGenerate}
              disabled={generateFlashcards.isPending}
              className="border-outline/20 bg-surface/30 hover:bg-surface/50 text-foreground flex items-center gap-1 text-xs active:scale-[0.98] transition-all duration-150"
            >
              {generateFlashcards.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              Regenerate
            </Button>
          </div>

          <div
            onClick={() => setIsFlipped((f) => !f)}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setIsFlipped((f) => !f) } }}
            role="button"
            tabIndex={0}
            aria-label="Flip flashcard"
            className="w-full max-w-lg h-72 flashcard cursor-pointer group"
          >
            <div
              className={cn(
                'w-full h-full relative flashcard-inner rounded-2xl glass-panel',
                isFlipped && 'flipped',
              )}
            >
              {/* Card Front */}
              <div className="absolute inset-0 w-full h-full flashcard-front flex flex-col p-8 justify-between select-none">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono tracking-wider text-primary uppercase font-bold flex items-center gap-1">
                    <RotateCw className="w-3 h-3 animate-spin-slow" />
                    Click to flip
                  </span>
                  <span
                    className={cn(
                      'text-[9px] font-mono font-semibold uppercase',
                      difficultyColors[activeCard.difficulty],
                    )}
                  >
                    {activeCard.difficulty}
                  </span>
                </div>
                <div className="text-lg font-headline font-bold text-center text-foreground px-4 leading-relaxed my-auto">
                  {activeCard.question}
                </div>
                <div className="text-center text-xs text-muted-foreground font-mono">
                  Question
                </div>
              </div>

              {/* Card Back */}
              <div className="absolute inset-0 w-full h-full flashcard-back flex flex-col p-8 justify-between select-none bg-surface/85">
                <span className="text-[10px] font-mono tracking-wider text-secondary uppercase font-bold">
                  Answer details
                </span>
                <div className="text-sm text-foreground/90 whitespace-pre-line leading-relaxed my-auto overflow-y-auto pr-2 px-2 text-center">
                  {activeCard.answer}
                </div>
                <div className="text-center text-xs text-muted-foreground font-mono">
                  Answer
                </div>
              </div>
            </div>
          </div>

          {/* Self-rating */}
          <div className="flex flex-col items-center gap-3 mt-6">
            <span className="text-xs text-muted-foreground font-medium">
              How well did you know this?
            </span>
            <div className="flex gap-3">
              <Button
                variant="outline"
                className="border-terminal-red/20 hover:border-terminal-red/50 bg-terminal-red/5 text-terminal-red hover:bg-terminal-red/10 text-xs font-semibold px-4 h-9 active:scale-[0.98] transition-all duration-150"
                onClick={() => handleRateSelf('hard')}
              >
                Hard
              </Button>
              <Button
                variant="outline"
                className="border-terminal-yellow/20 hover:border-terminal-yellow/50 bg-terminal-yellow/5 text-terminal-yellow hover:bg-terminal-yellow/10 text-xs font-semibold px-4 h-9 active:scale-[0.98] transition-all duration-150"
                onClick={() => handleRateSelf('medium')}
              >
                Medium
              </Button>
              <Button
                variant="outline"
                className="border-terminal-green/20 hover:border-terminal-green/50 bg-terminal-green/5 text-terminal-green hover:bg-terminal-green/10 text-xs font-semibold px-4 h-9 active:scale-[0.98] transition-all duration-150"
                onClick={() => handleRateSelf('easy')}
              >
                Easy
              </Button>
            </div>
          </div>

          {/* Prev / Next navigation */}
          <div className="flex items-center gap-6 mt-6">
            <Button
              variant="outline"
              size="icon"
              onClick={handlePrev}
              className="border-outline/20 bg-surface/30 hover:bg-surface/50 text-foreground rounded-full w-10 h-10 active:scale-[0.98] transition-all duration-150"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <span className="text-sm text-muted-foreground font-mono font-medium">
              {currentIndex + 1} / {displayCards.length}
            </span>
            <Button
              variant="outline"
              size="icon"
              onClick={handleNext}
              className="border-outline/20 bg-surface/30 hover:bg-surface/50 text-foreground rounded-full w-10 h-10 active:scale-[0.98] transition-all duration-150"
            >
              <ChevronRight className="w-5 h-5" />
            </Button>
          </div>
        </div>
      )}

      {/* All cards grid view */}
      {displayCards.length > 0 && !studyMode && (
        <div className="max-w-3xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-4">
          {displayCards.map((card, idx) => (
            <div
              key={card.id}
              className="glass-panel p-5 rounded-xl flex flex-col justify-between hover:border-primary/20 transition-all duration-200 hover:-translate-y-0.5"
            >
              <div>
                <div className="flex justify-between items-center text-[9px] font-mono text-muted-foreground uppercase border-b border-outline/10 pb-2 mb-3">
                  <span>Card #{idx + 1}</span>
                  <span className={difficultyColors[card.difficulty]}>{card.difficulty}</span>
                </div>
                <h4 className="text-sm font-headline font-bold text-foreground">
                  {card.question}
                </h4>
                <p className="text-xs text-muted-foreground mt-2 line-clamp-3 leading-relaxed whitespace-pre-line">
                  {card.answer}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
