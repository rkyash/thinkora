import { useEffect, useCallback } from 'react'
import { useSettingsStore } from '../store/settingsStore'

/**
 * ThemeProvider — Syncs the Zustand settingsStore theme to the DOM.
 * Adds/removes the 'dark' class on <html> to enable Tailwind's darkMode: 'class'.
 * Also handles 'system' preference and smooth theme transitions.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useSettingsStore((s) => s.theme)

  const applyTheme = useCallback((isDark: boolean) => {
    const root = document.documentElement
    // Enable smooth visual transition
    root.classList.add('theme-transitioning')
    root.classList.toggle('dark', isDark)
    // Remove transition class after animation completes
    requestAnimationFrame(() => {
      setTimeout(() => root.classList.remove('theme-transitioning'), 350)
    })
  }, [])

  // Apply theme whenever the setting changes
  useEffect(() => {
    if (theme === 'system') {
      applyTheme(window.matchMedia('(prefers-color-scheme: dark)').matches)
    } else {
      applyTheme(theme === 'dark')
    }
  }, [theme, applyTheme])

  // Listen for OS preference changes when in "system" mode
  useEffect(() => {
    if (theme !== 'system') return
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (e: MediaQueryListEvent) => applyTheme(e.matches)
    mql.addEventListener('change', handler)
    return () => mql.removeEventListener('change', handler)
  }, [theme, applyTheme])

  return <>{children}</>
}
