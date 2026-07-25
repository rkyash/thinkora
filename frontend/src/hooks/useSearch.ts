import { useQuery } from '@tanstack/react-query'
import { searchKeys } from '@/utils/queryKeys'
import * as searchApi from '@/api/search'

export function useSearch(
  query: string,
  options: {
    notebook_id?: string
    offset?: number
    limit?: number
  } = {},
) {
  return useQuery({
    queryKey: searchKeys.results(query, options),
    queryFn: () => searchApi.hybridSearch(query, options),
    enabled: query.trim().length >= 2,
    staleTime: 30_000,
    placeholderData: (prev) => prev, // keep previous results while fetching
  })
}
