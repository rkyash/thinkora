/**
 * TanStack Query hooks for all Phase 3 features:
 * Notes, Flashcards, Quizzes, Knowledge Graph, Content Generation.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { noteKeys, flashcardKeys, quizKeys, graphKeys } from '@/utils/queryKeys'
import * as generateApi from '@/api/generate'
import type {
  FlashcardGenerateRequest,
  QuizGenerateRequest,
} from '@/types/api'

// ─── Notes ────────────────────────────────────────────────────────────────────

export function useNotes(notebookId: string) {
  return useQuery({
    queryKey: noteKeys.list(notebookId),
    queryFn: () => generateApi.listNotes(notebookId),
    select: (data) => data.data,
    enabled: Boolean(notebookId),
  })
}

export function useCreateNote(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { title?: string; content?: string }) =>
      generateApi.createNote(notebookId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: noteKeys.list(notebookId) })
    },
  })
}

export function useUpdateNote(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...data
    }: {
      id: string
      title?: string
      content?: string
    }) => generateApi.updateNote(id, notebookId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: noteKeys.list(notebookId) })
    },
  })
}

export function useDeleteNote(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => generateApi.deleteNote(id, notebookId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: noteKeys.list(notebookId) })
    },
  })
}

export function useSummarizeNote(notebookId: string) {
  return useMutation({
    mutationFn: (noteId: string) => generateApi.summarizeNote(noteId, notebookId),
  })
}

// ─── Flashcards ───────────────────────────────────────────────────────────────

export function useFlashcards(notebookId: string) {
  return useQuery({
    queryKey: flashcardKeys.list(notebookId),
    queryFn: () => generateApi.listFlashcards(notebookId),
    select: (data) => data.data,
    enabled: Boolean(notebookId),
  })
}

export function useGenerateFlashcards(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: FlashcardGenerateRequest = {}) =>
      generateApi.generateFlashcards(notebookId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: flashcardKeys.list(notebookId) })
    },
  })
}

export function useDeleteFlashcard(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (cardId: string) => generateApi.deleteFlashcard(notebookId, cardId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: flashcardKeys.list(notebookId) })
    },
  })
}

// ─── Quizzes ──────────────────────────────────────────────────────────────────

export function useQuizzes(notebookId: string) {
  return useQuery({
    queryKey: quizKeys.list(notebookId),
    queryFn: () => generateApi.listQuizzes(notebookId),
    select: (data) => data.data,
    enabled: Boolean(notebookId),
  })
}

export function useGenerateQuiz(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: QuizGenerateRequest = {}) =>
      generateApi.generateQuiz(notebookId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: quizKeys.list(notebookId) })
    },
  })
}

export function useDeleteQuiz(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (quizId: string) => generateApi.deleteQuiz(notebookId, quizId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: quizKeys.list(notebookId) })
    },
  })
}

// ─── Knowledge Graph ──────────────────────────────────────────────────────────

export function useGraph(notebookId: string) {
  return useQuery({
    queryKey: graphKeys.detail(notebookId),
    queryFn: () => generateApi.getGraph(notebookId),
    select: (res) => res.data,
    enabled: Boolean(notebookId),
    staleTime: 5 * 60 * 1000, // graph is expensive to generate — 5 min stale
  })
}

export function useRefreshGraph(notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => generateApi.refreshGraph(notebookId),
    onSuccess: (data) => {
      // Immediately update cache with the new graph
      queryClient.setQueryData(graphKeys.detail(notebookId), data)
    },
  })
}

// ─── Content Generation ───────────────────────────────────────────────────────

export function useGenerateSummary(notebookId: string) {
  return useMutation({
    mutationFn: () => generateApi.generateSummary(notebookId),
  })
}

export function useGenerateStudyGuide(notebookId: string) {
  return useMutation({
    mutationFn: () => generateApi.generateStudyGuide(notebookId),
  })
}

// ─── Podcast / Audio ──────────────────────────────────────────────────────────

export function useGeneratePodcast(notebookId: string) {
  return useMutation({
    mutationFn: () => generateApi.generatePodcast(notebookId),
  })
}
