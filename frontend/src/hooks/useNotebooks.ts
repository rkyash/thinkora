import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as notebooksApi from '@/api/notebooks'
import { notebookKeys } from '@/utils/queryKeys'
import type { CreateNotebookRequest, UpdateNotebookRequest } from '@/types/api'

/** List notebooks in a workspace */
export function useNotebooks(workspaceId: string) {
  return useQuery({
    queryKey: notebookKeys.list(workspaceId),
    queryFn: () => notebooksApi.listNotebooks(workspaceId),
    select: (data) => data.data,
    enabled: Boolean(workspaceId),
  })
}

/** Fetch a single notebook by ID */
export function useNotebook(id: string) {
  return useQuery({
    queryKey: notebookKeys.detail(id),
    queryFn: () => notebooksApi.getNotebook(id),
    select: (res) => res.data,
    enabled: Boolean(id),
  })
}

/** Create a notebook in a workspace */
export function useCreateNotebook(workspaceId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Omit<CreateNotebookRequest, 'workspace_id'>) =>
      notebooksApi.createNotebook(workspaceId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notebookKeys.list(workspaceId) })
    },
  })
}

/** Update notebook metadata */
export function useUpdateNotebook(id: string, workspaceId?: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UpdateNotebookRequest) => notebooksApi.updateNotebook(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notebookKeys.detail(id) })
      if (workspaceId) {
        void queryClient.invalidateQueries({ queryKey: notebookKeys.list(workspaceId) })
      }
    },
  })
}

/** Delete a notebook */
export function useDeleteNotebook(workspaceId?: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => notebooksApi.deleteNotebook(id),
    onSuccess: () => {
      if (workspaceId) {
        void queryClient.invalidateQueries({ queryKey: notebookKeys.list(workspaceId) })
      }
    },
  })
}
