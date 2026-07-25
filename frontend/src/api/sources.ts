import { apiClient } from '@/lib/axios'
import type { ApiResponse, Source } from '@/types/api'

/** GET /api/v1/notebooks/:notebookId/sources */
export async function listSources(
  workspaceId: string,
  notebookId: string,
): Promise<ApiResponse<Source[]>> {
  const res = await apiClient.get<ApiResponse<Source[]>>(
    `/api/v1/notebooks/${notebookId}/sources/`,
    { params: { workspace_id: workspaceId } },
  )
  return res.data
}

/** POST /api/v1/notebooks/:notebookId/sources/upload — multipart file upload */
export async function uploadSource(
  workspaceId: string,
  notebookId: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<ApiResponse<Source>> {
  const formData = new FormData()
  formData.append('file', file)

  const res = await apiClient.post<ApiResponse<Source>>(
    `/api/v1/notebooks/${notebookId}/sources/upload`,
    formData,
    {
      params: { workspace_id: workspaceId },
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded / event.total) * 100))
        }
      },
    },
  )
  return res.data
}

/** POST /api/v1/notebooks/:notebookId/sources/url */
export async function addUrlSource(
  workspaceId: string,
  notebookId: string,
  name: string,
  url: string,
): Promise<ApiResponse<Source>> {
  const res = await apiClient.post<ApiResponse<Source>>(
    `/api/v1/notebooks/${notebookId}/sources/url`,
    { name, url },
    { params: { workspace_id: workspaceId } }
  )
  return res.data
}

/** POST /api/v1/notebooks/:notebookId/sources/youtube */
export async function addYoutubeSource(
  workspaceId: string,
  notebookId: string,
  name: string,
  url: string,
): Promise<ApiResponse<Source>> {
  const res = await apiClient.post<ApiResponse<Source>>(
    `/api/v1/notebooks/${notebookId}/sources/youtube`,
    { name, url },
    { params: { workspace_id: workspaceId } }
  )
  return res.data
}

/** POST /api/v1/notebooks/:notebookId/sources/text */
export async function addTextSource(
  workspaceId: string,
  notebookId: string,
  name: string,
  content: string,
): Promise<ApiResponse<Source>> {
  const res = await apiClient.post<ApiResponse<Source>>(
    `/api/v1/notebooks/${notebookId}/sources/text`,
    { name, content },
    { params: { workspace_id: workspaceId } }
  )
  return res.data
}

/** DELETE /api/v1/notebooks/:notebookId/sources/:id */
export async function deleteSource(
  workspaceId: string, 
  notebookId: string, 
  id: string
): Promise<void> {
  await apiClient.delete(
    `/api/v1/notebooks/${notebookId}/sources/${id}`,
    { params: { workspace_id: workspaceId } }
  )
}

/** GET /api/v1/notebooks/:notebookId/sources/:id */
export async function getSource(
  workspaceId: string, 
  notebookId: string, 
  id: string
): Promise<ApiResponse<Source>> {
  const res = await apiClient.get<ApiResponse<Source>>(
    `/api/v1/notebooks/${notebookId}/sources/${id}`,
    { params: { workspace_id: workspaceId } }
  )
  return res.data
}
