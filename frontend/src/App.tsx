import { useState } from 'react'
import { getRecommendations, ApiError } from './services/api'
import { useTheme } from './hooks/useTheme'
import { AudioRecorder } from './components/AudioRecorder'
import { TTSButton } from './components/TTSButton'
import { SongList } from './components/SongList'
import { SpotifyAuth } from './components/SpotifyAuth'
import { SpotifyPlayer } from './components/SpotifyPlayer'
import { SpotifyEmbed } from './components/SpotifyEmbed'
import type { MoodAnalysis, Song } from './types'

// Backend API URL
const API_URL = 'http://localhost:8000'

function App() {
  // Theme
  const { theme, toggleTheme } = useTheme()

  // State
  const [moodText, setMoodText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [moodAnalysis, setMoodAnalysis] = useState<MoodAnalysis | null>(null)
  const [songs, setSongs] = useState<Song[]>([])
  const [currentTrackId, setCurrentTrackId] = useState<string | null>(null)

  // Spotify state
  const [isSpotifyConnected, setIsSpotifyConnected] = useState(false)
  const [isCreatingPlaylist, setIsCreatingPlaylist] = useState(false)
  const [playlistUrl, setPlaylistUrl] = useState<string | null>(null)
  const [sdkFailed, setSdkFailed] = useState(false)  // True if Web Playback SDK failed

  // Get track URIs for player
  const trackUris = songs.map(song => song.uri)

  // Find selected track index (for clicking on songs in playlist)
  const selectedTrackIndex = currentTrackId
    ? songs.findIndex(song => song.uri.includes(currentTrackId))
    : 0

  // Handle form submission
  const handleSubmit = async () => {
    if (!moodText.trim() || isLoading) return

    setIsLoading(true)
    setError(null)
    setMoodAnalysis(null)
    setSongs([])
    setPlaylistUrl(null)

    try {
      const response = await getRecommendations(moodText)
      setMoodAnalysis(response.mood_analysis)
      setSongs(response.songs)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || err.message)
      } else {
        setError('Something went wrong. Please try again.')
      }
      console.error('API Error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Handle transcript from audio recording
  const handleTranscriptReceived = (transcript: string) => {
    setMoodText(transcript)
  }

  // Handle Enter key (Ctrl+Enter to submit)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Create playlist from current songs
  const handleCreatePlaylist = async () => {
    if (songs.length === 0 || !isSpotifyConnected) return

    setIsCreatingPlaylist(true)
    try {
      const playlistName = `Groovi - ${moodAnalysis?.category || 'Mood'} Vibes`
      const response = await fetch(`${API_URL}/playlist/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: playlistName,
          track_uris: trackUris,
          description: `Created by Groovi based on your ${moodAnalysis?.category || ''} mood 🎵`,
          public: false
        })
      })

      if (!response.ok) {
        throw new Error('Failed to create playlist')
      }

      const data = await response.json()
      setPlaylistUrl(data.playlist?.external_url)
    } catch (err) {
      console.error('Playlist creation failed:', err)
      setError('Failed to create playlist. Make sure you are connected to Spotify.')
    } finally {
      setIsCreatingPlaylist(false)
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white transition-colors">
      {/* Header controls */}
      <div className="fixed top-4 right-4 flex items-center gap-3 z-50">
        {/* Spotify Auth */}
        <SpotifyAuth onAuthChange={setIsSpotifyConnected} />

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 
                     hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </div>

      {/* Header */}
      <header className="py-12 text-center">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-500 to-indigo-500 bg-clip-text text-transparent">
          Groovi
        </h1>
        <p className="mt-4 text-lg text-zinc-500 dark:text-zinc-400">
          Describe your mood, get the perfect soundtrack
        </p>
        {isSpotifyConnected && (
          <p className="mt-2 text-sm text-green-500">
            🎧 Full playback enabled
          </p>
        )}
      </header>

      {/* Main content - add padding for player */}
      <main className={`max-w-2xl mx-auto px-4 ${songs.length > 0 && isSpotifyConnected ? 'pb-32' : 'pb-20'}`}>
        {/* Mood Input Section */}
        <div className="space-y-4">
          {/* Audio Recording Button - Above textarea */}
          <AudioRecorder
            onTranscriptReceived={handleTranscriptReceived}
            onError={setError}
            disabled={isLoading}
          />

          <textarea
            value={moodText}
            onChange={(e) => setMoodText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="How are you feeling today? (Ctrl+Enter to submit)"
            className="w-full p-4 rounded-xl bg-zinc-100 dark:bg-zinc-900 
                       border border-zinc-200 dark:border-zinc-800
                       text-zinc-900 dark:text-white 
                       placeholder-zinc-400 dark:placeholder-zinc-500
                       focus:outline-none focus:ring-2 focus:ring-purple-500
                       resize-none h-32 transition-colors"
            disabled={isLoading}
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !moodText.trim()}
            className="w-full py-3 px-6 rounded-xl font-semibold
                       bg-gradient-to-r from-purple-500 to-indigo-500
                       text-white hover:opacity-90 transition-opacity
                       focus:outline-none focus:ring-2 focus:ring-purple-500
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Finding your vibe...' : 'Get My Vibe'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 
                          border border-red-200 dark:border-red-800 
                          text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Mood Analysis Card */}
        {moodAnalysis && (
          <div className="mt-8 p-6 rounded-xl bg-zinc-100 dark:bg-zinc-900 
                          border border-zinc-200 dark:border-zinc-800 transition-colors">
            {/* Header with TTS button */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Your Mood Analysis</h2>
              <TTSButton text={moodAnalysis.summary} />
            </div>

            {/* Mood Category Badge */}
            <div className="flex items-center gap-3 mb-4">
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-purple-500 to-indigo-500 text-white">
                {moodAnalysis.category}
              </span>
              <span className="text-zinc-500 dark:text-zinc-400 text-sm">
                {moodAnalysis.intensity} intensity
              </span>
            </div>

            {/* Summary */}
            <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed mb-4">
              {moodAnalysis.summary}
            </p>

            {/* Description */}
            <p className="text-zinc-500 dark:text-zinc-400 text-sm">
              {moodAnalysis.description}
            </p>
          </div>
        )}

        {/* Songs - Glassmorphism stacked cards */}
        <SongList
          songs={songs}
          currentTrackId={currentTrackId}
          onSongSelect={setCurrentTrackId}
        />

        {/* Save as Playlist Button */}
        {songs.length > 0 && isSpotifyConnected && (
          <div className="mt-6 flex flex-col items-center gap-3">
            {!playlistUrl ? (
              <button
                onClick={handleCreatePlaylist}
                disabled={isCreatingPlaylist}
                className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                         bg-[#1DB954] hover:bg-[#1ed760] text-white
                         transition-all duration-200 hover:scale-105
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreatingPlaylist ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Creating Playlist...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
                    </svg>
                    Save as Spotify Playlist
                  </>
                )}
              </button>
            ) : (
              <a
                href={playlistUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold
                         bg-green-500/20 border border-green-500/50 text-green-500
                         hover:bg-green-500/30 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                </svg>
                Open Playlist in Spotify
              </a>
            )}
          </div>
        )}
      </main>

      {/* Spotify Player - Full playback controls (when authenticated and SDK working) */}
      {isSpotifyConnected && songs.length > 0 && !sdkFailed && (
        <SpotifyPlayer
          trackUris={trackUris}
          isAuthenticated={isSpotifyConnected}
          startTrackIndex={selectedTrackIndex >= 0 ? selectedTrackIndex : 0}
          onTrackChange={(index) => {
            // Sync currentTrackId when player changes tracks
            if (songs[index]) {
              const trackId = songs[index].uri.split(':')[2]
              setCurrentTrackId(trackId)
            }
          }}
          onPlaybackFailed={() => {
            // SDK failed - switch to embed with first track
            console.log('🔀 Switching to embed player')
            setSdkFailed(true)
            if (songs.length > 0) {
              // Extract track ID from URI (format: spotify:track:TRACKID)
              const trackId = songs[0].uri.split(':')[2]
              setCurrentTrackId(trackId)
            }
          }}
        />
      )}

      {/* Spotify Embed - Fallback player (when NOT authenticated OR SDK failed) */}
      {(!isSpotifyConnected || sdkFailed) && currentTrackId && (
        <SpotifyEmbed
          trackId={currentTrackId}
          onClose={() => setCurrentTrackId(null)}
        />
      )}

      {/* Footer - hide when player is showing */}
      {!(songs.length > 0) && (
        <footer className="fixed bottom-4 left-0 right-0 text-center text-sm text-zinc-400">
          <p>Built with ❤️ for music lovers</p>
        </footer>
      )}
    </div>
  )
}

export default App
