import { useEffect, useRef, useState, useCallback } from 'react';

export interface AgentIteration {
  index: number;
  tool: string;
  args: Record<string, string>;
  resultSummary: string;
  latencyMs: number;
  status: 'running' | 'done';
  tokensBefore?: number;  // Per-call raw chars from MCP result
  tokensAfter?: number;   // Per-call truncated chars sent to LLM
}

export interface PipelineState {
  // State machine
  currentState: 'LOADING' | 'WAKE_WORD' | 'LISTENING' | 'PROCESSING' | 'SPEAKING' | 'ERROR';
  
  // Node states — no MIC node; WAKE connects directly to VAD
  nodeStates: Record<'wake' | 'vad' | 'stt' | 'agent' | 'tts', 'idle' | 'active' | 'done' | 'error'>;
  nodeLatencies: Record<'stt' | 'agent' | 'tts', number | undefined>;
  
  // Wire states — wake-vad replaces the old wake-mic + mic-vad pair
  wireStates: Record<'wake-vad' | 'vad-stt' | 'stt-agent' | 'agent-tts', 'idle' | 'transmitting' | 'done'>;
  wirePayloads: Record<'stt-agent' | 'agent-tts', string | undefined>;
  
  // Agent log
  iterations: AgentIteration[];
  isAgentDone: boolean;
  tokensBefore?: number;
  tokensAfter?: number;
  agentTotalMs?: number;
  
  // Latency
  latency: {
    sttMs?: number;
    llmMs?: number;
    ttsMs?: number;
    totalMs?: number;
  };
  
  // Tab control — auto-swaps to 'agent' on first agent_iteration
  activeTab: 'pipeline' | 'agent';
  setActiveTab: (tab: 'pipeline' | 'agent') => void;
  
  // Utility
  resetPipeline: () => void;
}

const defaultNodeStates: PipelineState['nodeStates'] = {
  wake: 'idle',
  vad: 'idle',
  stt: 'idle',
  agent: 'idle',
  tts: 'idle',
};

const defaultWireStates: PipelineState['wireStates'] = {
  'wake-vad': 'idle',
  'vad-stt': 'idle',
  'stt-agent': 'idle',
  'agent-tts': 'idle',
};

const defaultWirePayloads: PipelineState['wirePayloads'] = {
  'stt-agent': undefined,
  'agent-tts': undefined,
};

export function usePipelineState(): PipelineState {
  const [currentState, setCurrentState] = useState<PipelineState['currentState']>('WAKE_WORD');
  const [nodeStates, setNodeStates] = useState<PipelineState['nodeStates']>(defaultNodeStates);
  const [nodeLatencies, setNodeLatencies] = useState<PipelineState['nodeLatencies']>({ stt: undefined, agent: undefined, tts: undefined });
  const [wireStates, setWireStates] = useState<PipelineState['wireStates']>(defaultWireStates);
  const [wirePayloads, setWirePayloads] = useState<PipelineState['wirePayloads']>(defaultWirePayloads);
  
  const [iterations, setIterations] = useState<AgentIteration[]>([]);
  const [isAgentDone, setIsAgentDone] = useState(false);
  const [tokensBefore, setTokensBefore] = useState<number | undefined>();
  const [tokensAfter, setTokensAfter] = useState<number | undefined>();
  const [agentTotalMs, setAgentTotalMs] = useState<number | undefined>();
  
  const [latency, setLatency] = useState<PipelineState['latency']>({});
  const [activeTab, setActiveTab] = useState<'pipeline' | 'agent'>('pipeline');

  // Refs for precise timing so we don't trigger extra re-renders
  const timestamps = useRef({
    listenStart: 0,
    sttDone: 0,
    agentStart: 0,
    agentDone: 0,
    ttsStart: 0,
  });

  const resetPipeline = useCallback(() => {
    setCurrentState('WAKE_WORD');
    setNodeStates(defaultNodeStates);
    setNodeLatencies({ stt: undefined, agent: undefined, tts: undefined });
    setWireStates(defaultWireStates);
    setWirePayloads(defaultWirePayloads);
    setIterations([]);
    setIsAgentDone(false);
    setTokensBefore(undefined);
    setTokensAfter(undefined);
    setAgentTotalMs(undefined);
    setLatency({});
    setActiveTab('pipeline');
  }, []);

  useEffect(() => {

    const handleMessage = (event: Event) => {
      try {
        const customEvent = event as CustomEvent;
        const data = customEvent.detail;
        console.log('[Pipeline State] Received event:', data.event, data);

        switch (data.event) {

          // ── Startup ────────────────────────────────────────────────────
          case 'loading':
            // Models are spinning up — amber badge, all nodes idle
            setCurrentState('LOADING');
            break;

          case 'ready':
            // Full reset, then immediately mark WAKE as active to signal
            // that wake-word detection is live and the mic is hot
            resetPipeline();
            setNodeStates(prev => ({ ...prev, wake: 'active' }));
            break;

          // ── Listening phase ────────────────────────────────────────────
          case 'wake_word_detected':
            setCurrentState('LISTENING');
            // WAKE done, wire pulses to VAD, VAD becomes active
            setNodeStates(prev => ({ ...prev, wake: 'done', vad: 'active' }));
            setWireStates(prev => ({ ...prev, 'wake-vad': 'transmitting' }));
            timestamps.current.listenStart = Date.now();
            setTimeout(() => {
              setWireStates(prev => ({ ...prev, 'wake-vad': 'done' }));
            }, 600);
            break;

          case 'listening':
            // Sent after tts_complete for a normal (non-music) response —
            // VAD reactivates so the user can speak a follow-up
            setNodeStates(prev => ({ ...prev, vad: 'active' }));
            setWireStates(prev => ({ ...prev, 'vad-stt': 'transmitting' }));
            break;

          // ── STT ────────────────────────────────────────────────────────
          case 'transcript': {
            // Use backend-provided STT processing time (Whisper only, excludes speaking)
            const sttTime = data.sttMs || 0;
            timestamps.current.sttDone = Date.now();
            timestamps.current.agentStart = Date.now();
            
            setNodeStates(prev => ({ ...prev, vad: 'done', stt: 'active' }));
            setNodeLatencies(prev => ({ ...prev, stt: sttTime }));
            setWireStates(prev => ({ ...prev, 'vad-stt': 'done', 'stt-agent': 'transmitting' }));
            setWirePayloads(prev => ({ ...prev, 'stt-agent': data.text }));
            setCurrentState('PROCESSING');
            
            // Animate STT → done, AGENT → active after wire shimmer
            setTimeout(() => {
              setWireStates(prev => ({ ...prev, 'stt-agent': 'done' }));
              setNodeStates(prev => ({ ...prev, stt: 'done', agent: 'active' }));
            }, 600);
            
            setLatency(prev => ({ ...prev, sttMs: sttTime }));
            break;
          }

          // ── Agent ──────────────────────────────────────────────────────
          case 'processing':
            setCurrentState('PROCESSING');
            setNodeStates(prev => ({ ...prev, agent: 'active' }));
            break;

          case 'agent_iteration':
            // Auto-switch to agent tab on the very first iteration
            setActiveTab(prev => prev === 'pipeline' ? 'agent' : prev);
            setIterations(prev => [
              ...prev,
              {
                index: data.iteration,
                tool: data.tool,
                args: data.args || {},
                resultSummary: `${data.resultCount} results`,
                latencyMs: data.latencyMs,
                status: 'done',
                tokensBefore: data.tokensBefore,  // Per-call raw chars
                tokensAfter: data.tokensAfter,     // Per-call truncated chars
              }
            ]);
            break;

          case 'response_text': {
            // Surface the first sentence on the agent→tts wire label
            const firstSentence = (data.text || '').split(/[.!?]/)[0] + '.';
            setWirePayloads(prev => ({ ...prev, 'agent-tts': firstSentence }));
            break;
          }

          case 'agent_complete': {
            const agentTotalTime = data.totalMs || (Date.now() - timestamps.current.agentStart);
            timestamps.current.agentDone = Date.now();
            
            setIsAgentDone(true);
            setTokensBefore(data.tokensBefore);
            setTokensAfter(data.tokensAfter);
            setAgentTotalMs(agentTotalTime);
            setNodeLatencies(prev => ({ ...prev, agent: agentTotalTime }));
            setLatency(prev => ({ ...prev, llmMs: agentTotalTime }));
            break;
          }

          // ── TTS ────────────────────────────────────────────────────────
          case 'tts_start':
            // Dedicated JSON event fired BEFORE binary audio bytes.
            // Binary frames bypass voice-ws-message, so this is the only
            // reliable signal to drive the TTS node state.
            setCurrentState('SPEAKING');
            setNodeStates(prev => ({ ...prev, agent: 'done', tts: 'active' }));
            setWireStates(prev => ({ ...prev, 'agent-tts': 'transmitting' }));
            setTimeout(() => {
              setWireStates(prev => ({ ...prev, 'agent-tts': 'done' }));
            }, 600);
            break;

          // ── TTS done (actual synthesis time from backend) ─────────────
          case 'tts_done': {
            // Backend sends actual Piper TTS synthesis time (excludes playback)
            const ttsTime = data.ttsMs || 0;
            setNodeLatencies(prev => ({ ...prev, tts: ttsTime }));
            setLatency(prev => {
              const updated = { ...prev, ttsMs: ttsTime };
              // Compute total as sum of STT + LLM + TTS
              if (updated.sttMs !== undefined && updated.llmMs !== undefined) {
                updated.totalMs = updated.sttMs + updated.llmMs + ttsTime;
              }
              return updated;
            });
            break;
          }

          // ── Songs result ───────────────────────────────────────────────
          case 'songs': {
            // Mark TTS node as done (latency already set by tts_done event)
            setNodeStates(prev => ({ ...prev, tts: 'done' }));
            setIsAgentDone(true);
            // Keep SPEAKING so the badge reads correctly until music_playing fires
            break;
          }

          case 'music_playing':
            // Backend has queued the songs and returned to WAKE_WORD mode.
            // Loop the pipeline back: WAKE node reactivates, badge resets.
            setCurrentState('WAKE_WORD');
            setNodeStates(prev => ({ ...prev, wake: 'active' }));
            break;

          // Normal (non-music) chat completed — TTS latency already set by tts_done
          case 'response_complete': {
            setNodeStates(prev => ({ ...prev, tts: 'done' }));
            // Compute total if we don't have it yet (STT + LLM + TTS)
            setLatency(prev => {
              const updated = { ...prev };
              if (updated.totalMs === undefined && updated.sttMs !== undefined && updated.llmMs !== undefined && updated.ttsMs !== undefined) {
                updated.totalMs = updated.sttMs + updated.llmMs + updated.ttsMs;
              }
              return updated;
            });
            setCurrentState('WAKE_WORD');
            setNodeStates(prev => ({ ...prev, wake: 'active' }));
            break;
          }

          // ── Error / Fallback ───────────────────────────────────────────
          case 'error':
            setCurrentState('ERROR');
            setNodeStates(prev => ({ ...prev, agent: 'error' }));
            break;
        }
      } catch (err) {
        // Ignored
      }
    };

    window.addEventListener('voice-ws-message', handleMessage);
    return () => {
      window.removeEventListener('voice-ws-message', handleMessage);
    };
  }, [resetPipeline]);

  return {
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
    resetPipeline
  };
}
