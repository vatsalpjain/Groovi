import type { Song } from '../types'

interface SongListProps {
    songs: Song[]
    currentTrackId: string | null
    onSongSelect: (trackId: string | null) => void
}

/**
 * SongList - Glassmorphism playlist container with stacked song cards
 */
export function SongList({ songs, currentTrackId, onSongSelect }: SongListProps) {
    if (songs.length === 0) return null

    return (
        <div className="mt-8">
            <h2 className="text-2xl font-bold mb-6">Your Personalized Playlist</h2>

            {/* Glassmorphism container */}
            <div className="bg-zinc-100/50 dark:bg-zinc-900/50 backdrop-blur-xl 
                      border border-zinc-200/50 dark:border-zinc-700/50 
                      rounded-3xl p-4 space-y-3">
                {songs.map((song, index) => {
                    // Extract track ID from URI (spotify:track:XXXXX)
                    const trackId = song.uri.split(':')[2]
                    const isPlaying = currentTrackId === trackId

                    return (
                        <button
                            key={song.uri}
                            onClick={() => onSongSelect(isPlaying ? null : trackId)}
                            className={`w-full flex items-center gap-4 p-3 rounded-2xl text-left
                         transition-all duration-200
                         ${isPlaying
                                    ? 'bg-purple-500/20 border border-purple-500/50 shadow-lg shadow-purple-500/10'
                                    : 'bg-white/50 dark:bg-zinc-800/50 border border-transparent hover:bg-white/80 dark:hover:bg-zinc-800/80 hover:border-zinc-200/50 dark:hover:border-zinc-600/50'}`}
                        >
                            {/* Track number */}
                            <span className="w-6 text-center text-sm font-medium text-zinc-400">
                                {isPlaying ? '▶' : index + 1}
                            </span>

                            {/* Album Art */}
                            <img
                                src={song.album_art}
                                alt={`${song.name} album art`}
                                className="w-12 h-12 rounded-xl object-cover shadow-md"
                            />

                            {/* Song Info */}
                            <div className="flex-1 min-w-0">
                                <p className={`font-semibold truncate ${isPlaying ? 'text-purple-500' : 'text-zinc-900 dark:text-white'}`}>
                                    {song.name}
                                </p>
                                <p className="text-zinc-500 dark:text-zinc-400 text-sm truncate">
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
        </div>
    )
}
