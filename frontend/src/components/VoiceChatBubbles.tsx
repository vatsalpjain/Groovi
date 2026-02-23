/**
 * VoiceChatBubbles - Fading conversation trail for voice mode
 * 
 * Displays user transcripts (right) and AI responses (left) as chat bubbles.
 * Older messages progressively fade out, creating a living conversation trail.
 * Max 4 visible messages at a time.
 */

import { useEffect, useRef } from 'react'

export interface ChatMessage {
    role: 'user' | 'assistant'
    text: string
    id: number // Unique ID for React key + ordering
}

interface VoiceChatBubblesProps {
    messages: ChatMessage[]
    theme: 'light' | 'dark'
}

// Only show the last 4 messages — older ones are hidden
const MAX_VISIBLE = 4

export function VoiceChatBubbles({ messages, theme }: VoiceChatBubblesProps) {
    const containerRef = useRef<HTMLDivElement>(null)

    // Auto-scroll to latest message when new ones arrive
    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight
        }
    }, [messages])

    // Slice to last MAX_VISIBLE messages
    const visibleMessages = messages.slice(-MAX_VISIBLE)

    // Always render container to reserve fixed space — even when empty
    return (
        <div
            ref={containerRef}
            className="w-full max-w-2xl mx-auto mt-4 mb-6 h-40 flex flex-col justify-end gap-1 px-4 overflow-hidden"
        >
            {visibleMessages.map((msg, index) => {
                // Paired fading: oldest 2 nearly invisible, newest 2 crisp
                // With 4 messages: [0.2, 0.3, 0.9, 1.0]
                const isOldPair = index < visibleMessages.length - 2
                const opacity = isOldPair
                    ? 0.2 + (index * 0.1) // Old pair: faded but readable
                    : 0.9 + ((index - (visibleMessages.length - 2)) * 0.1) // New pair: full
                // Old pair noticeably smaller
                const fontSize = isOldPair ? '0.75rem' : '1rem'

                const isUser = msg.role === 'user'

                return (
                    <div
                        key={msg.id}
                        className={`flex ${isUser ? 'justify-end' : 'justify-start'} voice-bubble-enter`}
                        style={{
                            opacity,
                            fontSize,
                            transition: 'opacity 0.5s ease-in-out, font-size 0.5s ease-in-out',
                        }}
                    >
                        {/* Plain text — no container, no label */}
                        <p
                            className={`
                max-w-[80%] text-base leading-relaxed
                ${isUser
                                    ? theme === 'dark' ? 'text-zinc-200' : 'text-zinc-800'
                                    : theme === 'dark' ? 'text-purple-400' : 'text-purple-600'
                                }
              `}
                        >
                            {msg.text}
                        </p>
                    </div>
                )
            })}
        </div>
    )
}
