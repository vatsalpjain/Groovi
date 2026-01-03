import { useState, useEffect } from 'react'

type Theme = 'light' | 'dark'

/**
 * useTheme hook - Standard dark mode implementation
 * - Persists preference to localStorage
 * - Falls back to system preference
 * - Applies 'dark' class to document element
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    // Check localStorage first
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('theme') as Theme | null
      if (stored) return stored
      
      // Fall back to system preference
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark'
      }
    }
    return 'light'
  })

  useEffect(() => {
    const root = document.documentElement
    
    // Apply theme class
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    
    // Persist to localStorage
    localStorage.setItem('theme', theme)
  }, [theme])

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    
    const handleChange = (e: MediaQueryListEvent) => {
      // Only update if user hasn't set a preference
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  return { theme, setTheme, toggleTheme }
}
