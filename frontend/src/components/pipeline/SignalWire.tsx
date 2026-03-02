import { useEffect, useState } from 'react';

export interface SignalWireProps {
    from: 'wake' | 'vad' | 'stt' | 'agent';
    to: 'vad' | 'stt' | 'agent' | 'tts';
    state: 'idle' | 'transmitting' | 'done';
    payload?: string; // the actual text to animate along the wire
}

export function SignalWire({ from, to, state, payload }: SignalWireProps) {
    // We use this local state to trigger the animation re-render reliably
    const [isAnimating, setIsAnimating] = useState(false);

    useEffect(() => {
        if (state === 'transmitting') {
            setIsAnimating(true);
            // The animation duration is defined in index.css as 600ms
            const timer = setTimeout(() => setIsAnimating(false), 600);
            return () => clearTimeout(timer);
        } else {
            setIsAnimating(false);
        }
    }, [state]);

    // Determine line style based on state
    let background = "linear-gradient(to right, rgba(139,92,246,0.3), rgba(139,92,246,0.3))";
    let baseStyles = "absolute top-1/2 -translate-y-1/2 left-0 right-0 h-[1px] transition-all duration-300";

    if (state === 'transmitting' || state === 'done') {
        background = "linear-gradient(to right, rgba(139,92,246,0.8), rgba(139,92,246,0.8))";
        baseStyles += " shadow-[0_0_10px_rgba(139,92,246,0.6)]";
    }

    // Determine what text to show on this specific wire (fallback to payload)
    const defaultText = (() => {
        if (from === 'wake' && to === 'vad') return "detected!";
        if (from === 'vad' && to === 'stt') return "speech confirmed";
        return payload || "";
    })();

    const textToShow = payload || defaultText;

    return (
        <div className="flex-1 px-2 relative flex items-center justify-center min-w-[60px] max-w-[120px] h-14">

            {/* Base Wire Line */}
            <div className={baseStyles} style={{ background }} />

            {/* Shimmer Effect (Idle -> Transmitting) */}
            {state === 'transmitting' && (
                <div className="absolute inset-x-2 h-px bg-gradient-to-r from-transparent via-white to-transparent animate-shimmer" />
            )}

            {/* Flowing Text Animation */}
            {isAnimating && textToShow && (
                <div className="absolute left-0 animate-wire-flow whitespace-nowrap">
                    <span className="text-[10px] text-purple-300 font-mono tracking-tight drop-shadow-[0_0_8px_rgba(168,85,247,0.8)]">
                        {textToShow}
                    </span>
                </div>
            )}

        </div>
    );
}
