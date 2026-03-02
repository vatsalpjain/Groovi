import { useMemo } from 'react';
import type { PipelineState } from '../../hooks/usePipelineState';

interface StateBadgeProps {
    state: PipelineState['currentState'];
}

export function StateBadge({ state }: StateBadgeProps) {
    const { label, colorClasses, dotClasses } = useMemo(() => {
        switch (state) {
            case 'LOADING':
                return {
                    label: 'Loading Models...',
                    colorClasses: 'text-amber-300 bg-amber-900/30 border-amber-500/40',
                    dotClasses: 'animate-pulse',
                };
            case 'WAKE_WORD':
                return {
                    label: 'Listening for "Hey Groovi"',
                    colorClasses: 'text-white/40 bg-white/5 border-white/10',
                    dotClasses: 'animate-[pulse_2s_ease-in-out_infinite]',
                };
            case 'LISTENING':
                return {
                    label: 'Listening',
                    colorClasses: 'text-blue-300 bg-blue-900/30 border-blue-500/40',
                    dotClasses: 'animate-pulse',
                };
            case 'PROCESSING':
                return {
                    label: 'Processing',
                    colorClasses: 'text-purple-300 bg-purple-900/30 border-purple-500/40',
                    dotClasses: 'animate-pulse',
                };
            case 'SPEAKING':
                return {
                    label: 'Speaking',
                    colorClasses: 'text-green-300 bg-green-900/30 border-green-500/40',
                    dotClasses: 'animate-pulse',
                };
            case 'ERROR':
                return {
                    label: 'Fallback Active',
                    colorClasses: 'text-yellow-300 bg-yellow-900/30 border-yellow-500/40',
                    dotClasses: 'animate-pulse',
                };
            default:
                return {
                    label: state,
                    colorClasses: 'text-white/40 bg-white/5 border-white/10',
                    dotClasses: '',
                };
        }
    }, [state]);

    return (
        <div
            className={`
        rounded-full px-4 py-1.5 text-sm border font-mono tracking-wide
        transition-colors duration-300 delay-100
        ${colorClasses}
      `}
        >
            <span className={`inline-block mr-2 ${dotClasses}`}>●</span>
            {label}
        </div>
    );
}
