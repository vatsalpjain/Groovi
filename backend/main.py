"""
Groovi Music Recommender API
Clean routes that delegate to service layer

Now uses Spotify MCP for recommendations instead of direct Spotify API calls.
"""
import httpx
import uvicorn
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models.schemas import TextInput, RecommendationResponse, TranscriptionResponse, TTSRequest
from services.mood_analyzer import mood_analyzer
from services.audio_transcriber import audio_transcriber
from services.local_audio_service import get_local_audio_service
from config.settings import settings

# MCP Server URL
MCP_URL = "http://localhost:5000"

# Initialize FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered mood analysis and song recommendations"
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


# ==================== Health Check ====================

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "Groovi API is running!",
        "version": settings.API_VERSION,
        "status": "healthy",
        "mcp_url": MCP_URL
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
        
        transcript = audio_transcriber.transcribe_audio(audio_data)
        
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
    AI Agent-based music recommendation
    
    Flow:
    1. Use AI Agent with Groq function calling
    2. Agent explores Spotify via MCP tools
    3. Agent curates 5 best tracks with reasoning
    4. Returns tracks + thought process for UI display
    """
    if not text_input.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    user_query = text_input.text.strip()
    print(f"🎵 User query: {user_query}")
    
    # Import agent here to avoid circular imports
    from services.music_agent import MusicRecommendationAgent
    from groq import Groq
    
    try:
        # Initialize Groq client and agent
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        agent = MusicRecommendationAgent(groq_client)
        
        # Run the agent
        result = await agent.run(user_query)
        await agent.close()
        
        # Check if agent succeeded
        if "error" in result:
            print(f"❌ Agent error: {result.get('error')}")
            # Fall back to simple mood-based search
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
                "reason": track.get("reason", "")  # Why this track was chosen
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
            "thought_process": result.get("thought_process", []),  # Agent's reasoning
            "agent_iterations": result.get("iterations", 0)
        }
        
    except Exception as e:
        print(f"❌ Agent failed: {e}")
        # Fall back to simple approach
        return await fallback_recommend(user_query)


async def fallback_recommend(user_query: str):
    """
    Fallback to simple mood-based recommendation when agent fails
    """
    # Analyze mood with Groq
    mood_analysis, _ = mood_analyzer.analyze(user_query)
    mood_category = mood_analysis['mood_category']
    
    print(f"🎯 Fallback: Using mood '{mood_category}'")
    
    # Get recommendations from MCP
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MCP_URL}/recommendations",
                json={"mood": mood_category, "limit": 5}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to get recommendations")
            
            mcp_data = response.json()
            songs = mcp_data.get("tracks", [])
            
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="MCP server not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")
    
    return {
        "mood_analysis": {
            "category": mood_analysis['mood_category'],
            "description": mood_analysis['mood_description'],
            "summary": mood_analysis['summary'],
            "score": mood_analysis['score'],
            "intensity": mood_analysis['intensity']
        },
        "songs": songs[:5],
        "thought_process": [],  # No agent thoughts in fallback
        "agent_iterations": 0
    }


# ==================== Spotify Playlist Management ====================

@app.post("/playlist/create")
async def create_playlist(request: PlaylistCreateRequest):
    """
    Create a Spotify playlist via MCP
    
    Requires user to be authenticated with Spotify via MCP.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MCP_URL}/playlist/create",
                json={
                    "name": request.name,
                    "description": request.description,
                    "public": request.public,
                    "track_uris": request.track_uris
                }
            )
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Not authenticated. Login via MCP first.")
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to create playlist")
            
            return response.json()
            
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="MCP server not available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Playlist creation failed: {str(e)}")


@app.get("/spotify/auth/status")
async def spotify_auth_status():
    """Check if user is authenticated with Spotify via MCP"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{MCP_URL}/auth/status")
            return response.json()
    except Exception:
        return {"authenticated": False, "mcp_available": False}


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
    print("🎵 Starting Groovi Backend Server...")
    print("📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print(f"🔗 MCP Server: {MCP_URL}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()