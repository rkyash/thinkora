/**
 * API response types mirroring backend Pydantic schemas.
 * Keep in sync with backend/app/schemas/
 */

// ─── Generic Wrappers ────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string | null;
  request_id: string | null;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  offset: number;
  limit: number;
  has_next: boolean;
}

export interface ApiError {
  success: false;
  error: string;
  details?: Record<string, unknown>;
  request_id: string | null;
}

// ─── User ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AuthTokens {
  user: User;
  tokens: {
    access_token: string;
    refresh_token: string;
    token_type: "bearer";
  };
  // access_token: string
  // refresh_token: string
  // token_type: 'bearer'
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

// ─── Workspace ───────────────────────────────────────────────────────────────

export interface Workspace {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkspaceRequest {
  name: string;
  description?: string;
}

export interface UpdateWorkspaceRequest {
  name?: string;
  description?: string;
}

// ─── Notebook ────────────────────────────────────────────────────────────────

export interface Notebook {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  emoji: string;
  source_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateNotebookRequest {
  workspace_id: string;
  name: string;
  description?: string;
  emoji?: string;
}

export interface UpdateNotebookRequest {
  name?: string;
  description?: string;
  emoji?: string;
}

// ─── Source ──────────────────────────────────────────────────────────────────

export type SourceType =
  | "pdf"
  | "docx"
  | "xlsx"
  | "csv"
  | "markdown"
  | "txt"
  | "pptx"
  | "epub"
  | "url"
  | "youtube"
  | "audio"
  | "image"
  | "text";

export type SourceStatus = "pending" | "processing" | "ready" | "error";

export interface Source {
  id: string;
  notebook_id: string;
  name: string;
  type: SourceType;
  status: SourceStatus;
  file_path: string | null;
  url: string | null;
  char_count: number | null;
  chunk_count: number | null;
  error_message: string | null;
  created_at: string;
}

// ─── Chat ────────────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface ChatSession {
  id: string;
  notebook_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  sources: SourceCitation[];
  created_at: string;
}

export interface SourceCitation {
  source_id: string;
  source_name: string;
  chunk_content: string;
  similarity: number;
}

// ─── Notes ───────────────────────────────────────────────────────────────────

export interface BacklinkItem {
  note_id: string;
  title: string;
}

export interface Note {
  id: string;
  notebook_id: string;
  title: string | null;
  content: string | null;
  backlinks: BacklinkItem[] | null;
  created_at: string;
  updated_at: string;
}

// ─── Flashcards ──────────────────────────────────────────────────────────────

export type Difficulty = "easy" | "medium" | "hard";

export interface Flashcard {
  id: string;
  notebook_id: string;
  question: string;
  answer: string;
  difficulty: Difficulty;
  created_at: string;
}

export interface FlashcardGenerateRequest {
  count?: number;
  difficulty?: Difficulty;
  topic?: string;
  model?: string;
}

// ─── Quiz ────────────────────────────────────────────────────────────────────

export type QuestionType = "mcq" | "true_false" | "fill_blank" | "short_answer";

export interface QuizOption {
  text: string;
  is_correct: boolean;
}

export interface QuizQuestion {
  id: string;
  quiz_id: string;
  question: string;
  type: QuestionType;
  options: QuizOption[] | null;
  correct_answer: string | null;
  explanation: string | null;
}

export interface Quiz {
  id: string;
  notebook_id: string;
  title: string | null;
  created_at: string;
}

export interface QuizDetail extends Quiz {
  questions: QuizQuestion[];
}

export interface QuizGenerateRequest {
  title?: string;
  question_count?: number;
  question_types?: QuestionType[];
  topic?: string;
  model?: string;
}

// ─── Knowledge Graph ─────────────────────────────────────────────────────────

export type NodeType = "concept" | "entity" | "topic" | "person" | "place" | "event";

export interface GraphNode {
  id: string;
  notebook_id: string;
  label: string;
  type: NodeType;
  x_pos: number | null;
  y_pos: number | null;
}

export interface GraphEdge {
  id: string;
  notebook_id: string;
  source_node: string;
  target_node: string;
  label: string | null;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ─── Generation (async tasks) ────────────────────────────────────────────────

export type TaskStatus = "pending" | "processing" | "ready" | "error";
export type GenerationType = "summary" | "quiz" | "flashcards" | "study_guide" | "podcast";

export interface Generation {
  id: string;
  notebook_id: string;
  type: GenerationType;
  status: TaskStatus | null;
  content: Record<string, unknown> | null;
  audio_path: string | null;
  task_id: string | null;
  created_at: string;
}

// ─── Search ───────────────────────────────────────────────────────────────────

export interface SearchResultItem {
  chunk_id: string;
  source_id: string;
  notebook_id: string;
  source_name: string;
  content: string;
  score: number;
  rank_method: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total: number;
  offset: number;
  limit: number;
  has_next: boolean;
}

// ─── Audio/Podcast ───────────────────────────────────────────────────────────

export interface AudioGenerateRequest {
  tts_backend?: string;
  model?: string;
}

export interface AudioStatusResponse {
  generation: Generation;
  audio_url: string | null;
}
