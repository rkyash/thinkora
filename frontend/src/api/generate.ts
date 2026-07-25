import { apiClient } from '@/lib/axios'
import type {
  ApiResponse,
  PaginatedResponse,
  Note,
  Flashcard,
  FlashcardGenerateRequest,
  Quiz,
  QuizDetail,
  QuizGenerateRequest,
  KnowledgeGraph,
  Generation,
} from '@/types/api'

// ─── Notes ────────────────────────────────────────────────────────────────────

export async function listNotes(
  notebookId: string,
  offset = 0,
  limit = 50,
): Promise<PaginatedResponse<Note>> {
  const res = await apiClient.get<PaginatedResponse<Note>>(
    `/api/v1/notebooks/${notebookId}/notes`,
    { params: { offset, limit } },
  )
  return res.data
}

export async function createNote(
  notebookId: string,
  data: { title?: string; content?: string },
): Promise<ApiResponse<Note>> {
  const res = await apiClient.post<ApiResponse<Note>>(
    `/api/v1/notebooks/${notebookId}/notes`,
    data,
  )
  return res.data
}

export async function updateNote(
  id: string,
  notebookId: string,
  data: Partial<{ title: string; content: string }>,
): Promise<ApiResponse<Note>> {
  const res = await apiClient.put<ApiResponse<Note>>(
    `/api/v1/notes/${id}`,
    data,
    { params: { notebook_id: notebookId } },
  )
  return res.data
}

export async function deleteNote(id: string, notebookId: string): Promise<void> {
  await apiClient.delete(`/api/v1/notes/${id}`, {
    params: { notebook_id: notebookId },
  })
}

export async function summarizeNote(
  id: string,
  notebookId: string,
): Promise<ApiResponse<{ note_id: string; summary: string }>> {
  const res = await apiClient.post<ApiResponse<{ note_id: string; summary: string }>>(
    `/api/v1/notes/${id}/summarize`,
    {},
    { params: { notebook_id: notebookId } },
  )
  return res.data
}

// ─── Flashcards ───────────────────────────────────────────────────────────────

export async function listFlashcards(
  notebookId: string,
  offset = 0,
  limit = 50,
): Promise<PaginatedResponse<Flashcard>> {
  const res = await apiClient.get<PaginatedResponse<Flashcard>>(
    `/api/v1/notebooks/${notebookId}/flashcards`,
    { params: { offset, limit } },
  )
  return res.data
}

export async function generateFlashcards(
  notebookId: string,
  payload: FlashcardGenerateRequest = {},
): Promise<ApiResponse<Flashcard[]>> {
  const res = await apiClient.post<ApiResponse<Flashcard[]>>(
    `/api/v1/notebooks/${notebookId}/flashcards/generate`,
    payload,
  )
  return res.data
}

export async function deleteFlashcard(notebookId: string, cardId: string): Promise<void> {
  await apiClient.delete(`/api/v1/notebooks/${notebookId}/flashcards/${cardId}`)
}

// ─── Quizzes ──────────────────────────────────────────────────────────────────

export async function listQuizzes(
  notebookId: string,
  offset = 0,
  limit = 20,
): Promise<PaginatedResponse<Quiz>> {
  const res = await apiClient.get<PaginatedResponse<Quiz>>(
    `/api/v1/notebooks/${notebookId}/quizzes`,
    { params: { offset, limit } },
  )
  return res.data
}

export async function generateQuiz(
  notebookId: string,
  payload: QuizGenerateRequest = {},
): Promise<ApiResponse<QuizDetail>> {
  const res = await apiClient.post<ApiResponse<QuizDetail>>(
    `/api/v1/notebooks/${notebookId}/quizzes/generate`,
    payload,
  )
  return res.data
}

export async function getQuiz(
  notebookId: string,
  quizId: string,
): Promise<ApiResponse<QuizDetail>> {
  const res = await apiClient.get<ApiResponse<QuizDetail>>(
    `/api/v1/notebooks/${notebookId}/quizzes/${quizId}`,
  )
  return res.data
}

export async function deleteQuiz(notebookId: string, quizId: string): Promise<void> {
  await apiClient.delete(`/api/v1/notebooks/${notebookId}/quizzes/${quizId}`)
}

// ─── Knowledge Graph ──────────────────────────────────────────────────────────

export async function getGraph(notebookId: string): Promise<ApiResponse<KnowledgeGraph>> {
  const res = await apiClient.get<ApiResponse<KnowledgeGraph>>(
    `/api/v1/notebooks/${notebookId}/graph`,
  )
  return res.data
}

export async function refreshGraph(notebookId: string): Promise<ApiResponse<KnowledgeGraph>> {
  const res = await apiClient.post<ApiResponse<KnowledgeGraph>>(
    `/api/v1/notebooks/${notebookId}/graph/refresh`,
  )
  return res.data
}

// ─── Content Generation ───────────────────────────────────────────────────────

export async function generateSummary(notebookId: string): Promise<ApiResponse<Generation>> {
  const res = await apiClient.post<ApiResponse<Generation>>(
    `/api/v1/notebooks/${notebookId}/generate/summary`,
  )
  return res.data
}

export async function generateStudyGuide(notebookId: string): Promise<ApiResponse<Generation>> {
  const res = await apiClient.post<ApiResponse<Generation>>(
    `/api/v1/notebooks/${notebookId}/generate/study-guide`,
  )
  return res.data
}

export async function listGenerations(
  notebookId: string,
  offset = 0,
  limit = 20,
): Promise<PaginatedResponse<Generation>> {
  const res = await apiClient.get<PaginatedResponse<Generation>>(
    `/api/v1/notebooks/${notebookId}/generate/history`,
    { params: { offset, limit } },
  )
  return res.data
}

// ─── Audio (Podcast) ──────────────────────────────────────────────────────────

export async function generatePodcast(notebookId: string): Promise<ApiResponse<Generation>> {
  const res = await apiClient.post<ApiResponse<Generation>>(
    `/api/v1/notebooks/${notebookId}/generate/podcast`,
  )
  return res.data
}
