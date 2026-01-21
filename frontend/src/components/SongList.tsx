import type { Song } from '../types'

interface SongListProps {
    songs: Song[]
    currentTrackId: string | null
    onSongSelect: (trackId: string | null) => void
    theme?: 'light' | 'dark'
}

/**
 * SongList - Playlist container with stacked song cards
 */
export function SongList({ songs, currentTrackId, onSongSelect, theme = 'dark' }: SongListProps) {
    if (songs.length === 0) return null

    // Animation delay classes for staggered entry (10 songs)
    const delayClasses = [
        'animate-delay-1', 'animate-delay-2', 'animate-delay-3', 'animate-delay-4', 'animate-delay-5',
        'animate-delay-6', 'animate-delay-7', 'animate-delay-8', 'animate-delay-9', 'animate-delay-10'
    ]

    return (
        <div className="animate-fade-in space-y-2 max-h-[480px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent">
            {songs.map((song, index) => {
                // Extract track ID from URI (spotify:track:XXXXX)
                const trackId = song.uri.split(':')[2]
                const isPlaying = currentTrackId === trackId
                const delayClass = delayClasses[index] || ''

                return (
                    <button
                        key={song.uri}
                        onClick={() => onSongSelect(isPlaying ? null : trackId)}
                        className={`w-full flex items-center gap-4 p-3 rounded-xl text-left
                         transition-all duration-300 ease-out hover-lift animate-fade-in ${delayClass}
                         ${isPlaying
                                ? 'bg-purple-500/20 border border-purple-500/40 shadow-lg shadow-purple-500/10'
                                : theme === 'dark'
                                    ? 'bg-white/[0.05] border border-white/[0.1] hover:bg-white/[0.1]'
                                    : 'bg-zinc-100/80 border border-zinc-200/50 hover:bg-zinc-100'}`}
                    >
                        {/* Track number */}
                        <span className={`w-6 text-center text-sm font-medium 
                                        ${isPlaying ? 'text-purple-500' : theme === 'dark' ? 'text-zinc-400' : 'text-zinc-500'}`}>
                            {isPlaying ? '▶' : index + 1}
                        </span>

                        {/* Album Art */}
                        {song.album_art ? (
                            <img
                                src={song.album_art}
                                alt={`${song.name} album art`}
                                className="w-12 h-12 rounded-xl object-cover shadow-md"
                            />
                        ) : (
                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center
                                           ${theme === 'dark'
                                    ? 'bg-white/[0.05] border border-white/[0.08] text-zinc-500'
                                    : 'bg-zinc-200 border border-zinc-300 text-zinc-400'}`}>
                                <span className="text-lg">🎵</span>
                            </div>
                        )}

                        {/* Song Info */}
                        <div className="flex-1 min-w-0">
                            <p className={`font-semibold truncate 
                                          ${isPlaying
                                    ? 'text-purple-500'
                                    : theme === 'dark' ? 'text-white' : 'text-zinc-900'}`}>
                                {song.name}
                            </p>
                            <p className={`text-sm truncate ${theme === 'dark' ? 'text-zinc-400' : 'text-zinc-600'}`}>
                                {song.artist}
                            </p>
                        </div>

                        {/* Playing indicator - animated bars */}
                        {isPlaying && (
                            <div className="flex gap-0.5">
                                <span className="w-1 h-4 bg-purple-500 rounded-full animate-pulse" />
                                <span className="w-1 h-4 bg-purple-500 rounded-full animate-pulse delay-75" />
                                <span className="w-1 h-4 bg-purple-500 rounded-full animate-pulse delay-150" />
                            </div>
                        )}
                    </button>
                )
            })}
        </div>
    )
}
