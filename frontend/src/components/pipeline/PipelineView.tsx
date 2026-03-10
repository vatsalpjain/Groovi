import { usePipelineState } from '../../hooks/usePipelineState';
import { StateBadge } from './StateBadge';
import { PipelineNode } from './PipelineNode';
import { SignalWire } from './SignalWire';
import { LatencyBar } from './LatencyBar';
import { AgentStarView } from './AgentStarView';

import {
    FaWaveSquare,
    FaFont,
    FaRobot,
    FaVolumeUp,
    FaBroadcastTower
} from 'react-icons/fa';

export interface PipelineViewProps {
    isOpen: boolean;
    onToggle: () => void;
}

export function PipelineView({ isOpen, onToggle }: PipelineViewProps) {
    const {
        currentState,
        nodeStates,
        nodeLatencies,
        wireStates,
        wirePayloads,
        iterations,
        activeTab,
        setActiveTab,
        isAgentDone,
        tokensBefore,
        tokensAfter,
        agentTotalMs,
        latency,
    } = usePipelineState();

    return (
        <div
            className={`fixed bottom-0 left-0 right-0 z-50 transform transition-transform duration-300 ease-out border-t border-purple-500/30 bg-black/80 backdrop-blur-md shadow-[0_-10px_40px_rgba(0,0,0,0.5)] flex flex-col items-center
      ${isOpen ? 'translate-y-0' : 'translate-y-full'}`}
            style={{ height: '55vh', minHeight: '380px', maxHeight: '600px' }}
        >
            {/* Close button */}
            <button
                onClick={onToggle}
                className="absolute top-4 right-6 text-white/50 hover:text-white transition-colors"
                aria-label="Close Systems View"
            >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>

            <div className="w-full max-w-6xl mx-auto px-4 py-6 flex flex-col h-full gap-4 overflow-hidden">

                {/* Zone 0: Tab switcher + StateBadge row */}
                <div className="flex items-center justify-center gap-4 flex-shrink-0">
                    {/* Tab pills */}
                    <div className="flex items-center bg-white/5 rounded-lg border border-white/10 p-0.5">
                        <button
                            onClick={() => setActiveTab('pipeline')}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all duration-200
                                ${activeTab === 'pipeline'
                                    ? 'bg-purple-600/40 text-purple-200 shadow-sm'
                                    : 'text-white/40 hover:text-white/60'
                                }`}
                        >
                            1 · Pipeline
                        </button>
                        <button
                            onClick={() => setActiveTab('agent')}
                            className={`px-3 py-1 text-xs font-medium rounded-md transition-all duration-200
                                ${activeTab === 'agent'
                                    ? 'bg-purple-600/40 text-purple-200 shadow-sm'
                                    : 'text-white/40 hover:text-white/60'
                                }`}
                        >
                            2 · Agent
                        </button>
                    </div>

                    <StateBadge state={currentState} />
                </div>

                {/* ═══════════════ TAB 1: Voice Pipeline ═══════════════ */}
                {activeTab === 'pipeline' && (
                    <>
                        {/* Node Graph */}
                        <div className="flex items-start justify-between w-full max-w-4xl mx-auto px-4 sm:px-12 flex-shrink-0 mt-2 overflow-x-auto custom-scrollbar pb-4">

                            <PipelineNode
                                id="wake"
                                label="WAKE"
                                icon={<FaBroadcastTower className="w-5 h-5 text-current opacity-80" />}
                                state={nodeStates.wake}
                            />

                            <SignalWire
                                from="wake"
                                to="vad"
                                state={wireStates['wake-vad']}
                            />

                            <PipelineNode
                                id="vad"
                                label="VAD"
                                icon={<FaWaveSquare className="w-5 h-5 text-current opacity-80" />}
                                state={nodeStates.vad}
                            />

                            <SignalWire
                                from="vad"
                                to="stt"
                                state={wireStates['vad-stt']}
                            />

                            <PipelineNode
                                id="stt"
                                label="STT"
                                icon={<FaFont className="w-5 h-5 text-current opacity-80" />}
                                state={nodeStates.stt}
                                latencyMs={nodeLatencies.stt}
                            />

                            <SignalWire
                                from="stt"
                                to="agent"
                                state={wireStates['stt-agent']}
                                payload={wirePayloads['stt-agent']}
                            />

                            <PipelineNode
                                id="agent"
                                label="AGENT"
                                icon={<FaRobot className="w-5 h-5 text-current opacity-80" />}
                                state={nodeStates.agent}
                                latencyMs={nodeLatencies.agent}
                            />

                            <SignalWire
                                from="agent"
                                to="tts"
                                state={wireStates['agent-tts']}
                                payload={wirePayloads['agent-tts']}
                            />

                            <PipelineNode
                                id="tts"
                                label="TTS"
                                icon={<FaVolumeUp className="w-5 h-5 text-current opacity-80" />}
                                state={nodeStates.tts}
                                latencyMs={nodeLatencies.tts}
                            />

                        </div>

                        {/* Latency — full width */}
                        <div className="flex-1 w-full max-w-3xl mx-auto flex items-start justify-center min-h-0">
                            <LatencyBar
                                sttMs={latency.sttMs}
                                llmMs={latency.llmMs}
                                ttsMs={latency.ttsMs}
                                totalMs={latency.totalMs}
                            />
                        </div>
                    </>
                )}

                {/* ═══════════════ TAB 2: Music Agent ═══════════════ */}
                {activeTab === 'agent' && (
                    <div className="flex-1 flex items-center justify-center min-h-0 overflow-hidden py-2">
                        <AgentStarView
                            iterations={iterations}
                            isComplete={isAgentDone}
                            totalTokensBefore={tokensBefore}
                            totalTokensAfter={tokensAfter}
                            totalMs={agentTotalMs}
                        />
                    </div>
                )}

            </div>
        </div>
    );
}
