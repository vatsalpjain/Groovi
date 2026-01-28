import { useState, useRef } from 'react'
import { synthesizeSpeech, ApiError } from '../services/api'

interface TTSButtonProps {
    text: string
    disabled?: boolean
}

/**
 * TTSButton - Text-to-Speech playback button
 * Calls /synthesize endpoint and plays the returned audio
 */
export function TTSButton({ text, disabled }: TTSButtonProps) {
    const [isLoading, setIsLoading] = useState(false)
    const [isPlaying, setIsPlaying] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const audioRef = useRef<HTMLAudioElement | null>(null)

    const handleClick = async () => {
        // If already playing, stop it
        if (isPlaying && audioRef.current) {
            audioRef.current.pause()
            audioRef.current.currentTime = 0
            setIsPlaying(false)
            return
        }

        if (!text.trim() || isLoading) return

        console.log('🔊 TTS: Starting synthesis for:', text.substring(0, 50) + '...')
        setIsLoading(true)
        setError(null)

        try {
            // Get audio blob from backend
            console.log('📡 TTS: Calling API...')
            const audioBlob = await synthesizeSpeech(text)
            console.log('✅ TTS: Received audio blob:', audioBlob.size, 'bytes, type:', audioBlob.type)

            // Create audio URL and play
            const audioUrl = URL.createObjectURL(audioBlob)
            const audio = new Audio(audioUrl)
            audioRef.current = audio

            // Handle playback end
            audio.onended = () => {
                console.log('✅ TTS: Playback ended')
                setIsPlaying(false)
                URL.revokeObjectURL(audioUrl)
            }

            // Handle errors
            audio.onerror = (e) => {
                console.error('❌ TTS: Audio playback error:', e)
                setError('Failed to play audio')
                setIsPlaying(false)
                URL.revokeObjectURL(audioUrl)
            }

            // Start playing
            console.log('▶️ TTS: Starting playback...')
            await audio.play()
            console.log('🎵 TTS: Playing...')
            setIsPlaying(true)

        } catch (err) {
            console.error('❌ TTS: Error:', err)
            if (err instanceof ApiError) {
                setError(err.detail || 'Speech synthesis failed')
            } else {
                setError('Failed to generate speech')
            }
        } finally {
            setIsLoading(false)
        }
    }

    // Determine button content
    let buttonContent: React.ReactNode
    let buttonTitle: string

    if (isLoading) {
        buttonContent = (
            <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        )
        buttonTitle = 'Generating speech...'
    } else if (isPlaying) {
        buttonContent = '⏹️'
        buttonTitle = 'Stop playback'
    } else {
        buttonContent = '🔊'
        buttonTitle = 'Read aloud'
    }

    return (
        <div className="inline-flex items-center gap-2">
            <button
                onClick={handleClick}
                disabled={disabled || isLoading || !text.trim()}
                title={buttonTitle}
                className="p-2 rounded-lg text-lg
                   bg-zinc-100 dark:bg-zinc-800 
                   hover:bg-zinc-200 dark:hover:bg-zinc-700 
                   transition-colors
                   disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {buttonContent}
            </button>

            {error && (
                <span className="text-red-500 text-sm">{error}</span>
            )}
        </div>
    )
}
