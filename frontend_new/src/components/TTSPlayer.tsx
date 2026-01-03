import { useState, useRef, useEffect } from "react";

interface TTSPlayerProps {
    text: string;           // Text to speak
    autoPlay?: boolean;     // Auto-play when text changes (default: true)
    onPlayStart?: () => void;
    onPlayEnd?: () => void;
}

/**
 * TTS Player Component
 * Fetches audio from /synthesize endpoint and plays it
 * Shows simple play/pause button with loading state
 */
export default function TTSPlayer({
    text,
    autoPlay = true,
    onPlayStart,
    onPlayEnd,
}: TTSPlayerProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [shouldAutoPlay, setShouldAutoPlay] = useState(false);
    const audioRef = useRef<HTMLAudioElement>(null);

    // Fetch audio when text changes
    useEffect(() => {
        if (!text || text.trim().length === 0) return;

        // Cancel any previous audio
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }

        const fetchAudio = async () => {
            setIsLoading(true);
            setError(null);
            setShouldAutoPlay(autoPlay);

            try {
                console.log("🔊 Fetching TTS audio...");
                const response = await fetch("http://127.0.0.1:8000/synthesize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text.slice(0, 500) }),
                });

                if (!response.ok) {
                    throw new Error("TTS failed");
                }

                // Get audio blob and create URL
                const blob = await response.blob();
                console.log("🔊 TTS blob received:", blob.size, "bytes, type:", blob.type);

                // Revoke old URL before creating new one
                if (audioUrl) {
                    URL.revokeObjectURL(audioUrl);
                }

                const url = URL.createObjectURL(blob);
                console.log("🔊 Audio URL created:", url);
                setAudioUrl(url);

            } catch (err) {
                console.error("TTS error:", err);
                setError("Could not generate speech");
            } finally {
                setIsLoading(false);
            }
        };

        fetchAudio();

        // Cleanup on unmount
        return () => {
            if (audioUrl) {
                URL.revokeObjectURL(audioUrl);
            }
        };
    }, [text]);

    // Auto-play when audio is loaded
    const handleLoadedData = () => {
        console.log("🔊 Audio loaded, shouldAutoPlay:", shouldAutoPlay);
        if (shouldAutoPlay && audioRef.current) {
            audioRef.current.play()
                .then(() => {
                    console.log("🔊 Auto-play started");
                })
                .catch((err) => {
                    console.log("🔊 Auto-play blocked by browser:", err.message);
                });
            setShouldAutoPlay(false); // Only auto-play once
        }
    };

    // Handle play/pause toggle
    const togglePlayPause = () => {
        if (!audioRef.current || !audioUrl) return;

        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play().catch((err) => {
                console.error("Play failed:", err);
            });
        }
    };

    // Audio event handlers
    const handlePlay = () => {
        setIsPlaying(true);
        onPlayStart?.();
    };

    const handlePause = () => {
        setIsPlaying(false);
    };

    const handleEnded = () => {
        setIsPlaying(false);
        onPlayEnd?.();
    };

    const handleError = (e: React.SyntheticEvent<HTMLAudioElement>) => {
        console.error("🔊 Audio error:", e);
        setError("Audio playback failed");
    };

    return (
        <div className="tts-player">
            {/* Hidden audio element */}
            <audio
                ref={audioRef}
                src={audioUrl || undefined}
                onLoadedData={handleLoadedData}
                onPlay={handlePlay}
                onPause={handlePause}
                onEnded={handleEnded}
                onError={handleError}
                preload="auto"
            />

            {/* Play/Pause button */}
            <button
                className={`tts-play-button ${isPlaying ? "playing" : ""} ${isLoading ? "loading" : ""}`}
                onClick={togglePlayPause}
                disabled={isLoading || !audioUrl}
                title={isPlaying ? "Pause" : "Play mood summary"}
            >
                {isLoading ? (
                    <span className="tts-spinner">⏳</span>
                ) : isPlaying ? (
                    "⏸️"
                ) : (
                    "🔊"
                )}
            </button>

            {/* Error indicator */}
            {error && <span className="tts-error" title={error}>⚠️</span>}
        </div>
    );
}
