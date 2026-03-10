

export interface LatencyBarProps {
    sttMs?: number;
    llmMs?: number;
    ttsMs?: number;
    totalMs?: number;
    threshold?: number; // default 1100
}

/** Format milliseconds as seconds: 52677 → "52.68s", 760 → "0.76s" */
function fmtSec(ms?: number): string {
    if (ms === undefined) return '—';
    return (ms / 1000).toFixed(2) + 's';
}

export function LatencyBar({
    sttMs,
    llmMs,
    ttsMs,
    totalMs,
    threshold = 1100
}: LatencyBarProps) {

    const hasAny = totalMs !== undefined || sttMs !== undefined || llmMs !== undefined || ttsMs !== undefined;

    // Calculate bar width proportional to total
    const calcPerc = (val?: number) => {
        if (!val || !totalMs) return 0;
        return Math.min((val / totalMs) * 100, 100);
    };

    // Total status
    const isWarning = totalMs ? totalMs >= threshold && totalMs < threshold * 2 : false;
    const isError = totalMs ? totalMs >= threshold * 2 : false;

    let totalColor = 'bg-green-500/60';
    let totalLabel = '✓ fast';
    let labelColor = 'text-green-400';

    if (isError) {
        totalColor = 'bg-red-500/60';
        totalLabel = '⚠ very slow';
        labelColor = 'text-red-400';
    } else if (isWarning) {
        totalColor = 'bg-yellow-500/60';
        totalLabel = '⚠ slow';
        labelColor = 'text-yellow-400';
    }

    // Reusable bar row — always renders, shows empty bar if no data
    const BarRow = ({
        label,
        value,
        color,
        delay,
        bold,
        statusLabel,
        statusColor,
    }: {
        label: string;
        value?: number;
        color: string;
        delay: string;
        bold?: boolean;
        statusLabel?: string;
        statusColor?: string;
    }) => {
        const hasValue = value !== undefined;
        return (
            <div className="flex items-center gap-2">
                <span className={`text-xs w-10 font-mono tracking-wide ${bold ? 'text-white/80 font-bold' : 'text-white/50'}`}>
                    {label}
                </span>
                <div className={`flex-1 bg-black/40 ${bold ? 'h-2' : 'h-1.5'} rounded-full overflow-hidden`}>
                    {hasValue && (
                        <div
                            className={`h-full ${color} rounded-full animate-bar-fill`}
                            style={{ width: bold ? '100%' : `${calcPerc(value)}%`, animationDelay: delay }}
                        />
                    )}
                </div>
                <div className="flex flex-col items-end min-w-[56px]">
                    <span className={`text-xs font-mono ${hasValue ? (bold ? 'text-white/80 font-bold' : 'text-white/30') : 'text-white/15'}`}>
                        {fmtSec(value)}
                    </span>
                    {statusLabel && (
                        <span className={`text-[9px] ${statusColor} font-mono leading-none mt-0.5`}>{statusLabel}</span>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="w-full px-5 py-4 bg-white/5 rounded-xl border border-white/10">

            {!hasAny && (
                <div className="flex items-center justify-center py-2">
                    <span className="text-xs text-white/40 font-mono tracking-wide animate-pulse">Waiting for latency data...</span>
                </div>
            )}

            {/* 2-column grid: STT + TTS left, LLM + Total right */}
            <div className="grid grid-cols-2 gap-x-6 gap-y-3">

                {/* Column 1 */}
                <div className="flex flex-col gap-2.5">
                    <BarRow label="STT" value={sttMs} color="bg-purple-600/40" delay="0ms" />
                    <BarRow label="TTS" value={ttsMs} color="bg-purple-600/40" delay="200ms" />
                </div>

                {/* Column 2 */}
                <div className="flex flex-col gap-2.5">
                    <BarRow label="LLM" value={llmMs} color="bg-purple-600/40" delay="100ms" />
                    <div>
                        <div className="h-px w-full bg-white/10 mb-2" />
                        <BarRow
                            label="TOT"
                            value={totalMs}
                            color={totalColor}
                            delay="300ms"
                            bold
                            statusLabel={totalMs !== undefined ? totalLabel : undefined}
                            statusColor={labelColor}
                        />
                    </div>
                </div>

            </div>
        </div>
    );
}
