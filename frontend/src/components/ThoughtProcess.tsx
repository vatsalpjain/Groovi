/**
 * ThoughtProcess - Displays AI Agent's reasoning steps
 * 
 * Shows an expandable timeline of the agent's tool calls and thoughts,
 * helping users understand how recommendations were curated.
 */

import { useState } from 'react'

interface ThoughtStep {
    iteration: number
    thought?: string
    tool?: string
    arguments?: Record<string, unknown>
    error?: string
}

interface ThoughtProcessProps {
    steps: ThoughtStep[]
    iterations: number
    isExpanded?: boolean
}

// Tool icons for visual flair
const getToolIcon = (tool: string): string => {
    const icons: Record<string, string> = {
        search_artist: '🎤',
        get_artist_top_tracks: '🔥',
        get_related_artists: '👥',
        search_tracks: '🔍',
        search_playlists: '📋',
        get_playlist_tracks: '🎵',
        search_by_genre: '🎸',
        get_genres: '📚',
        get_new_releases: '✨'
    }
    return icons[tool] || '🔧'
}

// Format tool name for display
const formatToolName = (tool: string): string => {
    return tool
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase())
}

export function ThoughtProcess({ steps, iterations, isExpanded: initialExpanded = false }: ThoughtProcessProps) {
    const [isExpanded, setIsExpanded] = useState(initialExpanded)

    if (!steps || steps.length === 0) {
        return null
    }

    return (
        <div className="mt-6 bg-gradient-to-br from-purple-500/10 via-blue-500/10 to-cyan-500/10 
                    rounded-2xl border border-white/10 backdrop-blur-sm overflow-hidden">
            {/* Header - Click to expand */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-5 py-4 flex items-center justify-between 
                   hover:bg-white/5 transition-colors"
            >
                <div className="flex items-center gap-3">
                    {/* Animated brain icon */}
                    <div className="relative">
                        <span className="text-2xl">🧠</span>
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full 
                           animate-pulse shadow-lg shadow-green-500/50" />
                    </div>

                    <div className="text-left">
                        <h3 className="font-semibold text-white">AI Thought Process</h3>
                        <p className="text-xs text-zinc-400">
                            {iterations} iterations • {steps.length} tool calls
                        </p>
                    </div>
                </div>

                {/* Expand/Collapse icon */}
                <div className={`transform transition-transform duration-200 
                        ${isExpanded ? 'rotate-180' : ''}`}>
                    <svg className="w-5 h-5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </button>

            {/* Expandable content */}
            <div className={`transition-all duration-300 ease-in-out overflow-hidden
                      ${isExpanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}>
                <div className="px-5 pb-5 space-y-3 overflow-y-auto max-h-[400px]">
                    {steps.map((step, index) => (
                        <div
                            key={index}
                            className="relative pl-8 pb-3 border-l-2 border-purple-500/30 last:border-transparent"
                        >
                            {/* Timeline dot */}
                            <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full 
                            bg-gradient-to-br from-purple-500 to-blue-500 
                            flex items-center justify-center text-[8px] font-bold text-white
                            shadow-lg shadow-purple-500/30">
                                {step.iteration}
                            </div>

                            {/* Step content */}
                            <div className="bg-white/5 rounded-xl p-4 border border-white/10 
                            hover:border-purple-500/30 transition-colors">
                                {/* Tool badge */}
                                {step.tool && (
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="text-lg">{getToolIcon(step.tool)}</span>
                                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 
                                   text-xs font-medium rounded-full">
                                            {formatToolName(step.tool)}
                                        </span>
                                    </div>
                                )}

                                {/* Thought/reasoning */}
                                {step.thought && (
                                    <p className="text-sm text-zinc-300 leading-relaxed mb-2">
                                        {step.thought}
                                    </p>
                                )}

                                {/* Arguments */}
                                {step.arguments && Object.keys(step.arguments).length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {Object.entries(step.arguments).map(([key, value]) => (
                                            <span
                                                key={key}
                                                className="px-2 py-1 bg-zinc-800/50 text-zinc-400 
                                 text-xs rounded-lg font-mono"
                                            >
                                                {key}: <span className="text-cyan-400">{String(value)}</span>
                                            </span>
                                        ))}
                                    </div>
                                )}

                                {/* Error */}
                                {step.error && (
                                    <div className="flex items-center gap-2 text-red-400 text-sm mt-2">
                                        <span>❌</span>
                                        <span>{step.error}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Completion indicator */}
                    <div className="flex items-center gap-2 pl-8 text-green-400 text-sm font-medium">
                        <span className="text-lg">✅</span>
                        <span>Recommendations curated!</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
