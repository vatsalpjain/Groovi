"""Configuration management - All environment variables in one place"""

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Centralized settings for API keys and configuration"""
    
    # Spotify API
    SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
    SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
    
    # AI Services
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Local Audio Models (no API keys needed)
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny, base, small, medium
    PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
    
    # CORS - Frontend URLs allowed to access API
    ALLOWED_ORIGINS = [
        "http://localhost:3000",   # React dev server
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173"    # Alternative localhost
    ]
    
    # API Metadata
    API_TITLE = "Groovi Music Recommender API"
    API_VERSION = "1.0.0"
    
    # Validation
    @classmethod
    def validate(cls):
        """Ensure required credentials exist"""
        if not cls.SPOTIPY_CLIENT_ID or not cls.SPOTIPY_CLIENT_SECRET:
            raise ValueError("❌ Spotify credentials missing in .env file")
        return True

settings = Settings()
settings.validate()
