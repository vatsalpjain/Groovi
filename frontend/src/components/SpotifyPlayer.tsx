import { useEffect, useState, useCallback, useRef } from 'react'

// MCP Server URL
const MCP_URL = 'http://localhost:5000'

// Spotify Web Playback SDK types
interface SpotifyPlayer {
    connect(): Promise<boolean>
    disconnect(): void
    togglePlay(): Promise<void>
    nextTrack(): Promise<void>
    previousTrack(): Promise<void>
    seek(position_ms: number): Promise<void>
    setVolume(volume: number): Promise<void>
    addListener(event: string, callback: (data: unknown) => void): void
}

interface SpotifyTrack {
    id: string
    uri: string
    name: string
    artists: Array<{ name: string }>
    album: {
        images: Array<{ url: string }>
    }
    duration_ms: number
}

interface SpotifyPlayerState {
    paused: boolean
    position: number
    track_window: {
        current_track: SpotifyTrack | null
        previous_tracks: SpotifyTrack[]
    }
}

declare global {
    interface Window {
        Spotify: {
            Player: new (config: {
                name: string
                getOAuthToken: (cb: (token: string) => void) => void
                volume: number
            }) => SpotifyPlayer
        }
        onSpotifyWebPlaybackSDKReady: () => void
    }
}

interface SpotifyPlayerProps {
    trackUris: string[]  // List of track URIs to play
    isAuthenticated: boolean
    startTrackIndex?: number  // Index of track to start from (when user clicks a song)
    onTrackChange?: (index: number) => void
    onPlaybackFailed?: () => void  // Called when SDK playback fails, so app can use fallback
}

interface TrackInfo {
    id: string  // Track ID for like/unlike
    name: string
    artist: string
    albumArt: string
    duration: number
}

/**
 * SpotifyPlayer - Full playback control using Web Playback SDK
 * 
 * Features:
 * - Play/Pause/Skip controls
 * - Progress bar with seek
 * - Volume control
 * - Current track display
 * - Queue support (auto-plays next track)
 */
export function SpotifyPlayer({ trackUris, isAuthenticated, startTrackIndex = 0, onTrackChange, onPlaybackFailed }: SpotifyPlayerProps) {
    const [player, setPlayer] = useState<SpotifyPlayer | null>(null)
    const [deviceId, setDeviceId] = useState<string | null>(null)
    const [isReady, setIsReady] = useState(false)
    const [isPlaying, setIsPlaying] = useState(false)
    const [currentTrack, setCurrentTrack] = useState<TrackInfo | null>(null)
    const [progress, setProgress] = useState(0)
    const [volume, setVolume] = useState(50)
    const [currentIndex, setCurrentIndex] = useState(0)

    // New feature states
    const [isShuffled, setIsShuffled] = useState(false)
    const [repeatMode, setRepeatMode] = useState<'off' | 'track' | 'context'>('off')
    const [isLiked, setIsLiked] = useState(false)

    const progressInterval = useRef<number | null>(null)

    // Load Spotify Web Playback SDK
    useEffect(() => {
        if (!isAuthenticated) return

        // Check if SDK is already loaded
        if (window.Spotify) {
            initializePlayer()
            return
        }

        // Load SDK script
        const script = document.createElement('script')
        script.src = 'https://sdk.scdn.co/spotify-player.js'
        script.async = true
        document.body.appendChild(script)

        window.onSpotifyWebPlaybackSDKReady = initializePlayer

        return () => {
            if (player) {
                player.disconnect()
            }
            if (progressInterval.current) {
                clearInterval(progressInterval.current)
            }
        }
    }, [isAuthenticated])

    // Store access token for direct API calls
    const accessTokenRef = useRef<string | null>(null)

    // Initialize Spotify Player
    const initializePlayer = async () => {
        try {
            // Get initial access token from MCP
            const tokenResponse = await fetch(`${MCP_URL}/auth/token`)
            if (!tokenResponse.ok) {
                console.error('Failed to get access token')
                onPlaybackFailed?.()
                return
            }
            const { access_token } = await tokenResponse.json()
            accessTokenRef.current = access_token  // Store for later use

            const spotifyPlayer = new window.Spotify.Player({
                name: 'Groovi Player',
                // IMPORTANT: Fetch fresh token each time SDK requests it
                getOAuthToken: async (cb: (token: string) => void) => {
                    try {
                        const response = await fetch(`${MCP_URL}/auth/token`)
                        if (response.ok) {
                            const data = await response.json()
                            accessTokenRef.current = data.access_token
                            cb(data.access_token)
                        } else {
                            // Fallback to stored token
                            cb(accessTokenRef.current || access_token)
                        }
                    } catch {
                        cb(accessTokenRef.current || access_token)
                    }
                },
                volume: volume / 100
            })

            // Ready event
            spotifyPlayer.addListener('ready', (data: unknown) => {
                const { device_id } = data as { device_id: string }
                console.log('🎵 Spotify Player ready with device ID:', device_id)
                setDeviceId(device_id)
                setIsReady(true)
            })

            // Not ready event
            spotifyPlayer.addListener('not_ready', (data: unknown) => {
                const { device_id } = data as { device_id: string }
                console.log('⚠️ Device went offline:', device_id)
                setIsReady(false)
            })

            // Player state changed
            spotifyPlayer.addListener('player_state_changed', (data: unknown) => {
                const state = data as SpotifyPlayerState | null
                if (!state) return

                setIsPlaying(!state.paused)
                setProgress(state.position)

                const track = state.track_window.current_track
                if (track) {
                    setCurrentTrack({
                        id: track.id,
                        name: track.name,
                        artist: track.artists.map((a: { name: string }) => a.name).join(', '),
                        albumArt: track.album.images[0]?.url || '',
                        duration: track.duration_ms
                    })
                }

                // Handle track ending
                if (state.paused && state.position === 0 && state.track_window.previous_tracks.length > 0) {
                    // Track ended, play next
                    const nextIndex = currentIndex + 1
                    if (nextIndex < trackUris.length) {
                        setCurrentIndex(nextIndex)
                        onTrackChange?.(nextIndex)
                    }
                }
            })

            // Errors
            spotifyPlayer.addListener('initialization_error', (data: unknown) => {
                const { message } = data as { message: string }
                console.error('Initialization error:', message)
            })
            spotifyPlayer.addListener('authentication_error', (data: unknown) => {
                const { message } = data as { message: string }
                console.error('Authentication error:', message)
            })
            spotifyPlayer.addListener('account_error', (data: unknown) => {
                const { message } = data as { message: string }
                console.error('Account error (Premium required):', message)
            })

            await spotifyPlayer.connect()
            setPlayer(spotifyPlayer)

        } catch (error) {
            console.error('Failed to initialize player:', error)
        }
    }

    // Start playback when device is ready and tracks are available
    useEffect(() => {
        if (isReady && deviceId && trackUris.length > 0) {
            startPlayback()
        }
    }, [isReady, deviceId, trackUris, startTrackIndex])  // Re-trigger when selected track changes

    // Update progress bar
    useEffect(() => {
        if (isPlaying) {
            progressInterval.current = window.setInterval(() => {
                setProgress(prev => prev + 1000)
            }, 1000)
        } else if (progressInterval.current) {
            clearInterval(progressInterval.current)
        }

        return () => {
            if (progressInterval.current) {
                clearInterval(progressInterval.current)
            }
        }
    }, [isPlaying])

    // Start playback with track URIs - calls Spotify API directly
    const startPlayback = async (retryCount = 0) => {
        if (!deviceId || !accessTokenRef.current) {
            console.log('⚠️ Missing deviceId or access token')
            return
        }

        // Wait for device to fully register with Spotify (longer on first try)
        const delay = retryCount === 0 ? 2000 : 2000 * retryCount
        console.log(`⏳ Waiting ${delay}ms for device activation...`)
        await new Promise(resolve => setTimeout(resolve, delay))

        // Verify our device is registered with Spotify
        try {
            const devicesResponse = await fetch('https://api.spotify.com/v1/me/player/devices', {
                headers: { 'Authorization': `Bearer ${accessTokenRef.current}` }
            })
            if (devicesResponse.ok) {
                const devicesData = await devicesResponse.json()
                // First try matching by ID, then by name ('Groovi Player')
                let ourDevice = devicesData.devices?.find((d: { id: string }) => d.id === deviceId)
                if (!ourDevice) {
                    // ID didn't match, try matching by name
                    ourDevice = devicesData.devices?.find((d: { name: string }) => d.name === 'Groovi Player')
                }

                if (ourDevice) {
                    console.log('✅ Device verified on Spotify:', ourDevice.name, ourDevice.is_active ? '(active)' : '(inactive)', 'ID:', ourDevice.id)
                    // Use the server-side device ID directly (might be different from SDK device_id)
                    const serverDeviceId = ourDevice.id
                    if (serverDeviceId !== deviceId) {
                        console.log('📝 Using server device ID:', serverDeviceId, 'instead of SDK ID:', deviceId)
                        setDeviceId(serverDeviceId)
                    }

                    // Start playback with the verified server device ID
                    try {
                        console.log('🎯 Starting playback on device:', serverDeviceId, 'from track index:', startTrackIndex)

                        const playResponse = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${serverDeviceId}`, {
                            method: 'PUT',
                            headers: {
                                'Authorization': `Bearer ${accessTokenRef.current}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                uris: trackUris,
                                offset: { position: startTrackIndex }  // Start from selected track
                            })
                        })

                        if (playResponse.ok || playResponse.status === 204) {
                            console.log('▶️ Playback started successfully with', trackUris.length, 'tracks from index', startTrackIndex)
                            setCurrentIndex(startTrackIndex)
                            return  // Success! Exit the function
                        } else {
                            console.log('❌ Playback failed with status:', playResponse.status)
                        }
                    } catch (playError) {
                        console.error('Playback error:', playError)
                    }
                } else {
                    console.log('❌ Groovi Player NOT found in Spotify devices list. Available:', devicesData.devices?.map((d: { name: string }) => d.name) || 'none')
                    if (retryCount < 3) {
                        return startPlayback(retryCount + 1)
                    } else {
                        console.log('⚠️ Device never registered, switching to embed')
                        onPlaybackFailed?.()
                        return
                    }
                }
            }
        } catch (e) {
            console.log('Could not verify devices:', e)
        }

        // Fallback: try with original deviceId (shouldn't reach here if above works)
        try {
            console.log('🎯 Fallback: Starting playback on device:', deviceId, retryCount > 0 ? `(attempt ${retryCount + 1})` : '')

            // Step 1: Transfer playback to this device with play=true
            const playResponse = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${accessTokenRef.current}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    uris: trackUris
                })
            })

            if (playResponse.status === 404 && retryCount < 3) {
                console.log('🔄 Device not ready, retrying...')
                return startPlayback(retryCount + 1)
            }

            if (!playResponse.ok && playResponse.status !== 204) {
                const errorData = await playResponse.json().catch(() => null)
                console.error('Failed to start playback:', playResponse.status, errorData)

                // Try transfer first, then play
                if (playResponse.status === 404 || playResponse.status === 502) {
                    console.log('📲 Trying transfer + play approach...')
                    await fetch('https://api.spotify.com/v1/me/player', {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${accessTokenRef.current}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            device_ids: [deviceId],
                            play: true
                        })
                    })

                    // Wait and try play again
                    await new Promise(resolve => setTimeout(resolve, 1000))

                    const retryPlay = await fetch(`https://api.spotify.com/v1/me/player/play?device_id=${deviceId}`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${accessTokenRef.current}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            uris: trackUris
                        })
                    })

                    if (retryPlay.ok || retryPlay.status === 204) {
                        console.log('▶️ Playback started after transfer!')
                    } else {
                        // Final attempt failed - trigger fallback to embed
                        console.log('⚠️ All SDK attempts failed, switching to embed player')
                        onPlaybackFailed?.()
                        return
                    }
                } else {
                    // Non-404/502 error - trigger fallback
                    console.log('⚠️ SDK error, switching to embed player')
                    onPlaybackFailed?.()
                    return
                }
            } else {
                console.log('▶️ Playback started with', trackUris.length, 'tracks')
            }
            setCurrentIndex(0)
        } catch (error) {
            console.error('Failed to start playback:', error)
            if (retryCount < 3) {
                return startPlayback(retryCount + 1)
            } else {
                // All retries exhausted - trigger fallback
                console.log('⚠️ SDK playback failed, triggering embed fallback')
                onPlaybackFailed?.()
            }
        }
    }

    // Toggle play/pause
    const togglePlay = useCallback(() => {
        player?.togglePlay()
    }, [player])

    // Skip to next track
    const nextTrack = useCallback(() => {
        player?.nextTrack()
        const nextIndex = Math.min(currentIndex + 1, trackUris.length - 1)
        setCurrentIndex(nextIndex)
        onTrackChange?.(nextIndex)
    }, [player, currentIndex, trackUris.length, onTrackChange])

    // Go to previous track
    const previousTrack = useCallback(() => {
        player?.previousTrack()
        const prevIndex = Math.max(currentIndex - 1, 0)
        setCurrentIndex(prevIndex)
        onTrackChange?.(prevIndex)
    }, [player, currentIndex, onTrackChange])

    // Seek to position
    const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const position = Number(e.target.value)
        setProgress(position)
        player?.seek(position)
    }, [player])

    // Set volume
    const handleVolume = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const vol = Number(e.target.value)
        setVolume(vol)
        player?.setVolume(vol / 100)
    }, [player])

    // Toggle shuffle
    const toggleShuffle = useCallback(async () => {
        if (!accessTokenRef.current) return
        const newState = !isShuffled
        try {
            const response = await fetch(`https://api.spotify.com/v1/me/player/shuffle?state=${newState}`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${accessTokenRef.current}` }
            })
            if (response.ok || response.status === 204) {
                setIsShuffled(newState)
                console.log('🔀 Shuffle:', newState ? 'ON' : 'OFF')
            }
        } catch (error) {
            console.error('Failed to toggle shuffle:', error)
        }
    }, [isShuffled])

    // Cycle repeat mode: off -> context -> track -> off
    const cycleRepeat = useCallback(async () => {
        if (!accessTokenRef.current) return
        const modes: Array<'off' | 'context' | 'track'> = ['off', 'context', 'track']
        const currentIdx = modes.indexOf(repeatMode)
        const nextMode = modes[(currentIdx + 1) % modes.length]
        try {
            const response = await fetch(`https://api.spotify.com/v1/me/player/repeat?state=${nextMode}`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${accessTokenRef.current}` }
            })
            if (response.ok || response.status === 204) {
                setRepeatMode(nextMode)
                console.log('🔁 Repeat:', nextMode)
            }
        } catch (error) {
            console.error('Failed to set repeat:', error)
        }
    }, [repeatMode])

    // Toggle like for current track
    const toggleLike = useCallback(async () => {
        if (!accessTokenRef.current || !currentTrack?.id) return
        try {
            if (isLiked) {
                // Unlike - DELETE from saved tracks
                const response = await fetch(`https://api.spotify.com/v1/me/tracks?ids=${currentTrack.id}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${accessTokenRef.current}` }
                })
                if (response.ok || response.status === 200) {
                    setIsLiked(false)
                    console.log('💔 Removed from library:', currentTrack.name)
                }
            } else {
                // Like - PUT to saved tracks
                const response = await fetch(`https://api.spotify.com/v1/me/tracks?ids=${currentTrack.id}`, {
                    method: 'PUT',
                    headers: { 'Authorization': `Bearer ${accessTokenRef.current}` }
                })
                if (response.ok || response.status === 200) {
                    setIsLiked(true)
                    console.log('💚 Added to library:', currentTrack.name)
                }
            }
        } catch (error) {
            console.error('Failed to toggle like:', error)
        }
    }, [isLiked, currentTrack])

    // Check if current track is liked when it changes
    useEffect(() => {
        const checkLiked = async () => {
            if (!accessTokenRef.current || !currentTrack?.id) {
                setIsLiked(false)
                return
            }
            try {
                const response = await fetch(`https://api.spotify.com/v1/me/tracks/contains?ids=${currentTrack.id}`, {
                    headers: { 'Authorization': `Bearer ${accessTokenRef.current}` }
                })
                if (response.ok) {
                    const [liked] = await response.json()
                    setIsLiked(liked)
                }
            } catch (error) {
                console.error('Failed to check liked status:', error)
            }
        }
        checkLiked()
    }, [currentTrack?.id])

    // Format time (ms to mm:ss)
    const formatTime = (ms: number) => {
        const seconds = Math.floor(ms / 1000)
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    // Not authenticated
    if (!isAuthenticated) {
        return null
    }

    // Loading state
    if (!isReady) {
        return (
            <div className="fixed bottom-0 left-0 right-0 bg-zinc-900/95 backdrop-blur-xl 
                          border-t border-zinc-800 p-4 text-center text-zinc-400">
                <span className="animate-pulse">🎵 Connecting to Spotify...</span>
            </div>
        )
    }

    // No tracks
    if (trackUris.length === 0) {
        return null
    }

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50">
            {/* Gradient background with glassmorphism */}
            <div className="bg-gradient-to-t from-black via-zinc-900/98 to-zinc-900/95 
                          backdrop-blur-2xl border-t border-zinc-700/50 
                          shadow-2xl shadow-black/50">

                {/* Progress bar at top - full width, thin */}
                <div className="relative h-1 bg-zinc-800 group cursor-pointer"
                    onClick={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect()
                        const percent = (e.clientX - rect.left) / rect.width
                        const newPosition = percent * (currentTrack?.duration || 0)
                        player?.seek(newPosition)
                        setProgress(newPosition)
                    }}>
                    {/* Progress fill */}
                    <div
                        className="h-full bg-gradient-to-r from-green-500 to-green-400 
                                 group-hover:from-green-400 group-hover:to-green-300
                                 transition-all duration-300"
                        style={{ width: `${(progress / (currentTrack?.duration || 1)) * 100}%` }}
                    />
                    {/* Hover dot */}
                    <div
                        className="absolute top-1/2 -translate-y-1/2 w-3 h-3 
                                 bg-white rounded-full shadow-lg opacity-0 
                                 group-hover:opacity-100 transition-opacity"
                        style={{ left: `${(progress / (currentTrack?.duration || 1)) * 100}%`, marginLeft: '-6px' }}
                    />
                </div>

                {/* Main player content */}
                <div className="max-w-6xl mx-auto px-4 py-3">
                    <div className="flex items-center gap-4">

                        {/* Left: Album Art + Track Info */}
                        <div className="flex items-center gap-3 min-w-0 flex-1 max-w-xs">
                            {/* Album Art with glow effect */}
                            <div className="relative group">
                                {currentTrack?.albumArt ? (
                                    <>
                                        <div className="absolute inset-0 bg-green-500/30 blur-xl 
                                                      opacity-0 group-hover:opacity-100 
                                                      transition-opacity rounded-xl" />
                                        <img
                                            src={currentTrack.albumArt}
                                            alt="Album art"
                                            className="w-14 h-14 rounded-lg shadow-xl relative z-10
                                                     group-hover:scale-105 transition-transform"
                                        />
                                    </>
                                ) : (
                                    <div className="w-14 h-14 rounded-lg bg-zinc-800 
                                                  flex items-center justify-center">
                                        <svg className="w-6 h-6 text-zinc-600" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
                                        </svg>
                                    </div>
                                )}
                            </div>

                            {/* Track Info */}
                            <div className="min-w-0">
                                <p className="font-semibold text-white truncate text-sm 
                                            hover:underline cursor-pointer">
                                    {currentTrack?.name || 'No track playing'}
                                </p>
                                <p className="text-xs text-zinc-400 truncate 
                                            hover:text-zinc-300 cursor-pointer">
                                    {currentTrack?.artist || 'Unknown artist'}
                                </p>
                            </div>

                            {/* Like button */}
                            <button
                                onClick={toggleLike}
                                className={`p-2 transition-all hover:scale-110 ${isLiked ? 'text-green-500' : 'text-zinc-400 hover:text-white'}`}
                                title={isLiked ? 'Remove from Liked Songs' : 'Add to Liked Songs'}
                            >
                                {isLiked ? (
                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                                    </svg>
                                ) : (
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                                    </svg>
                                )}
                            </button>
                        </div>

                        {/* Center: Controls */}
                        <div className="flex flex-col items-center gap-1">
                            {/* Control buttons */}
                            <div className="flex items-center gap-4">
                                {/* Shuffle */}
                                <button
                                    onClick={toggleShuffle}
                                    className={`p-2 transition-colors hidden sm:block relative
                                              ${isShuffled ? 'text-green-500' : 'text-zinc-500 hover:text-white'}`}
                                    title={`Shuffle ${isShuffled ? 'ON' : 'OFF'}`}
                                >
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z" />
                                    </svg>
                                    {isShuffled && <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 bg-green-500 rounded-full" />}
                                </button>

                                {/* Previous */}
                                <button
                                    onClick={previousTrack}
                                    className="p-2 text-zinc-400 hover:text-white transition-colors
                                             disabled:opacity-30 disabled:cursor-not-allowed"
                                    disabled={currentIndex === 0}
                                >
                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M6 6h2v12H6V6zm3.5 6l8.5 6V6l-8.5 6z" />
                                    </svg>
                                </button>

                                {/* Play/Pause - Main button */}
                                <button
                                    onClick={togglePlay}
                                    className="p-3 bg-white rounded-full text-black 
                                             hover:scale-110 hover:bg-white 
                                             active:scale-95 transition-all duration-200
                                             shadow-lg shadow-white/20"
                                >
                                    {isPlaying ? (
                                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                                        </svg>
                                    ) : (
                                        <svg className="w-6 h-6 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M8 5v14l11-7z" />
                                        </svg>
                                    )}
                                </button>

                                {/* Next */}
                                <button
                                    onClick={nextTrack}
                                    className="p-2 text-zinc-400 hover:text-white transition-colors
                                             disabled:opacity-30 disabled:cursor-not-allowed"
                                    disabled={currentIndex >= trackUris.length - 1}
                                >
                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M6 18l8.5-6L6 6v12zm10-12v12h2V6h-2z" />
                                    </svg>
                                </button>

                                {/* Repeat */}
                                <button
                                    onClick={cycleRepeat}
                                    className={`p-2 transition-colors hidden sm:block relative
                                              ${repeatMode !== 'off' ? 'text-green-500' : 'text-zinc-500 hover:text-white'}`}
                                    title={`Repeat: ${repeatMode.toUpperCase()}`}
                                >
                                    {repeatMode === 'track' ? (
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z" />
                                            <text x="12" y="14" fontSize="8" textAnchor="middle" fill="currentColor">1</text>
                                        </svg>
                                    ) : (
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z" />
                                        </svg>
                                    )}
                                    {repeatMode !== 'off' && <span className="absolute -bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 bg-green-500 rounded-full" />}
                                </button>
                            </div>

                            {/* Time display */}
                            <div className="flex items-center gap-2 text-xs text-zinc-500">
                                <span className="w-10 text-right">{formatTime(progress)}</span>
                                <span>/</span>
                                <span className="w-10">{formatTime(currentTrack?.duration || 0)}</span>
                            </div>
                        </div>

                        {/* Right: Volume + Extra controls */}
                        <div className="flex items-center gap-4 flex-1 justify-end max-w-xs">
                            {/* Track counter */}
                            <div className="hidden sm:flex items-center gap-1 text-xs text-zinc-500 
                                          bg-zinc-800/50 px-2 py-1 rounded-full">
                                <span className="text-green-400 font-medium">{currentIndex + 1}</span>
                                <span>/</span>
                                <span>{trackUris.length}</span>
                            </div>

                            {/* Volume control */}
                            <div className="flex items-center gap-2 group">
                                <button
                                    onClick={() => setVolume(volume > 0 ? 0 : 50)}
                                    className="text-zinc-400 hover:text-white transition-colors"
                                >
                                    {volume === 0 ? (
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z" />
                                        </svg>
                                    ) : volume < 50 ? (
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z" />
                                        </svg>
                                    ) : (
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                                        </svg>
                                    )}
                                </button>
                                <div className="w-24 hidden sm:block">
                                    <input
                                        type="range"
                                        min="0"
                                        max="100"
                                        value={volume}
                                        onChange={handleVolume}
                                        className="w-full h-1 bg-zinc-700 rounded-full appearance-none 
                                                 cursor-pointer accent-green-500
                                                 [&::-webkit-slider-thumb]:appearance-none
                                                 [&::-webkit-slider-thumb]:w-3
                                                 [&::-webkit-slider-thumb]:h-3
                                                 [&::-webkit-slider-thumb]:rounded-full
                                                 [&::-webkit-slider-thumb]:bg-white
                                                 [&::-webkit-slider-thumb]:opacity-0
                                                 [&::-webkit-slider-thumb]:group-hover:opacity-100
                                                 [&::-webkit-slider-thumb]:transition-opacity"
                                    />
                                </div>
                            </div>

                            {/* Spotify logo */}
                            <div className="hidden md:block">
                                <svg className="w-5 h-5 text-green-500" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
