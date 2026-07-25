import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as workspacesApi from '@/api/workspaces'
import { workspaceKeys } from '@/utils/queryKeys'
import type { CreateWorkspaceRequest, UpdateWorkspaceRequest } from '@/types/api'

/** List all workspaces for the current user */
export function useWorkspaces() {
  return useQuery({
    queryKey: workspaceKeys.lists(),
    queryFn: () => workspacesApi.listWorkspaces(),
    select: (data) => data.data,
  })
}

/** Fetch a single workspace by ID */
export function useWorkspace(id: string) {
  return useQuery({
    queryKey: workspaceKeys.detail(id),
    queryFn: () => workspacesApi.getWorkspace(id),
    select: (res) => res.data,
    enabled: Boolean(id),
  })
}

/** Create a workspace */
export function useCreateWorkspace() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateWorkspaceRequest) => workspacesApi.createWorkspace(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Update a workspace */
export function useUpdateWorkspace(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UpdateWorkspaceRequest) => workspacesApi.updateWorkspace(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(id) })
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}

/** Delete a workspace */
export function useDeleteWorkspace() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => workspacesApi.deleteWorkspace(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() })
    },
  })
}
