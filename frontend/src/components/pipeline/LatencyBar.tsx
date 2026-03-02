

export interface LatencyBarProps {
    sttMs?: number;
    llmMs?: number;
    ttsMs?: number;
    totalMs?: number;
    threshold?: number; // default 1100
}

export function LatencyBar({
    sttMs,
    llmMs,
    ttsMs,
    totalMs,
    threshold = 1100
}: LatencyBarProps) {

    if (!totalMs && !sttMs && !llmMs && !ttsMs) {
        return (
            <div className="flex flex-col items-center justify-center w-full max-w-sm px-4 py-3 bg-white/5 rounded-xl border border-white/10 opacity-50 min-h-[100px] h-full">
                <span className="text-xs text-white/40 font-mono tracking-wide animate-pulse">Waiting for latency data...</span>
            </div>
        );
    }

    // Calculate percentages (cap at 100% just in case)
    const calcPerc = (val?: number) => {
        if (!val || !totalMs) return 0;
        return Math.min((val / totalMs) * 100, 100);
    };

    const isWarning = totalMs ? totalMs >= threshold && totalMs < threshold * 2 : false;
    const isError = totalMs ? totalMs >= threshold * 2 : false;

    let totalColor = "bg-green-500/60";
    let totalLabel = "✓ <" + (threshold / 1000).toFixed(1) + "s";
    let labelColor = "text-green-400";

    if (isWarning) {
        totalColor = "bg-yellow-500/60";
        totalLabel = "⚠ slow";
        labelColor = "text-yellow-400";
    } else if (isError) {
        totalColor = "bg-red-500/60";
        totalLabel = "⚠ very slow";
        labelColor = "text-red-400";
    }

    return (
        <div className="flex flex-col gap-2 w-full max-w-sm px-4 py-3 bg-white/5 rounded-xl border border-white/10">

            {/* Individual Stages */}
            <div className="flex flex-col gap-1.5">

                {/* STT Row */}
                {sttMs !== undefined && (
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-white/50 w-10 font-mono tracking-wide">STT</span>
                        <div className="flex-1 bg-black/40 h-1.5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-purple-600/40 rounded-full animate-bar-fill"
                                style={{
                                    width: `${calcPerc(sttMs)}%`,
                                    // No delay for first item
                                }}
                            />
                        </div>
                        <span className="text-xs text-white/30 w-12 text-right font-mono">{sttMs}ms</span>
                    </div>
                )}

                {/* LLM/Agent Row */}
                {llmMs !== undefined && (
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-white/50 w-10 font-mono tracking-wide">LLM</span>
                        <div className="flex-1 bg-black/40 h-1.5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-purple-600/40 rounded-full animate-bar-fill"
                                style={{
                                    width: `${calcPerc(llmMs)}%`,
                                    animationDelay: '150ms'
                                }}
                            />
                        </div>
                        <span className="text-xs text-white/30 w-12 text-right font-mono">{llmMs}ms</span>
                    </div>
                )}

                {/* TTS Row */}
                {ttsMs !== undefined && (
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-white/50 w-10 font-mono tracking-wide">TTS</span>
                        <div className="flex-1 bg-black/40 h-1.5 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-purple-600/40 rounded-full animate-bar-fill"
                                style={{
                                    width: `${calcPerc(ttsMs)}%`,
                                    animationDelay: '300ms'
                                }}
                            />
                        </div>
                        <span className="text-xs text-white/30 w-12 text-right font-mono">{ttsMs}ms</span>
                    </div>
                )}

            </div>

            {/* Total Separator */}
            <div className="h-px w-full bg-white/10 my-0.5" />

            {/* Total Row */}
            {totalMs !== undefined && (
                <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-white/80 w-10 font-mono font-bold tracking-wide">TOT</span>
                    <div className="flex-1 bg-black/40 h-2 rounded-full overflow-hidden">
                        <div
                            className={`h-full rounded-full ${totalColor} animate-bar-fill`}
                            style={{
                                width: '100%',
                                animationDelay: '450ms'
                            }}
                        />
                    </div>
                    <div className="flex flex-col items-end w-12">
                        <span className="text-xs text-white/80 font-mono font-bold">{totalMs}ms</span>
                        <span className={`text-[9px] ${labelColor} font-mono leading-none mt-0.5`}>{totalLabel}</span>
                    </div>
                </div>
            )}

        </div>
    );
}
