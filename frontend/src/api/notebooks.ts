import { apiClient } from '@/lib/axios'
import type {
  ApiResponse,
  PaginatedResponse,
  Notebook,
  CreateNotebookRequest,
  UpdateNotebookRequest,
} from '@/types/api'
import type { PaginationParams } from '@/types/common'

/** GET /api/v1/workspaces/:workspaceId/notebooks */
export async function listNotebooks(
  workspaceId: string,
  params?: PaginationParams,
): Promise<PaginatedResponse<Notebook>> {
  const res = await apiClient.get<PaginatedResponse<Notebook>>(
    `/api/v1/workspaces/${workspaceId}/notebooks`,
    { params },
  )
  return res.data
}

/** POST /api/v1/workspaces/:workspaceId/notebooks */
export async function createNotebook(
  workspaceId: string,
  data: Omit<CreateNotebookRequest, 'workspace_id'>,
): Promise<ApiResponse<Notebook>> {
  const res = await apiClient.post<ApiResponse<Notebook>>(
    `/api/v1/workspaces/${workspaceId}/notebooks`,
    data,
  )
  return res.data
}

/** GET /api/v1/notebooks/:id */
export async function getNotebook(id: string): Promise<ApiResponse<Notebook>> {
  const res = await apiClient.get<ApiResponse<Notebook>>(`/api/v1/notebooks/${id}`)
  return res.data
}

/** PATCH /api/v1/notebooks/:id */
export async function updateNotebook(
  id: string,
  data: UpdateNotebookRequest,
): Promise<ApiResponse<Notebook>> {
  const res = await apiClient.patch<ApiResponse<Notebook>>(`/api/v1/notebooks/${id}`, data)
  return res.data
}

/** DELETE /api/v1/notebooks/:id */
export async function deleteNotebook(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/notebooks/${id}`)
}
