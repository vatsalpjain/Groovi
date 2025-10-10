import "./App.css";
import { useState, useRef } from "react";
import AudioRecorder from "./components/AudioRecorder";
import AudioUploader from "./components/AudioUploader";
import ScrollVelocity from "./components/ScrollVelocity";
import GlareHover from "./components/GlareHover";
import LottieRobot from "./components/LottieRobot";
import type { LottieRobotHandle } from "./components/LottieRobot";

// Define TypeScript interfaces for the API response
interface MoodAnalysis {
  category: string;
  description: string;
  summary: string;
  score: number;
  intensity: string;
}

interface Song {
  name: string;
  artist: string;
  album_art: string;
  uri: string;
  external_url: string;
}

interface ApiResponse {
  mood_analysis: MoodAnalysis;
  songs: Song[];
}

function App() {
  // State to store what the user types
  const [moodText, setMoodText] = useState("");
  // State to track if we're loading
  const [isLoading, setIsLoading] = useState(false);
  // State to store the API response
  const [recommendations, setRecommendations] = useState<Song[]>([]);
  const [moodAnalysis, setMoodAnalysis] = useState<MoodAnalysis | null>(null);
  // State to handle errors
  const [error, setError] = useState("");
  // State for success message
  const [showSuccess, setShowSuccess] = useState(false);
  // State to track if audio is uploading
  const [isUploading, setIsUploading] = useState(false);
  // State to track if robot is dancing
  const [isDancing, setIsDancing] = useState(false);
  // State to track which song is playing
  const [playingSongUri, setPlayingSongUri] = useState<string | null>(null);
  const [embeddedTrackUri, setEmbeddedTrackUri] = useState<string | null>(null);

  // TWO separate refs
  const robotRef1 = useRef<LottieRobotHandle>(null);
  const robotRef2 = useRef<LottieRobotHandle>(null);

  // Function to handle when user clicks the button
  const handleGetRecommendations = async () => {
    if (!moodText.trim()) return;

    setIsLoading(true);
    setError("");
    setShowSuccess(false);
    setRecommendations([]);
    setMoodAnalysis(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommend", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: moodText }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}. Please try again.`);
      }

      const data: ApiResponse = await response.json();

      if (!data.songs || data.songs.length === 0) {
        throw new Error(
          "No songs found for your mood. Try a different description."
        );
      }

      setRecommendations(data.songs);
      setMoodAnalysis(data.mood_analysis);
      setShowSuccess(true);

      // Auto-hide success message after 3 seconds
      setTimeout(() => setShowSuccess(false), 3000);

      // Scroll to results area after songs are loaded
      setTimeout(() => {
        const resultsArea = document.querySelector(".results-area");
        if (resultsArea) {
          resultsArea.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }, 500);
    } catch (err) {
      let errorMessage = "Something went wrong. Please try again.";

      if (err instanceof Error) {
        if (err.message.includes("fetch")) {
          errorMessage =
            "Can't connect to server. Make sure the backend is running.";
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to handle song click - embed player and start dancing
  const handleSongClick = (songUri: string, externalUrl: string) => {
    // Start dancing
    setIsDancing(true);
    setPlayingSongUri(songUri);
    
    if (robotRef1.current) {
      robotRef1.current.dance();
    }
    if (robotRef2.current) {
      robotRef2.current.dance();
    }

    // Extract track ID from Spotify URI (spotify:track:XXXXX)
    const trackId = songUri.split(':')[2];
    setEmbeddedTrackUri(trackId);

    // Scroll to player
    setTimeout(() => {
      const player = document.querySelector('.spotify-player');
      if (player) {
        player.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 300);
  };

  // Function to close the player and stop dancing
  const handleClosePlayer = () => {
    setEmbeddedTrackUri(null);
    setPlayingSongUri(null);
    setIsDancing(false);
    
    if (robotRef1.current) {
      robotRef1.current.stop();
    }
    if (robotRef2.current) {
      robotRef2.current.stop();
    }
  };

  // Handle Enter key in textarea
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && e.ctrlKey && !isLoading && moodText.trim()) {
      handleGetRecommendations();
    }
  };

  // Handle transcript from audio
  const handleTranscriptReceived = (transcript: string) => {
    setMoodText(transcript);
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  // Handle audio errors
  const handleAudioError = (errorMsg: string) => {
    setError(errorMsg);
  };

  return (
    <div className="app">
      <header className="app-header">
        {/* Only show robots at top when no results */}
        {!moodAnalysis && (
          <>
            {/* Robot 1 - Top Left */}
            <LottieRobot
              ref={robotRef1}
              className={isDancing ? 'dancing' : ''}
              style={{
                top: "10%",
                left: "5%",
                width: "400px",
                height: "400px",
                opacity: 0.8,
              }}
            />
            
            {/* Robot 2 - Top Right */}
            <LottieRobot
              ref={robotRef2}
              className={isDancing ? 'dancing' : ''}
              style={{
                top: "10%",
                right: "5%",
                width: "400px",
                height: "400px",
                opacity: 0.8,
              }}
            />
          </>
        )}
       
        <h1>Groovi</h1>
        <p>
          Describe your mood with text or voice, and we'll find the perfect
          soundtrack for you.
        </p>

        <div className="input-area">
          {/* Audio Input Options */}
          <div className="audio-input-section">
            <AudioRecorder
              onTranscriptReceived={handleTranscriptReceived}
              onError={handleAudioError}
            />
            <AudioUploader
              onTranscriptReceived={handleTranscriptReceived}
              onError={handleAudioError}
              onUploading={setIsUploading}
            />
          </div>

          {/* Existing Text Input */}
          <textarea
            value={moodText}
            onChange={(e) => setMoodText(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="e.g., 'I had a fantastic day and I'm ready to celebrate!' (Ctrl+Enter to submit)"
            rows={4}
          />
          <GlareHover
            glareColor="#ffffff"
            glareOpacity={0.3}
            glareAngle={-30}
            glareSize={300}
            transitionDuration={800}
            playOnce={false}
          >
            <button
              onClick={handleGetRecommendations}
              disabled={isLoading || isUploading || !moodText.trim()}
              className="simple-vibe-button"
            >
              {isLoading
                ? "Finding your vibe..."
                : isUploading
                ? "Processing audio..."
                : "Get My Vibe"}
            </button>
          </GlareHover>
          <div className="char-counter">{moodText.length}/500 characters</div>
        </div>
      </header>
      
      <ScrollVelocity
        texts={["🎵 Groovi", "✨ Your Vibe"]}
        velocity={50}
        className="text-white/20"
      />
      
      <main className="results-area">
        {/* Success message */}
        {showSuccess && (
          <div className="success">
            🎵 Found {recommendations.length} perfect songs for your mood!
          </div>
        )}

        {/* Error message */}
        {error && <div className="error">{error}</div>}

        {/* Embedded Spotify Player with Close Button */}
        {embeddedTrackUri && (
          <div className="spotify-player" style={{
            marginBottom: '2rem',
            borderRadius: '24px',
            overflow: 'hidden',
            boxShadow: '0 20px 40px rgba(168, 85, 247, 0.3)',
            animation: 'card-slide-up 0.6s ease-out',
            position: 'relative'
          }}>
            <button
              onClick={handleClosePlayer}
              style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                zIndex: 100,
                background: 'rgba(239, 68, 68, 0.9)',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '32px',
                height: '32px',
                cursor: 'pointer',
                fontSize: '18px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 12px rgba(239, 68, 68, 0.4)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'scale(1.1)';
                e.currentTarget.style.background = 'rgba(220, 38, 38, 1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.9)';
              }}
              title="Close player and stop dancing"
            >
              ✕
            </button>
            <iframe
              src={`https://open.spotify.com/embed/track/${embeddedTrackUri}?utm_source=generator&theme=0`}
              width="100%"
              height="152"
              frameBorder="0"
              allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
              loading="lazy"
              style={{ borderRadius: '24px' }}
            ></iframe>
          </div>
        )}

        {/* Mood analysis with robots */}
        {moodAnalysis && (
          <div className="mood-summary">
            {/* Robot 1 - Beside Summary Left - Use fixed positioning */}
            <div style={{ position: 'relative', width: '100%', minHeight: '300px' }}>
              <LottieRobot
                ref={robotRef1}
                className={isDancing ? 'dancing' : ''}
                style={{
                  position: 'fixed',
                  top: '40%',
                  left: '2%',
                  transform: 'translateY(-50%)',
                  width: isDancing ? "400px" : "350px",
                  height: isDancing ? "400px" : "350px",
                  opacity: isDancing ? 1 : 0.8,
                  zIndex: 10,
                }}
              />
              
              {/* Robot 2 - Beside Summary Right - Use fixed positioning */}
              <LottieRobot
                ref={robotRef2}
                className={isDancing ? 'dancing' : ''}
                style={{
                  position: 'fixed',
                  top: '40%',
                  right: '2%',
                  transform: 'translateY(-50%)',
                  width: isDancing ? "400px" : "350px",
                  height: isDancing ? "400px" : "350px",
                  opacity: isDancing ? 1 : 0.8,
                  zIndex: 10,
                }}
              />

              <h2>Your Mood Analysis</h2>
              <div className="mood-card">
                <div className="mood-category">
                  <span className="mood-label">{moodAnalysis.category}</span>
                  <span className="mood-intensity">
                    ({moodAnalysis.intensity} intensity)
                  </span>
                </div>

                <p className="mood-summary-text">{moodAnalysis.summary}</p>
                <p className="mood-description">{moodAnalysis.description}</p>
                <div className="mood-score">
                  Sentiment Score:{" "}
                  <span className="score-value">
                    {moodAnalysis.score.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Songs section */}
        {recommendations.length > 0 && (
          <div className="songs-section">
            <h2>Your Personalized Playlist</h2>
            <p className="songs-subtitle">
              Top {recommendations.length} songs curated for your current mood (Click to preview!)
            </p>
          </div>
        )}

        <div className="song-list">
          {recommendations.map((song, index) => (
            <div
              key={song.uri}
              className={`song-item ${playingSongUri === song.uri ? 'playing' : ''}`}
              onClick={() => handleSongClick(song.uri, song.external_url)}
              style={{ animationDelay: `${index * 0.15}s` }}
              title={`Preview ${song.name} by ${song.artist}`}
            >
              <img
                src={song.album_art}
                alt={`${song.name} album cover`}
                className="album-art"
                loading="lazy"
              />
              <div className="song-details">
                <p className="song-name">{song.name}</p>
                <p className="song-artist">{song.artist}</p>
              </div>
              <div className="play-indicator">
                {playingSongUri === song.uri ? '🔊' : '▶'}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;
