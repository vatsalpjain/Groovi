

export interface PipelineNodeProps {
    id: 'wake' | 'vad' | 'stt' | 'agent' | 'tts';
    label: string;
    icon: React.ReactNode;
    state: 'idle' | 'active' | 'done' | 'error';
    latencyMs?: number;
}

export function PipelineNode({ label, icon, state, latencyMs }: PipelineNodeProps) {
    // Base circle styles
    const baseCircle = "relative flex items-center justify-center w-14 h-14 rounded-full transition-all duration-300";

    // State-specific styles
    let circleStyle = "";
    let iconOpacity = "";

    switch (state) {
        case 'idle':
            circleStyle = "bg-white/5 border border-purple-900/40 opacity-80 animate-[pulse_3s_ease-in-out_infinite]";
            iconOpacity = "opacity-40";
            break;
        case 'active':
            circleStyle = "bg-purple-900/30 border border-purple-400";
            iconOpacity = "opacity-100";
            break;
        case 'done':
            circleStyle = "bg-white/5 border border-green-500/60";
            iconOpacity = "opacity-60";
            break;
        case 'error':
            circleStyle = "bg-red-900/20 border border-red-500/60";
            iconOpacity = "opacity-40";
            break;
    }

    return (
        <div className="flex flex-col items-center">
            {/* Node Circle */}
            <div
                className={`${baseCircle} ${circleStyle}`}
                style={state === 'active' ? { boxShadow: '0 0 20px rgba(139, 92, 246, 0.7)' } : undefined}
            >
                {/* Active Spinner */}
                {state === 'active' && (
                    <div className="absolute inset-0 rounded-full border-t-2 border-purple-400 animate-spin" />
                )}

                {/* Icon */}
                <div className={`transition-opacity duration-300 ${iconOpacity} flex items-center justify-center text-white text-xl`}>
                    {icon}
                </div>

                {/* Done / Error Badges */}
                {state === 'done' && (
                    <div className="absolute -top-1 -right-1 bg-green-500 rounded-full w-4 h-4 flex items-center justify-center border border-black z-10">
                        <svg className="w-2.5 h-2.5 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                )}

                {state === 'error' && (
                    <div className="absolute -top-1 -right-1 bg-red-500 rounded-full w-4 h-4 flex items-center justify-center border border-black z-10">
                        <span className="text-black text-[10px] font-bold leading-none">!</span>
                    </div>
                )}
            </div>

            {/* Label and Latency */}
            <div className="mt-2 text-center h-10 flex flex-col items-center justify-start">
                <span className="text-xs text-white/50 font-medium tracking-wide">
                    {label}
                </span>
                {state === 'done' && latencyMs !== undefined && (
                    <span className="text-xs text-white/30 mt-0.5 font-mono">
                        {latencyMs}ms
                    </span>
                )}
            </div>
        </div>
    );
}
