/**
 * AIOrb - Premium Smooth Gradient Voice AI Orb
 * Seamless glowing design with soft animations
 * 
 * States:
 * - idle: Gentle purple glow
 * - recording: Purple-to-pink gradient with outer glow
 * - thinking: Expanded with flowing radial gradient
 * - complete: Green success glow
 */

import { useEffect, useRef, useState } from 'react'

export type OrbState = 'idle' | 'recording' | 'thinking' | 'complete'

interface AIOrbProps {
    state: OrbState
    onClick: () => void
    disabled?: boolean
    theme?: 'light' | 'dark'
}

export function AIOrb({ state, onClick, disabled = false, theme = 'dark' }: AIOrbProps) {
    const [showRipple, setShowRipple] = useState(false)
    const prevStateRef = useRef<OrbState>(state)

    // Show ripple effect during recording
    useEffect(() => {
        setShowRipple(state === 'recording')
    }, [state])

    // Track state changes
    useEffect(() => {
        prevStateRef.current = state
    }, [state])

    // State class for container
    const stateClass = `state-${state}`

    return (
        <div className="flex flex-col items-center gap-6">
            {/* Main Orb Container */}
            <div className="orb-wrapper">
                <button
                    onClick={onClick}
                    disabled={disabled || state === 'thinking'}
                    className={`ai-orb-container ${stateClass} relative group focus:outline-none`}
                    aria-label={
                        state === 'idle' ? 'Click to start recording' :
                            state === 'recording' ? 'Recording... click to stop' :
                                state === 'thinking' ? 'AI is thinking...' :
                                    'Processing complete'
                    }
                >
                    {/* SVG Gooey Filter */}
                    <svg style={{ position: 'absolute', width: 0, height: 0 }}>
                        <defs>
                            <filter id="gooey">
                                <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
                                <feColorMatrix 
                                    in="blur"
                                    values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7" 
                                    result="gooey"
                                />
                                <feComposite in="SourceGraphic" in2="gooey" operator="atop" />
                            </filter>
                        </defs>
                    </svg>

                    {/* Border Glow Ring */}
                    <div className="orb-border-ring" />

                    {/* Outer Glow Aura */}
                    <div className="orb-outer-glow" />
                    
                    {/* Main Gradient Orb with Gooey Effect */}
                    <div className="orb-main">
                        {/* Morphing Blob Balls */}
                        <div className="orb-blob-container">
                            <div className="orb-blob orb-blob-1" />
                            <div className="orb-blob orb-blob-2" />
                            <div className="orb-blob orb-blob-3" />
                        </div>
                        
                        {/* Soft Inner Glow */}
                        <div className="orb-inner-glow" />
                        
                        {/* Center White Glow */}
                        <div className="orb-center-glow" />
                    </div>

                    {/* Subtle Pulse Rings (Recording State) */}
                    {showRipple && (
                        <>
                            <div className="orb-pulse-ring pulse-ring-1" />
                            <div className="orb-pulse-ring pulse-ring-2" />
                            <div className="orb-pulse-ring pulse-ring-3" />
                        </>
                    )}

                    {/* Icon Container */}
                    <div className="orb-icon-container">
                        {state === 'idle' && (
                            <svg 
                                className="orb-icon"
                                fill="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                            </svg>
                        )}

                        {state === 'recording' && (
                            <svg 
                                className="orb-icon"
                                fill="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                            </svg>
                        )}

                        {state === 'thinking' && (
                            <span className="orb-icon orb-icon-emoji">✨</span>
                        )}

                        {state === 'complete' && (
                            <svg 
                                className="orb-icon"
                                fill="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                            </svg>
                        )}
                    </div>
                </button>
            </div>

            {/* Label */}
            <span className={`orb-label
                            ${state === 'thinking' ? 'orb-label-active' : ''}
                            ${theme === 'dark' ? 'text-zinc-300' : 'text-zinc-600'}`}>
                {state === 'idle' && 'Tap to speak'}
                {state === 'recording' && 'Listening...'}
                {state === 'thinking' && 'Creating your vibe...'}
                {state === 'complete' && 'Done!'}
            </span>
        </div>
    )
}