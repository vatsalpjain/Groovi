"""
Groovi Music Recommender API
Clean routes that delegate to service layer
"""
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import TextInput, RecommendationResponse, TranscriptionResponse, TTSRequest
from services.mood_analyzer import mood_analyzer
from services.song_recommender import song_recommender
from services.audio_transcriber import audio_transcriber
from services.local_audio_service import get_local_audio_service
from config.settings import settings

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

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "Groovi API is running!",
        "version": settings.API_VERSION,
        "status": "healthy"
    }

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file to text using local Faster-Whisper
    
    Accepts: mp3, wav, webm, ogg, m4a
    Returns: Transcribed text
    """
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/x-m4a"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read audio data
    try:
        audio_data = await audio.read()
        
        # Check file size (max 10MB)
        if len(audio_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Max 10MB allowed.")
        
        # Transcribe audio
        transcript = audio_transcriber.transcribe_audio(audio_data)
        
        return {
            "transcript": transcript,
            "filename": audio.filename,
            "duration_estimate": len(audio_data) / (16000 * 2)  # Rough estimate
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/recommend", response_model=RecommendationResponse)
def recommend_songs(text_input: TextInput):
    """
    Analyze mood and recommend songs
    
    Flow:
    1. Analyze mood (Groq or VADER)
    2. Get song recommendations (Groq → Spotify → Fallback)
    3. Return mood analysis + 5 songs
    """
    if not text_input.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Step 1: Analyze mood
    mood_analysis, groq_song_recs = mood_analyzer.analyze(text_input.text)
    
    # Step 2: Get songs
    songs = song_recommender.recommend(mood_analysis, groq_song_recs)
    
    if not songs:
        raise HTTPException(status_code=404, detail="Could not find song recommendations")
    
    # Step 3: Return formatted response
    return {
        "mood_analysis": {
            "category": mood_analysis['mood_category'],
            "description": mood_analysis['mood_description'],
            "summary": mood_analysis['summary'],
            "score": mood_analysis['score'],
            "intensity": mood_analysis['intensity']
        },
        "songs": songs[:5]
    }


@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    Convert text to speech using local Piper TTS
    
    Accepts: JSON {"text": "Your text here"}
    Returns: WAV audio file
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Validate text length (max 500 chars)
    text = request.text.strip()
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="Text too long. Max 500 characters.")
    
    try:
        # Get local audio service and synthesize
        local_service = get_local_audio_service()
        audio_path = local_service.synthesize(text)
        
        # Return audio file
        return FileResponse(
            path=audio_path,
            media_type="audio/wav",
            filename="groovi_speech.wav",
            background=None  # Don't delete file until response is sent
        )
        
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"TTS service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

def start_server():
    print("🎵 Starting Groovi Backend Server...")
    print("📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    start_server()