import { apiClient } from '@/lib/axios'
import type { ApiResponse } from '@/types/api'

// ─── Response Types ───────────────────────────────────────────────────────────

export interface SettingResponse {
  key: string
  value: string | null
  is_secret: boolean
}

export interface ProviderInfo {
  id: string
  name: string
  description: string
  key_setting: string | null
  model_setting: string | null
  base_url_setting: string | null
  selected_base_url: string | null
  supports_fetch_models: boolean
  requires_key: boolean
  is_configured: boolean
  selected_model: string | null
}

export interface SettingsResponse {
  settings: SettingResponse[]
  providers: ProviderInfo[]
}

export interface ProviderTestResponse {
  provider_id: string
  success: boolean
  message: string
  model_count: number | null
}

// ─── Request Types ────────────────────────────────────────────────────────────

export interface SettingUpdate {
  value: string
}

export interface BulkSettingsUpdate {
  settings: Record<string, string>
}

// ─── Setting Key constants (mirrors backend SettingKey enum) ──────────────────

export const SettingKey = {
  ACTIVE_PROVIDER: 'active_provider',
  OPENAI_API_KEY: 'openai_api_key',
  ANTHROPIC_API_KEY: 'anthropic_api_key',
  GEMINI_API_KEY: 'gemini_api_key',
  GROQ_API_KEY: 'groq_api_key',
  MISTRAL_API_KEY: 'mistral_api_key',
  OPENROUTER_API_KEY: 'openrouter_api_key',
  OPENAI_PROXY_BASE_URL: 'openai_proxy_base_url',
  OPENAI_PROXY_API_KEY: 'openai_proxy_api_key',
  OLLAMA_BASE_URL: 'ollama_base_url',
  DEFAULT_CHAT_MODEL: 'default_chat_model',
  DEFAULT_GENERATION_MODEL: 'default_generation_model',
  // Per-provider model selections
  OPENAI_MODEL: 'openai_model',
  ANTHROPIC_MODEL: 'anthropic_model',
  GEMINI_MODEL: 'gemini_model',
  GROQ_MODEL: 'groq_model',
  MISTRAL_MODEL: 'mistral_model',
  OPENROUTER_MODEL: 'openrouter_model',
  OLLAMA_MODEL: 'ollama_model',
  OPENAI_PROXY_MODEL: 'openai_proxy_model',
  // Appearance
  THEME: 'theme',
  FONT_SIZE: 'font_size',
  COMPACT_MODE: 'compact_mode',
} as const

// ─── API Functions ────────────────────────────────────────────────────────────

/** GET /api/v1/settings — all settings with secrets masked */
export async function getSettings(): Promise<ApiResponse<SettingsResponse>> {
  const res = await apiClient.get<ApiResponse<SettingsResponse>>('/api/v1/settings')
  return res.data
}

/** PUT /api/v1/settings/{key} — update a single setting */
export async function updateSetting(
  key: string,
  value: string,
): Promise<ApiResponse<SettingResponse>> {
  const res = await apiClient.put<ApiResponse<SettingResponse>>(`/api/v1/settings/${key}`, {
    value,
  })
  return res.data
}

/** PUT /api/v1/settings — bulk update multiple settings */
export async function bulkUpdateSettings(
  settings: Record<string, string>,
): Promise<ApiResponse<SettingResponse[]>> {
  const res = await apiClient.put<ApiResponse<SettingResponse[]>>('/api/v1/settings', {
    settings,
  })
  return res.data
}

/** DELETE /api/v1/settings/{key} — clear/reset a setting to env default */
export async function clearSetting(key: string): Promise<ApiResponse<null>> {
  const res = await apiClient.delete<ApiResponse<null>>(`/api/v1/settings/${key}`)
  return res.data
}

/** POST /api/v1/settings/test/{provider_id} — test provider connectivity */
export async function testProvider(
  providerId: string,
): Promise<ApiResponse<ProviderTestResponse>> {
  const res = await apiClient.post<ApiResponse<ProviderTestResponse>>(
    `/api/v1/settings/test/${providerId}`,
  )
  return res.data
}

/** GET /api/v1/settings/models/{provider_id} — fetch dynamic models */
export async function fetchModels(
  providerId: string,
): Promise<ApiResponse<string[]>> {
  const res = await apiClient.get<ApiResponse<string[]>>(
    `/api/v1/settings/models/${providerId}`,
  )
  return res.data
}
