/**
 * AgentLoader - Shows live AI Agent activity while waiting for results
 * 
 * Displays an animated view of the agent "thinking" with simulated
 * tool calls that mimic the actual agent behavior.
 */

import { useState, useEffect } from 'react'

// Simulated agent steps based on query type
const AGENT_STEPS = [
    { tool: 'search_artist', icon: '🎤', text: 'Searching for artists...' },
    { tool: 'get_artist_top_tracks', icon: '🔥', text: 'Getting top tracks...' },
    { tool: 'get_related_artists', icon: '👥', text: 'Finding similar artists...' },
    { tool: 'search_playlists', icon: '📋', text: 'Exploring playlists...' },
    { tool: 'get_playlist_tracks', icon: '🎵', text: 'Gathering playlist tracks...' },
    { tool: 'curating', icon: '✨', text: 'Curating your perfect mix...' },
]

export function AgentLoader() {
    const [currentStep, setCurrentStep] = useState(0)
    const [completedSteps, setCompletedSteps] = useState<number[]>([])

    // Cycle through steps to simulate agent activity
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentStep(prev => {
                const next = (prev + 1) % AGENT_STEPS.length

                // Mark previous step as completed
                if (prev < AGENT_STEPS.length - 1) {
                    setCompletedSteps(steps => [...steps, prev])
                }

                // Reset if we've done a full cycle
                if (next === 0) {
                    setCompletedSteps([])
                }

                return next
            })
        }, 2000) // Change step every 2 seconds

        return () => clearInterval(interval)
    }, [])

    return (
        <div className="mt-12 p-6 rounded-2xl bg-white/[0.02] backdrop-blur-2xl
                    border border-white/[0.06]">
            {/* Header */}
            <div className="flex items-center gap-3 mb-6">
                {/* Animated brain */}
                <div className="relative">
                    <span className="text-3xl animate-pulse">🧠</span>
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full 
                         animate-ping shadow-lg shadow-green-500/50" />
                </div>

                <div>
                    <h3 className="font-bold text-lg text-white">AI Agent Working</h3>
                    <p className="text-sm text-zinc-400">Exploring Spotify's catalog for you...</p>
                </div>
            </div>

            {/* Steps timeline */}
            <div className="space-y-3">
                {AGENT_STEPS.map((step, index) => {
                    const isActive = index === currentStep
                    const isCompleted = completedSteps.includes(index)
                    const isPending = index > currentStep && !isCompleted

                    return (
                        <div
                            key={step.tool}
                            className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-500
                         ${isActive
                                    ? 'bg-purple-500/20 border border-purple-500/50 scale-[1.02]'
                                    : isCompleted
                                        ? 'bg-green-500/10 border border-green-500/30'
                                        : 'bg-zinc-800/30 border border-transparent opacity-50'
                                }`}
                        >
                            {/* Status indicator */}
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-lg
                             ${isActive
                                    ? 'bg-purple-500/30 animate-pulse'
                                    : isCompleted
                                        ? 'bg-green-500/30'
                                        : 'bg-zinc-700/30'
                                }`}>
                                {isCompleted ? '✓' : step.icon}
                            </div>

                            {/* Text */}
                            <span className={`flex-1 text-sm font-medium
                              ${isActive
                                    ? 'text-purple-300'
                                    : isCompleted
                                        ? 'text-green-400'
                                        : 'text-zinc-500'
                                }`}>
                                {step.text}
                            </span>

                            {/* Loading spinner for active step */}
                            {isActive && (
                                <div className="w-5 h-5 border-2 border-purple-500/30 border-t-purple-500 
                              rounded-full animate-spin" />
                            )}

                            {/* Checkmark for completed */}
                            {isCompleted && (
                                <span className="text-green-500 text-lg">✓</span>
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Progress bar */}
            <div className="mt-6">
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500"
                        style={{ width: `${((currentStep + 1) / AGENT_STEPS.length) * 100}%` }}
                    />
                </div>
                <p className="text-xs text-zinc-500 mt-2 text-center">
                    Step {currentStep + 1} of {AGENT_STEPS.length}
                </p>
            </div>
        </div>
    )
}
