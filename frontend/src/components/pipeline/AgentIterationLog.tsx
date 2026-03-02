import { useEffect, useRef } from 'react';
import type { AgentIteration } from '../../hooks/usePipelineState';

export interface AgentIterationLogProps {
    iterations: AgentIteration[];
    isComplete: boolean;
    totalTokensBefore?: number;
    totalTokensAfter?: number;
    totalMs?: number;
}

export function AgentIterationLog({
    iterations,
    isComplete,
    totalTokensBefore,
    totalTokensAfter,
    totalMs
}: AgentIterationLogProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new iterations arrive
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [iterations, isComplete]);

    const hasIterations = iterations.length > 0;

    // Calculate savings
    const savedTokens = (totalTokensBefore && totalTokensAfter)
        ? totalTokensBefore - totalTokensAfter
        : 0;
    const savingsPercent = totalTokensBefore
        ? Math.round((savedTokens / totalTokensBefore) * 100)
        : 0;

    return (
        <div className="flex flex-col w-full h-full min-h-[120px] max-h-32 bg-black/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden relative">

            {/* Header */}
            <div className="px-3 py-1.5 bg-white/5 border-b border-white/5 flex items-center justify-between sticky top-0 z-10">
                <span className="text-[10px] text-white/50 uppercase tracking-wider font-semibold">Agent Activity</span>
                {isComplete && (
                    <span className="text-[10px] text-green-400 font-mono">Completed in {totalMs}ms</span>
                )}
            </div>

            {/* Log Content Area */}
            <div
                ref={scrollRef}
                className="flex-1 p-3 overflow-y-auto custom-scrollbar flex flex-col gap-2 scroll-smooth"
            >
                {!hasIterations && !isComplete && (
                    <div className="flex-1 flex items-center justify-center">
                        <span className="text-white/20 text-xs italic animate-pulse">Waiting for agent activity...</span>
                    </div>
                )}

                {/* Iteration Rows */}
                {iterations.map((iter) => (
                    <div
                        key={`iter-${iter.index}`}
                        className="flex items-start gap-2 animate-fade-in"
                        style={{ animationDuration: '300ms' }}
                    >
                        {/* Status Dot */}
                        <div className="mt-1">
                            <span className={`inline-block w-1.5 h-1.5 rounded-full ${iter.status === 'running' ? 'bg-purple-500 animate-pulse shadow-[0_0_8px_rgba(168,85,247,0.8)]' : 'bg-green-500'}`} />
                        </div>

                        {/* Main Content */}
                        <div className="flex-1 flex flex-col min-w-0">
                            <div className="flex items-baseline justify-between gap-2">
                                <span className="text-xs text-white/40 whitespace-nowrap">Iter {iter.index}</span>
                                <span className="text-xs font-mono text-purple-400 truncate flex-1">{iter.tool}</span>
                                <span className="text-[10px] text-white/30 font-mono whitespace-nowrap">{iter.latencyMs}ms</span>
                            </div>
                            <span className="text-[10px] text-white/60 truncate mt-0.5">{iter.resultSummary}</span>
                        </div>
                    </div>
                ))}

                {/* Completion Summary Row */}
                {isComplete && hasIterations && (
                    <div className="flex items-center gap-2 pt-2 mt-1 border-t border-white/5 animate-fade-in">
                        <svg className="w-3 h-3 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                        <div className="flex-1 flex justify-between items-center min-w-0">
                            <span className="text-[10px] text-white/50 truncate">
                                Tokens: {totalTokensBefore?.toLocaleString()} → {totalTokensAfter?.toLocaleString()}
                                {savingsPercent > 0 && (
                                    <span className="text-green-400 ml-1">({savingsPercent}% saved)</span>
                                )}
                            </span>
                            <span className="text-[10px] text-white/40 font-mono ml-2">{totalMs}ms</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
