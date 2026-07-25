import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  bulkUpdateSettings,
  clearSetting,
  getSettings,
  testProvider,
  updateSetting,
  fetchModels,
} from '@/api/settings'
import type { SettingsResponse, SettingResponse, ProviderTestResponse } from '@/api/settings'
import { settingsKeys } from '@/utils/queryKeys'

// ─── Query ────────────────────────────────────────────────────────────────────

/** Fetch all settings (secrets masked). Cached for 30 seconds. */
export function useSettings() {
  return useQuery<SettingsResponse>({
    queryKey: settingsKeys.all,
    queryFn: async () => {
      const res = await getSettings()
      return res.data
    },
    staleTime: 30_000,
  })
}

// ─── Mutations ────────────────────────────────────────────────────────────────

/** Update a single setting key → value. Invalidates settings cache on success. */
export function useUpdateSetting() {
  const qc = useQueryClient()
  return useMutation<SettingResponse, Error, { key: string; value: string }>({
    mutationFn: async ({ key, value }) => {
      const res = await updateSetting(key, value)
      return res.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.all })
    },
  })
}

/** Bulk-update multiple settings at once. Invalidates settings cache on success. */
export function useBulkUpdateSettings() {
  const qc = useQueryClient()
  return useMutation<SettingResponse[], Error, Record<string, string>>({
    mutationFn: async (settings) => {
      const res = await bulkUpdateSettings(settings)
      return res.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.all })
    },
  })
}

/** Clear/reset a setting to its env default. Invalidates settings cache. */
export function useClearSetting() {
  const qc = useQueryClient()
  return useMutation<null, Error, string>({
    mutationFn: async (key) => {
      const res = await clearSetting(key)
      return res.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: settingsKeys.all })
    },
  })
}

/** Test provider connectivity. Returns success/fail + message. */
export function useTestProvider() {
  return useMutation<ProviderTestResponse, Error, string>({
    mutationFn: async (providerId) => {
      const res = await testProvider(providerId)
      return res.data
    },
  })
}

/** Fetch available models dynamically from provider. */
export function useFetchModels() {
  return useMutation<string[], Error, string>({
    mutationFn: async (providerId) => {
      const res = await fetchModels(providerId)
      return res.data
    },
  })
}
