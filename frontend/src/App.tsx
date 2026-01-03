import { useState } from 'react'
import { getRecommendations, ApiError } from './services/api'
import { useTheme } from './hooks/useTheme'
import { AudioRecorder } from './components/AudioRecorder'
import { TTSButton } from './components/TTSButton'
import { SpotifyEmbed } from './components/SpotifyEmbed'
import { SongList } from './components/SongList'
import type { MoodAnalysis, Song } from './types'

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

  // Handle form submission
  const handleSubmit = async () => {
    if (!moodText.trim() || isLoading) return

    setIsLoading(true)
    setError(null)
    setMoodAnalysis(null)
    setSongs([])

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

  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white transition-colors">
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 p-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 
                   hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? '☀️' : '🌙'}
      </button>

      {/* Header */}
      <header className="py-12 text-center">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-500 to-indigo-500 bg-clip-text text-transparent">
          Groovi
        </h1>
        <p className="mt-4 text-lg text-zinc-500 dark:text-zinc-400">
          Describe your mood, get the perfect soundtrack
        </p>
      </header>

      {/* Main content */}
      <main className="max-w-2xl mx-auto px-4 pb-20">
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
      </main>

      {/* Spotify Embed Player - Sticky bottom-right */}
      {currentTrackId && (
        <SpotifyEmbed
          trackId={currentTrackId}
          onClose={() => setCurrentTrackId(null)}
        />
      )}

      {/* Footer - hide when player is showing */}
      {!currentTrackId && (
        <footer className="fixed bottom-4 left-0 right-0 text-center text-sm text-zinc-400">
          <p>Built with ❤️ for music lovers</p>
        </footer>
      )}
    </div>
  )
}

export default App
