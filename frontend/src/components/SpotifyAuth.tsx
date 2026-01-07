import { useState, useEffect } from 'react'

// MCP Server URL
const MCP_URL = 'http://localhost:5000'

interface SpotifyAuthProps {
    onAuthChange?: (isAuthenticated: boolean) => void
}

/**
 * SpotifyAuth - Spotify OAuth login button
 * 
 * Opens OAuth popup, handles callback, and shows connection status.
 */
export function SpotifyAuth({ onAuthChange }: SpotifyAuthProps) {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    // Check auth status on mount
    useEffect(() => {
        checkAuthStatus()
    }, [])

    // Listen for OAuth callback message from popup
    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            if (event.data?.type === 'spotify-auth-success') {
                setIsAuthenticated(true)
                onAuthChange?.(true)
            }
        }

        window.addEventListener('message', handleMessage)
        return () => window.removeEventListener('message', handleMessage)
    }, [onAuthChange])

    // Check if already authenticated
    const checkAuthStatus = async () => {
        try {
            const response = await fetch(`${MCP_URL}/auth/status`)
            const data = await response.json()
            setIsAuthenticated(data.authenticated)
            onAuthChange?.(data.authenticated)
        } catch (error) {
            console.error('Failed to check auth status:', error)
            setIsAuthenticated(false)
        } finally {
            setIsLoading(false)
        }
    }

    // Open OAuth login popup
    const handleLogin = async () => {
        try {
            const response = await fetch(`${MCP_URL}/auth/login`)
            const data = await response.json()

            // Open popup for OAuth flow
            const width = 500
            const height = 700
            const left = window.screenX + (window.outerWidth - width) / 2
            const top = window.screenY + (window.outerHeight - height) / 2

            window.open(
                data.auth_url,
                'Spotify Login',
                `width=${width},height=${height},left=${left},top=${top}`
            )
        } catch (error) {
            console.error('Failed to start OAuth flow:', error)
        }
    }

    // Loading state
    if (isLoading) {
        return (
            <div className="flex items-center gap-2 text-zinc-400">
                <span className="animate-pulse">●</span>
                Checking Spotify...
            </div>
        )
    }

    // Authenticated state
    if (isAuthenticated) {
        return (
            <div className="flex items-center gap-2 px-4 py-2 rounded-xl 
                          bg-green-500/10 border border-green-500/30 text-green-500">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
                </svg>
                <span className="font-medium">Connected</span>
            </div>
        )
    }

    // Not authenticated - show login button
    return (
        <button
            onClick={handleLogin}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium
                     bg-[#1DB954] hover:bg-[#1ed760] text-white
                     transition-all duration-200 hover:scale-105"
        >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z" />
            </svg>
            Connect Spotify
        </button>
    )
}
