import { useState, useRef, useCallback, useEffect } from 'react'
import { transcribeAudio, ApiError } from '../services/api'

export type RecordingState = 'idle' | 'recording' | 'transcribing'

interface AudioRecorderProps {
    onTranscriptReceived: (transcript: string) => void
    onError: (error: string) => void
    disabled?: boolean
    // Callback to notify parent of recording state changes
    onRecordingStateChange?: (state: RecordingState) => void
    // Optional custom render - if provided, use custom UI
    renderButton?: (props: {
        state: RecordingState
        onClick: () => void
        disabled: boolean
    }) => React.ReactNode
}

/**
 * AudioRecorder - Microphone recording with transcription
 * Uses MediaRecorder API → sends to /transcribe → returns text
 * 
 * Can render default button or accept custom render prop for AIOrb integration
 */
export function AudioRecorder({
    onTranscriptReceived,
    onError,
    disabled = false,
    onRecordingStateChange,
    renderButton
}: AudioRecorderProps) {
    const [recordingState, setRecordingState] = useState<RecordingState>('idle')

    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])

    // Notify parent of state changes
    useEffect(() => {
        onRecordingStateChange?.(recordingState)
    }, [recordingState, onRecordingStateChange])

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            })

            mediaRecorderRef.current = mediaRecorder
            audioChunksRef.current = []

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data)
                }
            }

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach(track => track.stop())
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
                await handleTranscription(audioBlob)
            }

            mediaRecorder.start()
            setRecordingState('recording')

        } catch (err) {
            console.error('Microphone access error:', err)
            onError('Microphone access denied. Please allow microphone access and try again.')
        }
    }, [onError])

    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && recordingState === 'recording') {
            mediaRecorderRef.current.stop()
            setRecordingState('transcribing')
        }
    }, [recordingState])

    const handleTranscription = async (audioBlob: Blob) => {
        try {
            const response = await transcribeAudio(audioBlob)
            onTranscriptReceived(response.transcript)
        } catch (err) {
            if (err instanceof ApiError) {
                onError(err.detail || 'Transcription failed')
            } else {
                onError('Failed to transcribe audio. Please try again.')
            }
            console.error('Transcription error:', err)
        } finally {
            setRecordingState('idle')
        }
    }

    // Handle click - toggle recording
    const handleClick = useCallback(() => {
        if (recordingState === 'idle') {
            startRecording()
        } else if (recordingState === 'recording') {
            stopRecording()
        }
    }, [recordingState, startRecording, stopRecording])

    // If custom render prop is provided, use it
    if (renderButton) {
        return <>{renderButton({ state: recordingState, onClick: handleClick, disabled })}</>
    }

    // Default button rendering (backwards compatible)
    if (recordingState === 'transcribing') {
        return (
            <button
                disabled
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl
                   bg-white/[0.05] border border-white/[0.08] text-zinc-400
                   cursor-not-allowed"
            >
                <span className="inline-block w-4 h-4 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" />
                Transcribing...
            </button>
        )
    }

    if (recordingState === 'recording') {
        return (
            <button
                onClick={stopRecording}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl
                   bg-red-500/20 border border-red-500/30 text-red-400
                   hover:bg-red-500/30 transition-all duration-300
                   animate-pulse"
            >
                <span className="text-base">⏹</span>
                Stop Recording
            </button>
        )
    }

    return (
        <button
            onClick={startRecording}
            disabled={disabled}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl
                 bg-zinc-100 dark:bg-white/[0.05] 
                 border border-zinc-200 dark:border-white/[0.08]
                 text-zinc-700 dark:text-zinc-300
                 hover:bg-zinc-200 dark:hover:bg-white/[0.1]
                 transition-all duration-300
                 disabled:opacity-40 disabled:cursor-not-allowed"
        >
            <span className="text-base">🎤</span>
            Start Recording
        </button>
    )
}
