import { useState, useRef } from 'react'
import { transcribeAudio, ApiError } from '../services/api'

interface AudioRecorderProps {
    onTranscriptReceived: (transcript: string) => void
    onError: (error: string) => void
    disabled?: boolean
}

/**
 * AudioRecorder - Microphone recording with transcription
 * Uses MediaRecorder API → sends to /transcribe → returns text
 */
export function AudioRecorder({ onTranscriptReceived, onError, disabled }: AudioRecorderProps) {
    const [isRecording, setIsRecording] = useState(false)
    const [isTranscribing, setIsTranscribing] = useState(false)

    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])

    const startRecording = async () => {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

            // Create MediaRecorder with webm format (widely supported)
            const mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            })

            mediaRecorderRef.current = mediaRecorder
            audioChunksRef.current = []

            // Collect audio chunks
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data)
                }
            }

            // When recording stops, process the audio
            mediaRecorder.onstop = async () => {
                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop())

                // Create blob from chunks
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })

                // Send to backend for transcription
                await handleTranscription(audioBlob)
            }

            // Start recording
            mediaRecorder.start()
            setIsRecording(true)

        } catch (err) {
            console.error('Microphone access error:', err)
            onError('Microphone access denied. Please allow microphone access and try again.')
        }
    }

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop()
            setIsRecording(false)
        }
    }

    const handleTranscription = async (audioBlob: Blob) => {
        setIsTranscribing(true)

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
            setIsTranscribing(false)
        }
    }

    // Button states: idle → recording (pulse) → transcribing
    if (isTranscribing) {
        return (
            <button
                disabled
                className="flex items-center gap-2 px-4 py-2 rounded-lg
                   bg-zinc-200 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400
                   cursor-not-allowed"
            >
                <span className="inline-block w-4 h-4 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
                Transcribing...
            </button>
        )
    }

    if (isRecording) {
        return (
            <button
                onClick={stopRecording}
                className="flex items-center gap-2 px-4 py-2 rounded-lg
                   bg-red-500 text-white hover:bg-red-600 transition-colors
                   animate-pulse"
            >
                <span className="text-lg">⏹️</span>
                Stop Recording
            </button>
        )
    }

    return (
        <button
            onClick={startRecording}
            disabled={disabled}
            className="flex items-center gap-2 px-4 py-2 rounded-lg
                 bg-zinc-100 dark:bg-zinc-800 
                 text-zinc-700 dark:text-zinc-300
                 hover:bg-zinc-200 dark:hover:bg-zinc-700 
                 transition-colors
                 disabled:opacity-50 disabled:cursor-not-allowed"
        >
            <span className="text-lg">🎤</span>
            Start Recording
        </button>
    )
}
