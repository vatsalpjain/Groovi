/**
 * AIOrb - Animated voice AI-style orb button
 * 
 * States:
 * - idle: Subtle glowing orb, click to record
 * - recording: Pulsing with ripple effect
 * - thinking: Expanded with flowing gradient animation
 * - complete: Shrink back with success pulse
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
        <div className="flex flex-col items-center gap-4">
            {/* Main Orb Container */}
            <button
                onClick={onClick}
                disabled={disabled || state === 'thinking'}
                className={`ai-orb-container ${stateClass} w-24 h-24 relative group focus:outline-none`}
                aria-label={
                    state === 'idle' ? 'Click to start recording' :
                        state === 'recording' ? 'Recording... click to stop' :
                            state === 'thinking' ? 'AI is thinking...' :
                                'Processing complete'
                }
            >
                {/* Layer 1: Core Blob */}
                <div className="orb-layer-1 absolute inset-0 rounded-full transition-all duration-700" />

                {/* Layer 2: Accent Swirl (Visible in Thinking/Recording) */}
                <div className="orb-layer-2 absolute inset-0 rounded-full transition-all duration-700" />

                {/* Layer 3: Highlight (Visible in Thinking) */}
                <div className="orb-layer-3 absolute inset-0 rounded-full transition-all duration-700" />

                {/* Ripple for recording */}
                {showRipple && (
                    <div className="absolute inset-0 border-2 border-red-500/30 rounded-full animate-ping" />
                )}

                {/* Glass Reflection Overlay */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-white/20 to-transparent pointer-events-none" />

                {/* Center Icon/Content */}
                <div className="relative z-10 flex items-center justify-center w-full h-full text-white drop-shadow-lg transition-transform duration-300">
                    {state === 'idle' && (
                        <svg className={`w-8 h-8 opacity-90 transition-transform group-hover:scale-110 duration-300 
                                       ${theme === 'light' ? 'text-white' : 'text-white'}`}
                            fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                        </svg>
                    )}

                    {state === 'recording' && (
                        <div className="w-6 h-6 bg-white rounded-md animate-pulse shadow-lg shadow-red-500/50" />
                    )}

                    {state === 'thinking' && (
                        <span className="text-3xl animate-pulse">✨</span>
                    )}

                    {state === 'complete' && (
                        <svg className="w-8 h-8 text-white drop-shadow-md" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                        </svg>
                    )}
                </div>
            </button>

            {/* Label */}
            <span className={`text-sm font-medium transition-all duration-300
                            ${state === 'thinking' ? 'opacity-100 translate-y-0' : 'opacity-70'}
                            ${theme === 'dark' ? 'text-zinc-300' : 'text-zinc-600'}`}>
                {state === 'idle' && 'Tap to speak'}
                {state === 'recording' && 'Listening...'}
                {state === 'thinking' && 'Creating your vibe...'}
                {state === 'complete' && 'Done!'}
            </span>
        </div>
    )
}
