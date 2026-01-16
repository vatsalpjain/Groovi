/**
 * useAudioCapture - Raw PCM Audio Capture Hook
 * 
 * Uses AudioWorklet to capture raw PCM audio at 16kHz, 16-bit mono.
 * This format is required by:
 * - OpenWakeWord (wake word detection)
 * - Faster-Whisper (speech-to-text)
 * - Silero VAD (voice activity detection)
 */

import { useState, useRef, useCallback, useEffect } from 'react'

// Target sample rate for voice models
const TARGET_SAMPLE_RATE = 16000
// VAD requires exactly 512 samples at 16kHz (32ms chunks)
const VAD_CHUNK_SIZE = 512

interface UseAudioCaptureOptions {
  onAudioChunk?: (chunk: ArrayBuffer) => void
  onError?: (error: string) => void
}

export function useAudioCapture(options: UseAudioCaptureOptions = {}) {
  const { onAudioChunk, onError } = options

  const [isCapturing, setIsCapturing] = useState(false)
  const [isReady, setIsReady] = useState(false)
  
  const audioContextRef = useRef<AudioContext | null>(null)
  const workletNodeRef = useRef<AudioWorkletNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  
  // Accumulator for samples to create proper chunk sizes
  const sampleAccumulatorRef = useRef<Int16Array>(new Int16Array(0))

  // Use refs for callbacks to keep functions stable
  const onAudioChunkRef = useRef(onAudioChunk)
  const onErrorRef = useRef(onError)
  
  useEffect(() => {
    onAudioChunkRef.current = onAudioChunk
    onErrorRef.current = onError
  }, [onAudioChunk, onError])

  // Downsample audio from native rate (48kHz) to 16kHz
  const downsample = useCallback((buffer: Int16Array, fromRate: number): Int16Array => {
    if (fromRate === TARGET_SAMPLE_RATE) {
      return buffer
    }

    const ratio = fromRate / TARGET_SAMPLE_RATE
    const newLength = Math.floor(buffer.length / ratio)
    const result = new Int16Array(newLength)

    for (let i = 0; i < newLength; i++) {
      const sourceIndex = Math.floor(i * ratio)
      result[i] = buffer[sourceIndex]
    }

    return result
  }, [])

  // Process samples: accumulate and emit VAD-sized chunks
  const processSamples = useCallback((samples: Int16Array) => {
    // Append new samples to accumulator
    const combined = new Int16Array(sampleAccumulatorRef.current.length + samples.length)
    combined.set(sampleAccumulatorRef.current)
    combined.set(samples, sampleAccumulatorRef.current.length)
    
    // Emit complete chunks of VAD_CHUNK_SIZE
    let offset = 0
    while (offset + VAD_CHUNK_SIZE <= combined.length) {
      const chunk = combined.slice(offset, offset + VAD_CHUNK_SIZE)
      onAudioChunkRef.current?.(chunk.buffer as ArrayBuffer)
      offset += VAD_CHUNK_SIZE
    }
    
    // Keep remaining samples for next batch
    sampleAccumulatorRef.current = combined.slice(offset)
  }, [])

  // Start capturing audio
  const startCapture = useCallback(async () => {
    if (isCapturing) return

    try {
      // Reset accumulator
      sampleAccumulatorRef.current = new Int16Array(0)
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: { ideal: 48000 }
        }
      })
      streamRef.current = stream

      // Create AudioContext
      const audioContext = new AudioContext({ sampleRate: 48000 })
      audioContextRef.current = audioContext

      // Load AudioWorklet processor
      await audioContext.audioWorklet.addModule('/audio-processor.js')
      setIsReady(true)

      // Create worklet node
      const workletNode = new AudioWorkletNode(audioContext, 'audio-capture-processor')
      workletNodeRef.current = workletNode

      // Handle audio from worklet
      workletNode.port.onmessage = (event) => {
        if (event.data.type === 'audio') {
          const rawBuffer = new Int16Array(event.data.buffer)
          const sampleRate = event.data.sampleRate
          
          // Downsample to 16kHz
          const downsampled = downsample(rawBuffer, sampleRate)
          
          // Process into VAD-sized chunks
          processSamples(downsampled)
        }
      }

      // Connect microphone to worklet
      const source = audioContext.createMediaStreamSource(stream)
      sourceRef.current = source
      source.connect(workletNode)
      
      // Don't connect to destination (we don't want to play back)
      // workletNode.connect(audioContext.destination)

      setIsCapturing(true)
      console.log('🎤 Audio capture started (16kHz PCM, 512 samples/chunk)')

    } catch (err) {
      console.error('Audio capture error:', err)
      onErrorRef.current?.('Microphone access denied')
      setIsCapturing(false)
    }
  }, [isCapturing, downsample, processSamples])

  // Stop capturing audio
  const stopCapture = useCallback(() => {
    // Disconnect worklet
    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }

    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect()
      workletNodeRef.current = null
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
      streamRef.current = null
    }

    setIsCapturing(false)
    setIsReady(false)
    console.log('🎤 Audio capture stopped')
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCapture()
    }
  }, [stopCapture])

  return {
    isCapturing,
    isReady,
    startCapture,
    stopCapture
  }
}
