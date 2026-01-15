"""
Groovi Music Recommender API
Uses MCP protocol (stdio) for Spotify integration
"""
import logging
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.schemas import TextInput, RecommendationResponse, TranscriptionResponse, TTSRequest
from services.mood_analyzer import mood_analyzer
from services.local_audio_service import get_local_audio_service
from services.spotify_auth import spotify_auth
from services.mcp_client import get_mcp_client
from config.settings import settings
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Initialize FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered mood analysis and song recommendations via MCP"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Request Models ====================

class PlaylistCreateRequest(BaseModel):
    """Request to create a Spotify playlist"""
    name: str
    track_uris: List[str]
    description: str = ""
    public: bool = False
class RecommendationRequest(BaseModel):
    mood: str
    limit: int = 5

class PlaybackRequest(BaseModel):
    uris: Optional[List[str]] = None
    device_id: Optional[str] = None

class PlaylistAddRequest(BaseModel):
    playlist_id: str
    track_uris: List[str]

# ==================== Spotify OAuth ====================

@app.get("/auth/login")
async def auth_login():
    """Get Spotify OAuth authorization URL"""
    return {"auth_url": spotify_auth.get_auth_url()}

@app.get("/auth/login/redirect")
async def auth_login_redirect():
    """Redirect directly to Spotify OAuth"""
    return RedirectResponse(url=spotify_auth.get_auth_url())

@app.get("/callback")
async def auth_callback(code: str = Query(...), state: Optional[str] = None):
    """Handle Spotify OAuth callback"""
    try:
        spotify_auth.exchange_code(code)
        
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head><title>Spotify Connected</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✅ Spotify Connected!</h1>
            <p>You can close this window.</p>
            <script>
                if (window.opener) {
                    window.opener.postMessage({ type: 'spotify-auth-success' }, '*');
                    setTimeout(() => window.close(), 1500);
                }
            </script>
        </body>
        </html>
        """)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@app.get("/auth/token")
async def get_token():
    """Get current access token for Web Playback SDK"""
    token = spotify_auth.get_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    return {"access_token": token}

@app.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    return {
        "authenticated": spotify_auth.is_authenticated(),
        "user": spotify_auth.get_user_info()
    }

# ==================== Health Check ====================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "Groovi API is running!",
        "version": settings.API_VERSION,
        "status": "healthy",
        "mcp_transport": "stdio"  
    }

# ==================== Audio Transcription ====================

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text using local Faster-Whisper
    
    Accepts: mp3, wav, webm, ogg, m4a
    Returns: Transcribed text
    """
    allowed_types = ["audio/mpeg", "audio/wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/x-m4a"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    try:
        audio_data = await audio.read()
        
        if len(audio_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max 10MB allowed.")
        
        # Use consolidated local audio service
        local_service = get_local_audio_service()
        transcript = local_service.transcribe_audio_bytes(audio_data)
        
        return {
            "transcript": transcript,
            "filename": audio.filename,
            "duration_estimate": len(audio_data) / (16000 * 2)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# ==================== Mood Analysis & Recommendations ====================

@app.post("/recommend")
async def recommend_songs(text_input: TextInput):
    """
    AI Agent-based music recommendation via MCP
    
    Flow:
    1. Use AI Agent with Groq function calling
    2. Agent explores Spotify via MCP tools (stdio)
    3. Agent curates 5 best tracks with reasoning
    4. Returns tracks + thought process for UI display
    """
    if not text_input.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    user_query = text_input.text.strip()
    logger.info(f"🎵 User query: {user_query}")
    
    # Import agent here to avoid circular imports
    from services.music_agent import MusicRecommendationAgent
    from groq import Groq
    
    try:
        # Initialize Groq client and agent
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        agent = MusicRecommendationAgent(groq_client)
        
        # Run the agent (uses MCP client internally)
        result = await agent.run(user_query)
        await agent.close()
        
        # Check if agent succeeded
        if "error" in result:
            logger.error(f"❌ Agent error: {result.get('error')}")
            return await fallback_recommend(user_query)
        
        # Format response
        tracks = result.get("tracks", [])
        if not tracks:
            return await fallback_recommend(user_query)
        
        # Format songs for frontend
        songs = []
        for track in tracks[:5]:
            songs.append({
                "name": track.get("name", "Unknown"),
                "artist": track.get("artist", "Unknown"),
                "uri": track.get("uri", ""),
                "album_art": track.get("album_art", ""),
                "external_url": track.get("external_url", ""),
                "reason": track.get("reason", "")
            })
        
        return {
            "mood_analysis": {
                "category": result.get("mood", "neutral"),
                "description": result.get("summary", ""),
                "summary": result.get("summary", ""),
                "score": 0.5,
                "intensity": "moderate"
            },
            "songs": songs,
            "thought_process": result.get("thought_process", []),
            "agent_iterations": result.get("iterations", 0)
        }
        
    except Exception as e:
        logger.error(f"❌ Agent failed: {e}")
        return await fallback_recommend(user_query)

async def fallback_recommend(user_query: str):
    """
    Fallback to simple mood-based recommendation when agent fails.
    Uses MCP client via stdio instead of HTTP.
    """
    # Analyze mood with Groq/VADER
    mood_analysis, _ = mood_analyzer.analyze(user_query)
    mood_category = mood_analysis['mood_category']
    
    logger.info(f"🎯 Fallback: Using mood '{mood_category}'")
    
    try:
        # Use MCP client to search for tracks
        async with get_mcp_client() as mcp:
            # Search based on mood
            mood_queries = {
                "happy": "happy upbeat feel good",
                "energetic": "energetic pump up workout",
                "calm": "calm relaxing peaceful",
                "sad": "emotional sad melancholy",
                "angry": "intense angry powerful",
                "anxious": "soothing calm ambient",
                "romantic": "love romantic ballad",
                "neutral": "popular hits top"
            }
            query = mood_queries.get(mood_category, "popular hits")
            
            result = await mcp.call_tool("search_tracks", {"query": query, "limit": 5})
            songs = result.get("tracks", [])
        
    except Exception as e:
        logger.error(f"❌ MCP fallback failed: {e}")
        # Ultimate fallback - use curated library
        from data.mood_libraries import MOOD_SONG_LIBRARIES
        import random
        
        curated = MOOD_SONG_LIBRARIES.get(mood_category, [])
        songs = random.sample(curated, min(5, len(curated)))
        songs = [{
            "name": s["name"],
            "artist": s["artist"],
            "uri": f"spotify:search:{s['name']} {s['artist']}",
            "album_art": "",
            "external_url": f"https://open.spotify.com/search/{s['name']}"
        } for s in songs]
    
    return {
        "mood_analysis": {
            "category": mood_analysis['mood_category'],
            "description": mood_analysis['mood_description'],
            "summary": mood_analysis['summary'],
            "score": mood_analysis['score'],
            "intensity": mood_analysis['intensity']
        },
        "songs": songs[:5],
        "thought_process": [],
        "agent_iterations": 0
    }

# ==================== Spotify Playlist Management ====================

@app.post("/playlist/create")
async def create_playlist(request: PlaylistCreateRequest):
    """
    Create a Spotify playlist via MCP
    
    Requires user to be authenticated with Spotify.
    """
    if not spotify_auth.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated. Login first.")
    
    try:
        async with get_mcp_client() as mcp:
            result = await mcp.call_tool("create_playlist", {
                "name": request.name,
                "description": request.description,
                "track_uris": request.track_uris
            })
            
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])
            
            return {"playlist": result.get("playlist")}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Playlist creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Playlist creation failed: {str(e)}")


@app.get("/spotify/auth/status")
async def spotify_auth_status():
    """Check if user is authenticated with Spotify"""
    return {
        "authenticated": spotify_auth.is_authenticated(),
        "user": spotify_auth.get_user_info()
    }

# ==================== Text-to-Speech ====================

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using local Piper TTS
    
    Accepts: JSON {"text": "Your text here"}
    Returns: WAV audio file
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    text = request.text.strip()
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text too long. Max 500 characters.")
    
    try:
        local_service = get_local_audio_service()
        audio_path = local_service.synthesize(text)
        
        return FileResponse(
            path=audio_path,
            media_type="audio/wav",
            filename="groovi_speech.wav",
            background=None
        )
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"TTS service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")


# ==================== Server Startup ====================

def start_server():
    logger.info("🎵 Starting Groovi Backend Server...")
    logger.info("📡 Server: http://localhost:5000")
    logger.info("📚 API Docs: http://localhost:5000/docs")
    logger.info("� MCP Transport: stdio")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()