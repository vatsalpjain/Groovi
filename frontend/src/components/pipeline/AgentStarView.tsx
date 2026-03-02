import { useMemo } from 'react';
import { FaRobot, FaSearch, FaUser, FaListUl, FaMusic } from 'react-icons/fa';
import type { AgentIteration } from '../../hooks/usePipelineState';

// 4 MCP tools the agent can call, arranged around the center AGENT node
const TOOL_NODES = [
    { id: 'search_tracks', label: 'Search\nTracks', icon: FaSearch, angle: -90 }, // top
    { id: 'search_artist', label: 'Search\nArtist', icon: FaUser, angle: 0 }, // right
    { id: 'get_playlist_tracks', label: 'Playlist\nTracks', icon: FaMusic, angle: 90 }, // bottom
    { id: 'search_playlists', label: 'Search\nPlaylists', icon: FaListUl, angle: 180 }, // left
] as const;

// Radius of the orbital circle (px)
const ORBIT_RADIUS = 120;
// Center node size
const CENTER_SIZE = 64;
// Orbital node size
const ORBITAL_SIZE = 48;

export interface AgentStarViewProps {
    iterations: AgentIteration[];
    isComplete: boolean;
    totalTokensBefore?: number;
    totalTokensAfter?: number;
    totalMs?: number;
}

export function AgentStarView({
    iterations,
    isComplete,
    totalTokensBefore,
    totalTokensAfter,
    totalMs
}: AgentStarViewProps) {

    // Determine state per-tool: which tools were called and in what order
    const toolStates = useMemo(() => {
        const states: Record<string, 'idle' | 'active' | 'done'> = {
            search_tracks: 'idle',
            search_artist: 'idle',
            search_playlists: 'idle',
            get_playlist_tracks: 'idle',
        };

        // Mark all tools that have been called as done
        for (const iter of iterations) {
            if (iter.tool in states) {
                states[iter.tool] = 'done';
            }
        }

        // If the agent is still running, mark the most recent tool as active
        if (!isComplete && iterations.length > 0) {
            const lastTool = iterations[iterations.length - 1].tool;
            if (lastTool in states) {
                states[lastTool] = 'done'; // just completed its call
            }
        }

        return states;
    }, [iterations, isComplete]);

    // Is the agent currently running (at least one iteration but not complete)
    const isAgentActive = iterations.length > 0 && !isComplete;

    // Current iteration display
    const currentIteration = iterations.length;
    const maxIterations = 5;

    // Token savings
    const savedTokens = (totalTokensBefore && totalTokensAfter)
        ? totalTokensBefore - totalTokensAfter
        : 0;
    const savingsPercent = totalTokensBefore
        ? Math.round((savedTokens / totalTokensBefore) * 100)
        : 0;

    return (
        <div className="flex flex-col items-center w-full h-full gap-4">

            {/* Star Graph Container */}
            <div
                className="relative flex-shrink-0"
                style={{ width: ORBIT_RADIUS * 2 + ORBITAL_SIZE + 40, height: ORBIT_RADIUS * 2 + ORBITAL_SIZE + 40 }}
            >
                {/* SVG for radial lines */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {TOOL_NODES.map((tool) => {
                        const cx = (ORBIT_RADIUS * 2 + ORBITAL_SIZE + 40) / 2;
                        const cy = (ORBIT_RADIUS * 2 + ORBITAL_SIZE + 40) / 2;
                        const rad = (tool.angle * Math.PI) / 180;
                        const tx = cx + ORBIT_RADIUS * Math.cos(rad);
                        const ty = cy + ORBIT_RADIUS * Math.sin(rad);
                        const state = toolStates[tool.id];

                        return (
                            <line
                                key={`line-${tool.id}`}
                                x1={cx}
                                y1={cy}
                                x2={tx}
                                y2={ty}
                                stroke={
                                    state === 'done'
                                        ? 'rgba(34, 197, 94, 0.6)'
                                        : state === 'active'
                                            ? 'rgba(139, 92, 246, 0.8)'
                                            : 'rgba(139, 92, 246, 0.15)'
                                }
                                strokeWidth={state === 'idle' ? 1 : 2}
                                className="transition-all duration-500"
                                strokeDasharray={state === 'active' ? '6 4' : 'none'}
                            >
                                {state === 'active' && (
                                    <animate
                                        attributeName="stroke-dashoffset"
                                        values="10;0"
                                        dur="0.6s"
                                        repeatCount="indefinite"
                                    />
                                )}
                            </line>
                        );
                    })}
                </svg>

                {/* Center AGENT node */}
                <div
                    className="absolute flex items-center justify-center rounded-full transition-all duration-300 z-10"
                    style={{
                        width: CENTER_SIZE,
                        height: CENTER_SIZE,
                        left: '50%',
                        top: '50%',
                        transform: 'translate(-50%, -50%)',
                        background: isAgentActive
                            ? 'rgba(88, 28, 135, 0.4)'
                            : isComplete
                                ? 'rgba(255, 255, 255, 0.05)'
                                : 'rgba(255, 255, 255, 0.03)',
                        border: isAgentActive
                            ? '2px solid rgba(139, 92, 246, 0.8)'
                            : isComplete
                                ? '2px solid rgba(34, 197, 94, 0.5)'
                                : '1px solid rgba(139, 92, 246, 0.2)',
                        boxShadow: isAgentActive
                            ? '0 0 25px rgba(139, 92, 246, 0.6)'
                            : 'none',
                    }}
                >
                    {/* Active spinner */}
                    {isAgentActive && (
                        <div className="absolute inset-0 rounded-full border-t-2 border-purple-400 animate-spin" />
                    )}
                    <FaRobot className={`w-6 h-6 transition-opacity duration-300 ${isAgentActive ? 'text-purple-300 opacity-100' : isComplete ? 'text-green-400 opacity-70' : 'text-white opacity-40'
                        }`} />

                    {/* Done badge */}
                    {isComplete && iterations.length > 0 && (
                        <div className="absolute -top-1 -right-1 bg-green-500 rounded-full w-4 h-4 flex items-center justify-center border border-black z-10">
                            <svg className="w-2.5 h-2.5 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                    )}
                </div>

                {/* Iteration counter below center */}
                {currentIteration > 0 && (
                    <div
                        className="absolute z-10 text-center"
                        style={{
                            left: '50%',
                            top: '50%',
                            transform: `translate(-50%, ${CENTER_SIZE / 2 + 6}px)`,
                        }}
                    >
                        <span className={`text-xs font-mono tracking-wide ${isComplete ? 'text-green-400' : 'text-purple-400'
                            }`}>
                            {currentIteration}/{maxIterations}
                        </span>
                    </div>
                )}

                {/* Orbital tool nodes */}
                {TOOL_NODES.map((tool) => {
                    const rad = (tool.angle * Math.PI) / 180;
                    const halfContainer = (ORBIT_RADIUS * 2 + ORBITAL_SIZE + 40) / 2;
                    const left = halfContainer + ORBIT_RADIUS * Math.cos(rad) - ORBITAL_SIZE / 2;
                    const top = halfContainer + ORBIT_RADIUS * Math.sin(rad) - ORBITAL_SIZE / 2;
                    const state = toolStates[tool.id];
                    const Icon = tool.icon;

                    // Find iteration info for this tool (latest call)
                    const toolIter = [...iterations].reverse().find(i => i.tool === tool.id);

                    return (
                        <div key={tool.id} className="absolute" style={{ left, top }}>
                            {/* Node circle */}
                            <div
                                className={`flex items-center justify-center rounded-full transition-all duration-300
                                    ${state === 'active'
                                        ? 'bg-purple-900/30 border-2 border-purple-400'
                                        : state === 'done'
                                            ? 'bg-white/5 border border-green-500/60'
                                            : 'bg-white/5 border border-purple-900/40 opacity-60'
                                    }`}
                                style={{
                                    width: ORBITAL_SIZE,
                                    height: ORBITAL_SIZE,
                                    boxShadow: state === 'active'
                                        ? '0 0 20px rgba(139, 92, 246, 0.7)'
                                        : 'none',
                                }}
                            >
                                {/* Active spinner */}
                                {state === 'active' && (
                                    <div className="absolute inset-0 rounded-full border-t-2 border-purple-400 animate-spin" />
                                )}
                                <Icon className={`w-4 h-4 transition-opacity duration-300 ${state === 'idle' ? 'text-white opacity-40' : 'text-white opacity-80'
                                    }`} />

                                {/* Done badge */}
                                {state === 'done' && (
                                    <div className="absolute -top-1 -right-1 bg-green-500 rounded-full w-3.5 h-3.5 flex items-center justify-center border border-black z-10">
                                        <svg className="w-2 h-2 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                )}
                            </div>

                            {/* Label + result info */}
                            <div className="mt-1.5 text-center" style={{ width: ORBITAL_SIZE + 20, marginLeft: -10 }}>
                                <span className="text-[9px] text-white/40 font-medium leading-tight whitespace-pre-line">
                                    {tool.label}
                                </span>
                                {toolIter && (
                                    <span className="block text-[9px] text-white/30 font-mono mt-0.5">
                                        {toolIter.resultSummary}
                                    </span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Completion Summary */}
            {isComplete && iterations.length > 0 && (
                <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 animate-fade-in">
                    <svg className="w-3.5 h-3.5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-xs text-white/50">
                        {iterations.length} tool calls
                        {totalMs && <span className="text-white/40 ml-1">· {totalMs}ms</span>}
                        {savingsPercent > 0 && (
                            <span className="text-green-400 ml-1">
                                · Tokens: {totalTokensBefore?.toLocaleString()} → {totalTokensAfter?.toLocaleString()} ({savingsPercent}% saved)
                            </span>
                        )}
                    </span>
                </div>
            )}

            {/* Waiting state */}
            {iterations.length === 0 && !isComplete && (
                <span className="text-white/20 text-xs italic animate-pulse">
                    Waiting for music agent...
                </span>
            )}
        </div>
    );
}
