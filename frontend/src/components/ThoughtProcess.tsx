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
    theme?: 'light' | 'dark'
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

export function ThoughtProcess({ steps, iterations, isExpanded: initialExpanded = false, theme = 'dark' }: ThoughtProcessProps) {
    const [isExpanded, setIsExpanded] = useState(initialExpanded)

    if (!steps || steps.length === 0) {
        return null
    }

    const isDark = theme === 'dark'

    return (
        <div className={`mt-8 backdrop-blur-xl rounded-3xl border overflow-hidden transition-all duration-300
                        ${isDark
                ? 'bg-white/[0.02] border-white/[0.06]'
                : 'bg-zinc-50/50 border-zinc-200'}`}>
            {/* Header - Click to expand */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className={`w-full px-6 py-5 flex items-center justify-between transition-colors group
                           ${isDark ? 'hover:bg-white/5' : 'hover:bg-black/5'}`}
            >
                <div className="flex items-center gap-4">
                    {/* Animated brain icon */}
                    <div className="relative">
                        <span className="text-2xl transition-transform group-hover:scale-110 duration-300">🧠</span>
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full 
                           animate-pulse shadow-lg shadow-green-500/50" />
                    </div>

                    <div className="text-left">
                        <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-zinc-800'}`}>
                            AI Thought Process
                        </h3>
                        <div className={`flex items-center gap-2 text-xs ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                            <span className={`px-2 py-0.5 rounded-full border
                                           ${isDark ? 'bg-white/5 border-white/10' : 'bg-black/5 border-black/5'}`}>
                                {iterations} iterations
                            </span>
                            <span className={`px-2 py-0.5 rounded-full border
                                           ${isDark ? 'bg-white/5 border-white/10' : 'bg-black/5 border-black/5'}`}>
                                {steps.length} steps
                            </span>
                        </div>
                    </div>
                </div>

                {/* Expand/Collapse icon */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center
                               transform transition-all duration-300
                               ${isDark ? 'bg-white/5 group-hover:bg-white/10' : 'bg-black/5 group-hover:bg-black/10'}
                        ${isExpanded ? 'rotate-180' : ''}`}>
                    <svg className={`w-5 h-5 ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </button>

            {/* Expandable content - Vertical Stack */}
            <div className={`transition-all duration-500 ease-in-out border-t
                      ${isExpanded ? 'max-h-[600px] opacity-100' : 'max-h-0 opacity-0'}
                      ${isDark ? 'border-white/[0.06]' : 'border-zinc-200'}`}>

                <div className="p-6 overflow-y-auto max-h-[500px] custom-scrollbar space-y-4">
                    {steps.map((step, index) => (
                        <div key={index} className={`relative pl-6 border-l-2 last:border-transparent pb-2 group
                                                  ${isDark ? 'border-white/10' : 'border-zinc-200'}`}>

                            {/* Timeline Dot */}
                            <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border flex items-center justify-center text-[8px] transition-colors
                                          ${isDark
                                    ? 'bg-white/10 border-white/20 text-zinc-400 group-hover:bg-purple-500/20 group-hover:text-purple-300 group-hover:border-purple-500/40'
                                    : 'bg-zinc-200 border-zinc-300 text-zinc-600 group-hover:bg-purple-100 group-hover:text-purple-700 group-hover:border-purple-300'}`}>
                                {step.iteration}
                            </div>

                            {/* Step Card */}
                            <div className={`rounded-xl p-4 border transition-all duration-300
                                          ${isDark
                                    ? 'bg-white/[0.03] border-white/[0.04] hover:bg-white/[0.05] hover:border-purple-500/20'
                                    : 'bg-white border-zinc-200 hover:border-purple-300 hover:shadow-sm'}`}>

                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {step.tool ? (
                                            <>
                                                <span className="text-lg opacity-80">{getToolIcon(step.tool)}</span>
                                                <span className={`text-sm font-medium ${isDark ? 'text-purple-200/80' : 'text-purple-700'}`}>
                                                    {formatToolName(step.tool)}
                                                </span>
                                            </>
                                        ) : (
                                            <span className={`text-sm font-medium ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>Thinking...</span>
                                        )}
                                    </div>
                                    {step.error && (
                                        <span className="text-xs text-red-500 bg-red-100 px-2 py-0.5 rounded">Error</span>
                                    )}
                                </div>

                                {step.thought && (
                                    <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-700'}`}>
                                        {step.thought}
                                    </p>
                                )}

                                {step.arguments && Object.keys(step.arguments).length > 0 && (
                                    <div className="mt-2 flex flex-wrap gap-1.5 opacity-80 hover:opacity-100 transition-opacity">
                                        {Object.entries(step.arguments).slice(0, 3).map(([key, value]) => (
                                            <span key={key} className={`text-[10px] px-1.5 py-0.5 rounded font-mono
                                                                    ${isDark ? 'bg-white/5 text-zinc-500' : 'bg-zinc-100 text-zinc-600'}`}>
                                                {key}: {String(value).substring(0, 15)}{String(value).length > 15 ? '...' : ''}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Completion Indicator */}
                    <div className={`flex items-center gap-3 pl-2 pt-2 text-sm font-medium tracking-wide
                                  ${isDark ? 'text-green-400/80' : 'text-green-600'}`}>
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span>PROCESS COMPLETE</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
