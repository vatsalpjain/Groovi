interface SpotifyEmbedProps {
    trackId: string
    onClose: () => void
}

/**
 * SpotifyEmbed - Glassmorphism floating player bar
 * Centered at bottom with rounded corners and blur effect
 */
export function SpotifyEmbed({ trackId, onClose }: SpotifyEmbedProps) {
    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 
                    w-[90%] max-w-2xl
                    bg-zinc-900/80 backdrop-blur-xl
                    border border-zinc-700/50 
                    rounded-2xl shadow-2xl shadow-purple-500/10
                    overflow-hidden">
            {/* Close button */}
            <button
                onClick={onClose}
                className="absolute top-2 right-3 z-10 w-6 h-6 rounded-full
                   bg-zinc-700/50 hover:bg-zinc-600/50 text-white text-xs
                   flex items-center justify-center transition-colors"
                aria-label="Close player"
            >
                ✕
            </button>

            {/* Spotify iframe embed - compact */}
            <iframe
                src={`https://open.spotify.com/embed/track/${trackId}?utm_source=generator&theme=0`}
                width="100%"
                height="80"
                frameBorder="0"
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                loading="lazy"
                className="rounded-2xl"
            />
        </div>
    )
}
