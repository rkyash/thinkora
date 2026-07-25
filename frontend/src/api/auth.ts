import { apiClient } from '@/lib/axios'
import type { ApiResponse, User, AuthTokens } from '@/types/api'

// ─── Request Types ────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface RefreshRequest {
  refresh_token: string
}

// ─── API Functions ────────────────────────────────────────────────────────────

/** POST /api/v1/auth/register */
export async function register(data: RegisterRequest): Promise<ApiResponse<User>> {
  const res = await apiClient.post<ApiResponse<User>>('/api/v1/auth/register', data)
  return res.data
}

/** POST /api/v1/auth/login → returns tokens */
export async function login(data: LoginRequest): Promise<ApiResponse<AuthTokens>> {
  const res = await apiClient.post<ApiResponse<AuthTokens>>('/api/v1/auth/login', data)
  return res.data
}

/** POST /api/v1/auth/refresh → returns new access_token */
export async function refreshTokens(data: RefreshRequest): Promise<ApiResponse<AuthTokens>> {
  const res = await apiClient.post<ApiResponse<AuthTokens>>('/api/v1/auth/refresh', data)
  return res.data
}

/** POST /api/v1/auth/logout */
export async function logout(): Promise<void> {
  await apiClient.post('/api/v1/auth/logout')
}

/** GET /api/v1/auth/me → current user profile */
export async function getMe(): Promise<ApiResponse<User>> {
  const res = await apiClient.get<ApiResponse<User>>('/api/v1/auth/me')
  return res.data
}
