import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as sourcesApi from '@/api/sources'
import { sourceKeys, notebookKeys } from '@/utils/queryKeys'

/** List all sources in a notebook */
export function useSources(workspaceId: string, notebookId: string) {
  return useQuery({
    queryKey: sourceKeys.list(notebookId),
    queryFn: () => sourcesApi.listSources(workspaceId, notebookId),
    select: (data) => data.data,
    enabled: Boolean(workspaceId && notebookId),
    // Poll every 5s while any source is in pending/processing state
    refetchInterval: (query) => {
      const sources = query.state.data?.data ?? []
      const hasPending = sources.some((s) =>
        s.status === 'pending' || s.status === 'processing',
      )
      return hasPending ? 5000 : false
    },
  })
}

/** Get a single source */
export function useSource(workspaceId: string, notebookId: string, sourceId: string) {
  return useQuery({
    queryKey: sourceKeys.detail(sourceId),
    queryFn: () => sourcesApi.getSource(workspaceId, notebookId, sourceId),
    select: (data) => data.data,
    enabled: Boolean(workspaceId && notebookId && sourceId),
  })
}

/** Upload a file source with optional progress tracking */
export function useUploadSource(workspaceId: string, notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      file,
      onProgress,
    }: {
      file: File
      onProgress?: (pct: number) => void
    }) => sourcesApi.uploadSource(workspaceId, notebookId, file, onProgress),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourceKeys.list(notebookId) })
      void queryClient.invalidateQueries({ queryKey: notebookKeys.detail(notebookId) })
    },
  })
}

/** Add a URL source */
export function useAddUrlSource(workspaceId: string, notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, url }: { name: string; url: string }) => 
      sourcesApi.addUrlSource(workspaceId, notebookId, name, url),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourceKeys.list(notebookId) })
      void queryClient.invalidateQueries({ queryKey: notebookKeys.detail(notebookId) })
    },
  })
}

/** Add a YouTube source */
export function useAddYoutubeSource(workspaceId: string, notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, url }: { name: string; url: string }) => 
      sourcesApi.addYoutubeSource(workspaceId, notebookId, name, url),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourceKeys.list(notebookId) })
      void queryClient.invalidateQueries({ queryKey: notebookKeys.detail(notebookId) })
    },
  })
}

/** Add a text source */
export function useAddTextSource(workspaceId: string, notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ name, content }: { name: string; content: string }) => 
      sourcesApi.addTextSource(workspaceId, notebookId, name, content),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourceKeys.list(notebookId) })
      void queryClient.invalidateQueries({ queryKey: notebookKeys.detail(notebookId) })
    },
  })
}

/** Delete a source */
export function useDeleteSource(workspaceId: string, notebookId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => sourcesApi.deleteSource(workspaceId, notebookId, id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sourceKeys.list(notebookId) })
      void queryClient.invalidateQueries({ queryKey: notebookKeys.detail(notebookId) })
    },
  })
}
