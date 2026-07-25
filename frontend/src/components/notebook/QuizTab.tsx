import React, { useState } from 'react'
import {
  HelpCircle,
  Trophy,
  Sparkles,
  Play,
  Check,
  X,
  ArrowRight,
  Clock,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import { useParams } from 'react-router-dom'
import { useGenerateQuiz } from '@/hooks/useGenerate'
import type { QuizDetail, QuizQuestion, QuestionType } from '@/types/api'

interface PastScore {
  id: string
  date: string
  score: string
  type: string
}

const TYPE_LABELS: Record<string, string> = {
  mcq: 'MCQ',
  true_false: 'True / False',
  fill_blank: 'Fill in Blank',
  short_answer: 'Short Answer',
}

export function QuizTab() {
  const { id: notebookId = '' } = useParams<{ id: string }>()

  const generateQuiz = useGenerateQuiz(notebookId)

  // ─── Form state ───────────────────────────────────────────────────────────
  const [selectedTypes, setSelectedTypes] = useState<QuestionType[]>(['mcq', 'true_false'])
  const [qCount, setQCount] = useState(5)

  // ─── Quiz state ───────────────────────────────────────────────────────────
  const [activeQuiz, setActiveQuiz] = useState<QuizDetail | null>(null)
  const [currentIdx, setCurrentIdx] = useState(0)
  const [selectedOpt, setSelectedOpt] = useState<number | null>(null)
  const [shortAnswer, setShortAnswer] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)
  const [correctAnswers, setCorrectAnswers] = useState(0)
  const [quizFinished, setQuizFinished] = useState(false)
  const [pastScores, setPastScores] = useState<PastScore[]>([])

  const activeQuestion: QuizQuestion | null = activeQuiz?.questions[currentIdx] ?? null

  // ─── Toggle question types ────────────────────────────────────────────────
  const toggleType = (type: QuestionType) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.length > 1
          ? prev.filter((t) => t !== type)
          : prev
        : [...prev, type],
    )
  }

  // ─── Generation ───────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    const result = await generateQuiz.mutateAsync({
      question_count: qCount,
      question_types: selectedTypes,
    })
    if (result.data) {
      setActiveQuiz(result.data)
      setCurrentIdx(0)
      setSelectedOpt(null)
      setShortAnswer('')
      setShowFeedback(false)
      setCorrectAnswers(0)
      setQuizFinished(false)
    }
  }

  // ─── Quiz answer logic ────────────────────────────────────────────────────
  const isCorrect = (): boolean => {
    if (!activeQuestion) return false
    if (activeQuestion.type === 'mcq' && activeQuestion.options) {
      if (selectedOpt === null) return false
      return activeQuestion.options[selectedOpt]?.is_correct ?? false
    }
    if (activeQuestion.type === 'true_false') {
      if (selectedOpt === null) return false
      const answer = activeQuestion.correct_answer?.toLowerCase()
      return selectedOpt === 0 ? answer === 'true' : answer === 'false'
    }
    // short_answer / fill_blank — case-insensitive trim match
    if (activeQuestion.correct_answer) {
      return shortAnswer.trim().toLowerCase() === activeQuestion.correct_answer.toLowerCase()
    }
    return false
  }

  const handleSubmit = () => {
    if (!activeQuestion) return
    const hasInput =
      activeQuestion.type === 'mcq' || activeQuestion.type === 'true_false'
        ? selectedOpt !== null
        : shortAnswer.trim().length > 0
    if (!hasInput) return

    setShowFeedback(true)
    if (isCorrect()) setCorrectAnswers((v) => v + 1)
  }

  const handleNext = () => {
    if (!activeQuiz) return
    const nextIdx = currentIdx + 1
    if (nextIdx < activeQuiz.questions.length) {
      setCurrentIdx(nextIdx)
      setSelectedOpt(null)
      setShortAnswer('')
      setShowFeedback(false)
    } else {
      setQuizFinished(true)
      const total = activeQuiz.questions.length
      const scoreStr = `${correctAnswers}/${total} (${Math.round((correctAnswers / total) * 100)}%)`
      setPastScores((prev) => [
        {
          id: Date.now().toString(),
          date: 'Just now',
          score: scoreStr,
          type: `${selectedTypes.map((t) => TYPE_LABELS[t]).join(' + ')} (${total} Qs)`,
        },
        ...prev,
      ])
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-surface/5 px-8 py-6 space-y-6 overflow-y-auto animate-fade-in">
      {!activeQuiz || quizFinished ? (
        /* Generator panel + past scores */
        <div className="max-w-xl mx-auto w-full space-y-6">
          {/* Completion scorecard */}
          {quizFinished && activeQuiz && (
            <div className="glass-panel p-6 rounded-2xl text-center space-y-3 border-terminal-green/20 shadow-[0_0_15px_rgba(16,185,129,0.08)]">
              <Trophy className="w-12 h-12 text-terminal-green mx-auto animate-bounce" />
              <h2 className="text-xl font-headline font-bold text-foreground">Quiz Completed!</h2>
              <p className="text-2xl font-headline font-extrabold text-primary">
                {correctAnswers} / {activeQuiz.questions.length} Correct
              </p>
              <p className="text-xs text-muted-foreground">
                Score:{' '}
                {Math.round((correctAnswers / (activeQuiz.questions.length || 1)) * 100)}%
              </p>
              <Button
                onClick={() => setActiveQuiz(null)}
                className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold text-xs px-4 py-2 mt-2 active:scale-[0.98] transition-all duration-150"
              >
                Back to Generator
              </Button>
            </div>
          )}

          {/* Generator form */}
          <div className="glass-panel p-6 rounded-2xl space-y-5">
            <h3 className="text-base font-headline font-bold text-foreground flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Generate New Quiz
            </h3>

            {/* Question type multi-selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider">
                Question Types (select multiple)
              </label>
              <div className="grid grid-cols-2 gap-2">
                {(
                  ['mcq', 'true_false', 'fill_blank', 'short_answer'] as QuestionType[]
                ).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => toggleType(type)}
                    className={cn(
                      'py-2 px-3 text-xs rounded-xl border text-center font-medium transition-all active:scale-[0.98] duration-150',
                      selectedTypes.includes(type)
                        ? 'bg-primary/10 border-primary text-primary font-bold shadow-[0_0_8px_rgba(189,157,255,0.15)]'
                        : 'border-outline/20 bg-surface/20 text-muted-foreground hover:text-foreground',
                    )}
                  >
                    {TYPE_LABELS[type]}
                  </button>
                ))}
              </div>
            </div>

            {/* Count slider */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider">
                <span>Number of questions</span>
                <span className="text-primary font-bold font-sans">{qCount}</span>
              </div>
              <input
                type="range"
                min="3"
                max="20"
                value={qCount}
                onChange={(e) => setQCount(parseInt(e.target.value))}
                className="w-full h-1 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary"
              />
            </div>

            <Button
              onClick={handleGenerate}
              disabled={generateQuiz.isPending}
              className="w-full btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold h-10 flex items-center justify-center gap-2 active:scale-[0.98] transition-all duration-150"
            >
              {generateQuiz.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {generateQuiz.isPending ? 'Generating Quiz...' : 'Generate from sources'}
            </Button>

            {generateQuiz.isError && (
              <div className="flex items-center gap-2 text-xs text-destructive">
                <AlertCircle className="w-3.5 h-3.5" />
                Failed to generate quiz. Make sure the notebook has source material.
              </div>
            )}
          </div>

          {/* Past Scores */}
          {pastScores.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase font-mono tracking-wider">
                Past Scores History
              </h4>
              <div className="glass-panel p-4 rounded-xl space-y-3">
                {pastScores.map((score) => (
                  <div
                    key={score.id}
                    className="flex justify-between items-center text-xs pb-2 border-b border-outline/10 last:border-b-0 last:pb-0"
                  >
                    <div>
                      <p className="font-semibold text-foreground">{score.type}</p>
                      <span className="text-[10px] text-muted-foreground font-mono flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" />
                        {score.date}
                      </span>
                    </div>
                    <span className="font-headline font-bold text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded-lg">
                      {score.score}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Active quiz question */
        <div className="max-w-xl mx-auto w-full space-y-6">
          {/* Progress header */}
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-muted-foreground uppercase tracking-wider">
              Question {currentIdx + 1} of {activeQuiz.questions.length}
            </span>
            <span className="text-[10px] text-muted-foreground font-mono bg-surface/50 border border-outline/10 px-2 py-0.5 rounded-full">
              Correct: {correctAnswers}
            </span>
          </div>

          {/* Question card */}
          <div className="glass-panel p-6 rounded-2xl space-y-6 shadow-md">
            <div className="flex items-start gap-3">
              <HelpCircle className="w-4 h-4 text-primary mt-0.5 shrink-0" />
              <div>
                <span className="text-[9px] font-mono text-primary uppercase font-bold">
                  {TYPE_LABELS[activeQuestion?.type ?? 'mcq']}
                </span>
                <h3 className="text-base font-headline font-bold text-foreground leading-relaxed mt-1">
                  {activeQuestion?.question}
                </h3>
              </div>
            </div>

            {/* MCQ Options */}
            {(activeQuestion?.type === 'mcq') && activeQuestion.options && (
              <div className="space-y-3">
                {activeQuestion.options.map((opt, idx) => {
                  const isSelected = selectedOpt === idx
                  const isCorrectOpt = opt.is_correct
                  return (
                    <div
                      key={idx}
                      onClick={() => !showFeedback && setSelectedOpt(idx)}
                      onKeyDown={(e) => { if (!showFeedback && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setSelectedOpt(idx) } }}
                      role="button"
                      tabIndex={0}
                      className={cn(
                        'glass rounded-xl p-4 cursor-pointer transition-all duration-200 border flex items-center gap-3 select-none hover:-translate-y-0.5',
                        isSelected && !showFeedback && 'border-primary bg-primary/5 glow-sm',
                        showFeedback && isCorrectOpt &&
                          'border-terminal-green bg-terminal-green/10 shadow-[0_0_8px_rgba(16,185,129,0.2)]',
                        showFeedback && isSelected && !isCorrectOpt &&
                          'border-destructive bg-destructive/10',
                        !isSelected && !isCorrectOpt && 'border-outline/10',
                      )}
                    >
                      <div
                        className={cn(
                          'w-6 h-6 rounded-full flex items-center justify-center shrink-0 border text-xs font-mono font-bold',
                          isSelected && !showFeedback && 'bg-primary/20 text-primary border-primary',
                          showFeedback && isCorrectOpt &&
                            'bg-terminal-green/20 text-terminal-green border-terminal-green',
                          showFeedback && isSelected && !isCorrectOpt &&
                            'bg-destructive/20 text-destructive border-destructive',
                          !isSelected && (!showFeedback || !isCorrectOpt) &&
                            'border-outline/20 text-muted-foreground',
                        )}
                      >
                        {String.fromCharCode(65 + idx)}
                      </div>
                      <span className="text-xs text-foreground font-medium">{opt.text}</span>
                      {showFeedback && isCorrectOpt && (
                        <Check className="w-4 h-4 text-terminal-green ml-auto shrink-0" />
                      )}
                      {showFeedback && isSelected && !isCorrectOpt && (
                        <X className="w-4 h-4 text-destructive ml-auto shrink-0" />
                      )}
                    </div>
                  )
                })}
              </div>
            )}

            {/* True / False */}
            {activeQuestion?.type === 'true_false' && (
              <div className="flex gap-4">
                {['True', 'False'].map((label, idx) => {
                  const isSelected = selectedOpt === idx
                  const isCorrectOpt =
                    activeQuestion.correct_answer?.toLowerCase() === label.toLowerCase()
                  return (
                    <div
                      key={label}
                      onClick={() => !showFeedback && setSelectedOpt(idx)}
                      onKeyDown={(e) => { if (!showFeedback && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setSelectedOpt(idx) } }}
                      role="button"
                      tabIndex={0}
                      className={cn(
                        'flex-1 glass rounded-xl p-4 cursor-pointer transition-all duration-200 border flex items-center justify-center gap-2 select-none font-semibold text-sm hover:-translate-y-0.5',
                        isSelected && !showFeedback && 'border-primary bg-primary/5',
                        showFeedback && isCorrectOpt &&
                          'border-terminal-green bg-terminal-green/10',
                        showFeedback && isSelected && !isCorrectOpt &&
                          'border-destructive bg-destructive/10',
                        !isSelected && 'border-outline/10',
                      )}
                    >
                      {label}
                      {showFeedback && isCorrectOpt && (
                        <Check className="w-4 h-4 text-terminal-green" />
                      )}
                      {showFeedback && isSelected && !isCorrectOpt && (
                        <X className="w-4 h-4 text-destructive" />
                      )}
                    </div>
                  )
                })}
              </div>
            )}

            {/* Short answer / fill blank */}
            {(activeQuestion?.type === 'short_answer' ||
              activeQuestion?.type === 'fill_blank') && (
              <div className="space-y-3">
                <textarea
                  value={shortAnswer}
                  onChange={(e) => !showFeedback && setShortAnswer(e.target.value)}
                  disabled={showFeedback}
                  rows={3}
                  placeholder={
                    activeQuestion.type === 'fill_blank'
                      ? 'Fill in the blank...'
                      : 'Write your answer...'
                  }
                  className="w-full bg-surface/30 border border-outline/20 rounded-xl p-3 text-sm text-foreground focus:outline-none focus:border-primary/50 resize-none"
                />
                {showFeedback && activeQuestion.correct_answer && (
                  <div className="p-3 rounded-xl bg-terminal-green/10 border border-terminal-green/20">
                    <p className="text-[10px] font-mono text-terminal-green uppercase mb-1">
                      Correct Answer
                    </p>
                    <p className="text-xs text-foreground">{activeQuestion.correct_answer}</p>
                  </div>
                )}
              </div>
            )}

            {/* Explanation on feedback */}
            {showFeedback && activeQuestion?.explanation && (
              <div className="p-3 rounded-xl bg-primary/5 border border-primary/20">
                <p className="text-[10px] font-mono text-primary uppercase mb-1">Explanation</p>
                <p className="text-xs text-muted-foreground">{activeQuestion.explanation}</p>
              </div>
            )}

            {/* Submit / Next */}
            <div className="flex justify-end gap-3 border-t border-outline/10 pt-4 mt-2">
              {!showFeedback ? (
                <Button
                  onClick={handleSubmit}
                  disabled={
                    activeQuestion?.type === 'mcq' || activeQuestion?.type === 'true_false'
                      ? selectedOpt === null
                      : shortAnswer.trim().length === 0
                  }
                  className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold text-xs px-4 h-9 active:scale-[0.98] transition-all duration-150"
                >
                  Submit Answer
                </Button>
              ) : (
                <Button
                  onClick={handleNext}
                  className="btn-glow bg-primary hover:bg-violet-primary text-primary-foreground font-semibold text-xs px-4 h-9 flex items-center gap-1.5 active:scale-[0.98] transition-all duration-150"
                >
                  {currentIdx + 1 < (activeQuiz?.questions.length ?? 0)
                    ? 'Next Question'
                    : 'Finish Quiz'}
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
