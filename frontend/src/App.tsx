import { useState, useMemo, useEffect } from 'react'
import { getRecommendations, ApiError } from './services/api'
import { useTheme } from './hooks/useTheme'
import { useSmoothScroll } from './hooks/useSmoothScroll'
import { useScrollPosition } from './hooks/useScrollPosition'
import { useVoiceWebSocket } from './hooks/useVoiceWebSocket'
import { useAudioCapture } from './hooks/useAudioCapture'
import { AudioRecorder, type RecordingState } from './components/AudioRecorder'
import { AIOrb, type OrbState } from './components/AIOrb'
import { TTSButton } from './components/TTSButton'
import { SongList } from './components/SongList'
import { SpotifyAuth } from './components/SpotifyAuth'
import { SpotifyPlayer } from './components/SpotifyPlayer'
import { SpotifyEmbed } from './components/SpotifyEmbed'
import { ThoughtProcess } from './components/ThoughtProcess'
import type { MoodAnalysis, Song, ThoughtStep } from './types'

// Backend API URL - should match the backend server port (5000)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function App() {
  // Theme
  const { theme, toggleTheme } = useTheme()

  // Smooth scroll
  useSmoothScroll()

  // Scroll position for navbar effect
  const { scrolled } = useScrollPosition(100)

  // State
  const [moodText, setMoodText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [moodAnalysis, setMoodAnalysis] = useState<MoodAnalysis | null>(null)
  const [songs, setSongs] = useState<Song[]>([])
  const [currentTrackId, setCurrentTrackId] = useState<string | null>(null)
  const [thoughtProcess, setThoughtProcess] = useState<ThoughtStep[]>([])
  const [agentIterations, setAgentIterations] = useState(0)

  // Voice mode toggle
  // voiceMode is different from voiceReady. voiceMode is when the user clicks the voice button to enable voice mode. voiceReady is when the backend models are loaded and ready to use.
  const [voiceMode, setVoiceMode] = useState(false) // True when backend models are loaded
  const [voiceReady, setVoiceReady] = useState(false) // True when backend models are loaded

  // AI Orb state
  const [recordingState, setRecordingState] = useState<RecordingState>('idle')
  const [orbState, setOrbState] = useState<OrbState>('idle')

  // Voice WebSocket connection
  const { isConnected, connect, disconnect, sendAudio } = useVoiceWebSocket({
    onMessage: (event) => {
      console.log('Voice event:', event)

      if (event.event === 'loading') {
        // Backend is loading models - show thinking state
        setOrbState('thinking')
        setVoiceReady(false)
      } else if (event.event === 'ready') {
        // Backend models loaded - now safe to stream audio
        console.log('✅ Voice models ready')
        setVoiceReady(true)
        setOrbState('idle') // Waiting for wake word
      } else if (event.event === 'wake_word_detected') {
        setOrbState('recording') // User said "Hey Groovi"
      } else if (event.event === 'listening') {
        setOrbState('recording') // Listening for speech
      } else if (event.event === 'transcript') {
        setMoodText(event.text)
        setOrbState('thinking')
      } else if (event.event === 'songs') {
        // Music agent found songs - display in UI with mood analysis
        setSongs(event.songs)
        // Set mood analysis from agent (same structure for both voice and click mode)
        if (event.mood_analysis) {
          setMoodAnalysis(event.mood_analysis)
        }
      } else if (event.event === 'response') {
        // Agent responded
        setOrbState('complete')
      } else if (event.event === 'interrupted') {
        setOrbState('idle')
      } else if (event.event === 'voice_mode_stop') {
        // User said "pause" or "stop" - switch to click mode
        console.log('🛑 Voice mode stopped by user')
        setVoiceMode(false)
        setOrbState('idle')
      } else if (event.event === 'idle_timeout') {
        // Idle for 5 seconds - waiting for wake word
        setOrbState('idle')
      }
    },
    onAudio: (audioBlob) => {
      // Play TTS audio (WAV format from backend)
      const wavBlob = new Blob([audioBlob], { type: 'audio/wav' })
      const url = URL.createObjectURL(wavBlob)
      const audio = new Audio(url)
      audio.play().catch(err => {
        console.error('Audio playback error:', err)
      })
      // Cleanup URL after playback
      audio.onended = () => URL.revokeObjectURL(url)
    },
    onError: (error) => {
      console.error('Voice mode error:', error)
      setError(`Voice mode error: ${error}. Switching to click mode.`)
      setVoiceMode(false) // Auto-disable voice mode
      setVoiceReady(false)
      setOrbState('idle')
    },
    onConnectionChange: (state) => {
      if (state === 'error') {
        setError('Unable to connect to voice server. Switching to click mode.')
        setVoiceMode(false) // Auto-disable voice mode
        setVoiceReady(false)
        setOrbState('idle')
      } else if (state === 'disconnected') {
        setVoiceReady(false)
      }
    }
  })

  // Derive orb state from recording state and loading state (Click Mode only)
  useEffect(() => {
    if (voiceMode) return // Don't override orb state in voice mode

    if (recordingState === 'recording') {
      setOrbState('recording')
    } else if (recordingState === 'transcribing' || isLoading) {
      setOrbState('thinking')
    } else if (moodAnalysis && orbState === 'thinking') {
      // Show complete briefly when results arrive
      setOrbState('complete')
      const timer = setTimeout(() => setOrbState('idle'), 1500)
      return () => clearTimeout(timer)
    } else if (orbState !== 'complete') {
      setOrbState('idle')
    }
  }, [recordingState, isLoading, moodAnalysis, voiceMode])

  // Spotify state
  const [isSpotifyConnected, setIsSpotifyConnected] = useState(false)
  const [isCreatingPlaylist, setIsCreatingPlaylist] = useState(false)
  const [playlistUrl, setPlaylistUrl] = useState<string | null>(null)
  const [sdkFailed, setSdkFailed] = useState(false)  // True if Web Playback SDK failed

  // Get track URIs for player - memoized to prevent re-renders
  const trackUris = useMemo(() => songs.map(song => song.uri), [songs])

  // Find selected track index (for clicking on songs in playlist) - memoized
  const selectedTrackIndex = useMemo(() => {
    if (!currentTrackId) return 0
    return songs.findIndex(song => song.uri.includes(currentTrackId))
  }, [currentTrackId, songs])

  // Handle voice mode toggle - connect/disconnect WebSocket
  useEffect(() => {
    if (voiceMode) {
      // Connect WebSocket (models will load, we'll get "ready" event)
      connect()
      setOrbState('thinking') // Show loading state while models load
    } else {
      // Disconnect WebSocket
      disconnect()
      setOrbState('idle')
    }
  }, [voiceMode, connect, disconnect])

  // Raw PCM audio capture (16kHz, 16-bit mono)
  const { startCapture, stopCapture } = useAudioCapture({
    onAudioChunk: (chunk) => {
      if (isConnected) {
        sendAudio(chunk)
      }
    },
    onError: (error) => {
      setError(`Microphone error: ${error}`)
      setVoiceMode(false)
    }
  })

  // Start audio capture ONLY after backend is ready
  useEffect(() => {
    if (voiceReady) {
      startCapture()
      console.log('🎤 Voice mode active - raw PCM streaming')
    } else {
      stopCapture()
    }
  }, [voiceReady, startCapture, stopCapture])

  // Handle form submission
  const handleSubmit = async () => {
    if (!moodText.trim() || isLoading) return

    setIsLoading(true)
    setError(null)
    setMoodAnalysis(null)
    setSongs([])
    setPlaylistUrl(null)
    setThoughtProcess([])
    setAgentIterations(0)

    try {
      const response = await getRecommendations(moodText)
      setMoodAnalysis(response.mood_analysis)
      setSongs(response.songs)
      // Store agent thought process for display
      if (response.thought_process) {
        setThoughtProcess(response.thought_process)
      }
      if (response.agent_iterations) {
        setAgentIterations(response.agent_iterations)
      }
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
    <div className="min-h-screen bg-white dark:bg-black text-zinc-900 dark:text-white transition-colors">
      {/* Fixed Navbar - Glassmorphism on scroll */}
      <nav className={`fixed top-0 left-0 right-0 z-50 navbar
                      ${scrolled
          ? (theme === 'dark' ? 'navbar-scrolled' : 'navbar-scrolled-light')
          : ''}`}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          {/* Logo - Left */}
          <a href="#" className="text-xl font-bold tracking-tight">
            <span className={theme === 'dark' ? 'hero-text-gradient' : 'hero-text-gradient-light'}>Groovi</span>
          </a>

          {/* Controls - Right */}
          <div className="flex items-center gap-3">
            {/* Spotify Auth */}
            <SpotifyAuth onAuthChange={setIsSpotifyConnected} />

            {/* Voice Mode Toggle */}
            <button
              onClick={() => setVoiceMode(!voiceMode)}
              className={`px-4 py-2.5 rounded-xl transition-all duration-300 font-medium
                         ${voiceMode
                  ? 'bg-purple-600 text-white hover:bg-purple-500'
                  : theme === 'dark'
                    ? 'bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1] text-zinc-300'
                    : 'bg-black/[0.05] border border-black/[0.08] hover:bg-black/[0.1] text-zinc-700'
                }`}
              aria-label="Toggle voice mode"
            >
              {voiceMode ? '🎤 Voice Mode' : '✋ Click Mode'}
            </button>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2.5 rounded-xl transition-all duration-300
                         ${theme === 'dark'
                  ? 'bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1]'
                  : 'bg-black/[0.05] border border-black/[0.08] hover:bg-black/[0.1]'}`}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section - Full screen */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 pt-16">
        <h1 className={`text-5xl md:text-7xl font-bold tracking-tight text-center max-w-4xl leading-tight
                       ${theme === 'dark' ? 'hero-text-gradient' : 'hero-text-gradient-light'}`}>
          Discover Your Vibe<br />Through Music
        </h1>
        <p className={`mt-6 text-lg md:text-xl text-center max-w-2xl
                      ${theme === 'dark' ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Describe your mood, and let AI curate the perfect soundtrack for you
        </p>
        {isSpotifyConnected && (
          <p className="mt-4 text-sm text-green-500 font-medium">
            🎧 Spotify connected
          </p>
        )}

        {/* Scroll indicator */}
        <div className="absolute bottom-8 animate-bounce">
          <svg className={`w-6 h-6 ${theme === 'dark' ? 'text-zinc-500' : 'text-zinc-400'}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* Main content - Input and Results */}
      <main id="main" className={`relative py-20 ${songs.length > 0 && isSpotifyConnected ? 'pb-32' : 'pb-20'}`}>
        {/* Background gradient for visual interest */}
        <div className={`absolute inset-0 -z-10 overflow-hidden
                        ${theme === 'dark'
            ? 'bg-gradient-to-b from-purple-900/10 via-transparent to-transparent'
            : 'bg-gradient-to-b from-purple-100/50 via-transparent to-transparent'}`} />

        <div className="max-w-4xl mx-auto px-4">
          {/* Section heading */}
          <h2 className={`text-2xl font-bold mb-2 text-center
                         ${theme === 'dark' ? 'text-white' : 'text-zinc-900'}`}>
            What's your vibe today?
          </h2>

          {/* Mode indicator */}
          <p className={`text-center mb-6 ${theme === 'dark' ? 'text-zinc-400' : 'text-zinc-600'}`}>
            {voiceMode
              ? '🎤 Voice Mode Active - Say "Hey Groovi" to start'
              : '✋ Click the orb to record'}
          </p>

          {/* AI Orb - Centered between heading and input */}
          <div className="flex justify-center mb-6">
            <AudioRecorder
              onTranscriptReceived={handleTranscriptReceived}
              onError={setError}
              disabled={isLoading}
              onRecordingStateChange={setRecordingState}
              renderButton={({ onClick, disabled: btnDisabled }) => (
                <AIOrb
                  state={orbState}
                  onClick={onClick}
                  disabled={btnDisabled}
                  theme={theme}
                />
              )}
            />
          </div>

          {/* Glassmorphic Input Card */}
          <div className={`p-6 rounded-3xl backdrop-blur-xl transition-all duration-300
                          ${theme === 'dark'
              ? 'bg-gradient-to-br from-purple-600/[0.15] via-violet-500/[0.10] to-indigo-600/[0.15] border border-purple-500/20 shadow-2xl shadow-purple-500/20'
              : 'bg-gradient-to-br from-purple-200/80 via-violet-100/60 to-indigo-200/80 border border-purple-300/60 shadow-xl shadow-purple-500/20'}`}>

            {/* Textarea */}
            <textarea
              value={moodText}
              onChange={(e) => setMoodText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="How are you feeling today? (Ctrl+Enter to submit)"
              className={`w-full p-5 rounded-2xl backdrop-blur-xl
                         resize-none h-32 transition-all duration-300
                         focus:outline-none focus:ring-2 focus:ring-purple-500/50
                         ${theme === 'dark'
                  ? 'bg-white/[0.03] border border-white/[0.08] text-zinc-100 placeholder-zinc-500'
                  : 'bg-zinc-50 border border-zinc-200 text-zinc-900 placeholder-zinc-400'}`}
              disabled={isLoading}
            />

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={isLoading || !moodText.trim()}
              className="w-full mt-4 py-4 px-6 rounded-2xl font-semibold
                         bg-gradient-to-r from-purple-600 to-violet-600 
                         hover:from-purple-500 hover:to-violet-500
                         text-white transition-all duration-300
                         hover:shadow-lg hover:shadow-purple-500/30
                         focus:outline-none focus:ring-2 focus:ring-purple-500/50
                         disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none"
            >
              {isLoading ? 'Finding your vibe...' : 'Get My Vibe'}
            </button>
          </div>

          {/* Results Section - Box in box design */}
          {(error || isLoading || moodAnalysis || songs.length > 0) && (
            <div className={`mt-8 p-6 rounded-3xl backdrop-blur-xl transition-all duration-300 animate-fade-in
                            ${theme === 'dark'
                ? 'bg-gradient-to-br from-purple-600/25 via-indigo-500/20 to-violet-600/25 border border-purple-400/30 shadow-2xl shadow-purple-500/25'
                : 'bg-gradient-to-br from-purple-300/50 via-indigo-200/40 to-violet-300/50 border border-purple-400/40 shadow-xl shadow-purple-500/20'}`}>

              {/* Error Message */}
              {error && (
                <div className={`p-4 rounded-xl mb-6
                                ${theme === 'dark'
                    ? 'bg-red-900/40 border border-red-500/40 text-red-300'
                    : 'bg-red-50 border border-red-200 text-red-600'}`}>
                  {error}
                </div>
              )}

              {/* Loading indicator text - orb handles visual */}
              {isLoading && (
                <p className={`text-center py-4 ${theme === 'dark' ? 'text-zinc-400' : 'text-zinc-500'}`}>
                  AI is exploring Spotify for you...
                </p>
              )}

              {/* Mood Analysis - Inner white glass box */}
              {moodAnalysis && (
                <div className={`mb-6 p-6 rounded-2xl backdrop-blur-xl
                                ${theme === 'dark'
                    ? 'bg-white/[0.08] border border-white/[0.15]'
                    : 'bg-white/80 border border-white/60 shadow-sm'}`}>
                  {/* Header with TTS - centered */}
                  <div className="flex items-center justify-center gap-4 mb-4">
                    <h2 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-zinc-900'}`}>
                      Your Mood Analysis
                    </h2>
                    <TTSButton text={moodAnalysis.description} />
                  </div>

                  {/* Mood Badge - centered */}
                  <div className="flex items-center justify-center gap-3 mb-6">
                    <span className="px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-purple-500 to-indigo-500 text-white">
                      {moodAnalysis.category}
                    </span>
                  </div>

                  {/* Description/Reasoning */}
                  <p className={`text-center leading-relaxed mb-4 ${theme === 'dark' ? 'text-zinc-200' : 'text-zinc-700'}`}>
                    {moodAnalysis.description}
                  </p>

                  {/* Thought Process */}
                  <ThoughtProcess
                    steps={thoughtProcess}
                    iterations={agentIterations}
                    theme={theme}
                  />
                </div>
              )}


              {/* Song List - Inner white glass box */}
              {songs.length > 0 && (
                <div className={`p-6 rounded-2xl backdrop-blur-xl
                                ${theme === 'dark'
                    ? 'bg-white/[0.08] border border-white/[0.15]'
                    : 'bg-white/80 border border-white/60 shadow-sm'}`}>
                  <h2 className={`text-2xl font-bold mb-6 tracking-tight text-center ${theme === 'dark' ? 'text-white' : 'text-zinc-900'}`}>
                    Your Personalized Playlist
                  </h2>
                  <SongList
                    songs={songs}
                    currentTrackId={currentTrackId}
                    onSongSelect={setCurrentTrackId}
                    theme={theme}
                  />

                  {/* Playlist Button */}
                  {isSpotifyConnected && (
                    <div className="mt-6 flex justify-center">
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
                </div>
              )}
            </div>
          )}
        </div>
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
