"""Pydantic models for API request/response validation"""

from pydantic import BaseModel, Field
from typing import List, Optional

class TextInput(BaseModel):
    """
    Request model for mood analysis
    User sends their mood text to /recommend endpoint
    """
    text: str = Field(..., min_length=1, max_length=1000, description="User's mood text")
    
    class Config:
        json_schema_extra = {
            "example": {"text": "I'm feeling really happy today!"}
        }

class TTSRequest(BaseModel):
    """Request model for text-to-speech synthesis"""
    text: str = Field(..., min_length=1, max_length=500, description="Text to convert to speech")

class TranscriptionResponse(BaseModel):
    """Audio transcription result"""
    transcript: str = Field(..., description="Transcribed text from audio")
    filename: str = Field(..., description="Original filename")
    duration_estimate: float = Field(..., description="Estimated audio duration in seconds")

class MoodAnalysis(BaseModel):
    """Mood analysis result"""
    category: str = Field(..., description="Mood category (e.g., happy, sad, energetic)")
    description: str = Field(..., description="Reasoning for song selection based on mood analysis")

class Song(BaseModel):
    """Spotify track information"""
    name: str
    artist: str
    uri: str
    album_art: Optional[str] = None
    external_url: str

class RecommendationResponse(BaseModel):
    """Complete API response"""
    mood_analysis: MoodAnalysis
    songs: List[Song] = Field(..., min_length=1, max_length=10)

class PlaylistCreateRequest(BaseModel):
    """Request to create a Spotify playlist"""
    name: str
    track_uris: List[str]
    description: str = ""
    public: bool = False

class RecommendationRequest(BaseModel):
    """Request for mood-based recommendations"""
    mood: str
    limit: int = 5

class PlaybackRequest(BaseModel):
    """Request to control Spotify playback"""
    uris: Optional[List[str]] = None
    device_id: Optional[str] = None

class PlaylistAddRequest(BaseModel):
    """Request to add tracks to a playlist"""
    playlist_id: str
    track_uris: List[str]