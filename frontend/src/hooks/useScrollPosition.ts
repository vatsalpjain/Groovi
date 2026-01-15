import { useState, useEffect } from 'react'

/**
 * useScrollPosition - Detects scroll position for UI effects
 * 
 * Compatible with Lenis smooth scroll - uses native scroll events
 * which Lenis also listens to internally.
 * 
 * @param threshold - Scroll distance (in px) to trigger "scrolled" state
 * @returns { scrolled: boolean, scrollY: number }
 */
export function useScrollPosition(threshold = 50) {
  const [scrolled, setScrolled] = useState(false)
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    // Handler for scroll events
    const handleScroll = () => {
      const currentScrollY = window.scrollY
      setScrollY(currentScrollY)
      setScrolled(currentScrollY > threshold)
    }

    // Check initial position (might already be scrolled on page load)
    handleScroll()

    // Use passive listener for performance
    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      window.removeEventListener('scroll', handleScroll)
    }
  }, [threshold])

  return { scrolled, scrollY }
}
