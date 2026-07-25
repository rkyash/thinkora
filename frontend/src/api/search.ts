import { apiClient } from '@/lib/axios'
import type { SearchResponse } from '@/types/api'

/**
 * GET /api/v1/search/
 * Hybrid semantic + full-text search with RRF ranking.
 */
export async function hybridSearch(
  query: string,
  options: {
    notebook_id?: string
    offset?: number
    limit?: number
  } = {},
): Promise<SearchResponse> {
  const res = await apiClient.get<SearchResponse>('/api/v1/search/', {
    params: {
      q: query,
      notebook_id: options.notebook_id,
      offset: options.offset ?? 0,
      limit: options.limit ?? 20,
    },
  })
  return res.data
}
