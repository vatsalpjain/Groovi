import { useEffect } from 'react'
import Lenis from 'lenis'

/**
 * useSmoothScroll - Initializes Lenis smooth scrolling
 * 
 * Provides a buttery, weighted scroll experience.
 * Automatically cleans up on unmount.
 */
export function useSmoothScroll() {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,           // Scroll duration (higher = smoother)
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), // Easing function
      orientation: 'vertical', // Scroll direction
      smoothWheel: true,       // Enable smooth wheel scrolling
    })

    // Animation frame loop
    function raf(time: number) {
      lenis.raf(time)
      requestAnimationFrame(raf)
    }

    requestAnimationFrame(raf)

    // Cleanup on unmount
    return () => {
      lenis.destroy()
    }
  }, [])
}
