/**
 * useVoiceWebSocket - WebSocket hook for continuous voice connection
 * 
 * Provides:
 * - Persistent WebSocket connection to /ws/voice
 * - Send audio chunks continuously
 * - Receive events (transcript, songs, audio)
 */

import { useState, useRef, useCallback, useEffect } from 'react'

// WebSocket URL
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:5000/ws/voice'

export type ConnectionState = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface VoiceEvent {
  event: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any
}

interface UseVoiceWebSocketOptions {
  onMessage?: (event: VoiceEvent) => void
  onAudio?: (audioData: Blob) => void
  onError?: (error: string) => void
  onConnectionChange?: (state: ConnectionState) => void
}

export function useVoiceWebSocket(options: UseVoiceWebSocketOptions = {}) {
  const { onMessage, onAudio, onError, onConnectionChange } = options

  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  
  // Use refs for callbacks to keep connect/disconnect stable
  const onMessageRef = useRef(onMessage)
  const onAudioRef = useRef(onAudio)
  const onErrorRef = useRef(onError)
  const onConnectionChangeRef = useRef(onConnectionChange)
  
  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage
    onAudioRef.current = onAudio
    onErrorRef.current = onError
    onConnectionChangeRef.current = onConnectionChange
  }, [onMessage, onAudio, onError, onConnectionChange])

  // Update connection state and notify parent
  const updateConnectionState = useCallback((state: ConnectionState) => {
    setConnectionState(state)
    onConnectionChangeRef.current?.(state)
  }, [])

  // Connect to WebSocket
  const connect = useCallback(() => {
    // Don't create new connection if already connected or connecting
    if (wsRef.current?.readyState === WebSocket.OPEN || 
        wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('🔌 WebSocket already connecting/connected')
      return // Already connected or connecting
    }

    updateConnectionState('connecting')

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('🔌 WebSocket connected')
        updateConnectionState('connected')
      }

      ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
          // Binary data = TTS audio
          onAudioRef.current?.(event.data)
        } else {
          // JSON event
          try {
            const data = JSON.parse(event.data) as VoiceEvent
            onMessageRef.current?.(data)
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err)
          }
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        updateConnectionState('error')
        onErrorRef.current?.('WebSocket connection error')
      }

      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected')
        updateConnectionState('disconnected')
        wsRef.current = null
      }

    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      updateConnectionState('error')
      onErrorRef.current?.('Failed to connect to voice server')
    }
  }, [updateConnectionState])  // Only depends on stable updateConnectionState

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    updateConnectionState('disconnected')
  }, [updateConnectionState])

  // Send audio chunk (binary)
  const sendAudio = useCallback((audioData: Blob | ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData)
    }
  }, [])

  // Send JSON message
  const sendMessage = useCallback((message: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    connect,
    disconnect,
    sendAudio,
    sendMessage,
  }
}
