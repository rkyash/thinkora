import { apiClient } from '@/lib/axios'
import type {
  ApiResponse,
  PaginatedResponse,
  Workspace,
  CreateWorkspaceRequest,
  UpdateWorkspaceRequest,
} from '@/types/api'
import type { PaginationParams } from '@/types/common'

/** GET /api/v1/workspaces */
export async function listWorkspaces(
  params?: PaginationParams,
): Promise<PaginatedResponse<Workspace>> {
  const res = await apiClient.get<PaginatedResponse<Workspace>>('/api/v1/workspaces', {
    params,
  })
  return res.data
}

/** POST /api/v1/workspaces */
export async function createWorkspace(
  data: CreateWorkspaceRequest,
): Promise<ApiResponse<Workspace>> {
  const res = await apiClient.post<ApiResponse<Workspace>>('/api/v1/workspaces', data)
  return res.data
}

/** GET /api/v1/workspaces/:id */
export async function getWorkspace(id: string): Promise<ApiResponse<Workspace>> {
  const res = await apiClient.get<ApiResponse<Workspace>>(`/api/v1/workspaces/${id}`)
  return res.data
}

/** PATCH /api/v1/workspaces/:id */
export async function updateWorkspace(
  id: string,
  data: UpdateWorkspaceRequest,
): Promise<ApiResponse<Workspace>> {
  const res = await apiClient.patch<ApiResponse<Workspace>>(`/api/v1/workspaces/${id}`, data)
  return res.data
}

/** DELETE /api/v1/workspaces/:id */
export async function deleteWorkspace(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/workspaces/${id}`)
}
