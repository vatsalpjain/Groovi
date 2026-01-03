# Groovi Project - AI Agent Instructions

## 🚨 CRITICAL WORKFLOW RULES (Read First!)

**This is a resume project - the developer is in complete control.**

1. **Write code with comments** (concise, not verbose)
2. **Explain everything you do** - no silent changes
3. **Ask before making decisions** about structure, tech choices, or implementation approaches
4. **Go step-by-step** - do ONE thing, explain it, wait for approval before proceeding
5. **User approval required** - never assume the next step
6. **No need to create any md to explain**- never create md just talk in chat

**Example:** "I've implemented X. Should I proceed with Y, or would you like to review/modify X first?"

---

## Project Overview
Groovi - AI-Powered Mood-Based Music Recommender

**📖 Full Documentation:** Read [README.md](./README.md) for complete architecture, setup, and API documentation.

## Architecture (Quick Reference)
- **Backend** (`backend_new/`): FastAPI application with modular services
- **Frontend** (`frontend_new/`): React 18 + TypeScript + Vite
- **Mood Analysis** (`services/mood_analyzer.py`): Groq LLM (Llama 4 Maverick) + VADER fallback
- **Music Recommendations** (`services/song_recommender.py`): Multi-strategy Spotify search
- **Audio Transcription** (`services/audio_transcriber.py`): Deepgram API integration
- **Spotify Integration** (`services/spotify_client.py`): Spotipy wrapper for music data
- **Config** (`config/settings.py`): Environment-based configuration with python-dotenv

## Code Conventions (Project-Specific)

### Import Order
```python
# Standard library
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party (alphabetical)
from fastapi import FastAPI, HTTPException
from groq import Groq
import spotipy

# Local (alphabetical)
from config.settings import settings
from services.mood_analyzer import MoodAnalyzer
```

### API Error Handling
- Catch specific exceptions, use meaningful HTTP status codes
- Always return consistent JSON response structure: `{"error": str, "detail": str}`
- Log errors with context for debugging
- Use FastAPI's `HTTPException` for API errors

### Response Format (All API Endpoints)
```python
# Recommendation Response
{
    "mood_analysis": {
        "category": str,      # e.g., "Very Positive"
        "description": str,   # Short mood description
        "summary": str,       # 100-word AI-generated summary
        "score": float,       # Sentiment score (-1 to 1)
        "intensity": str      # "low", "moderate", "high"
    },
    "songs": [
        {
            "name": str,
            "artist": str,
            "uri": str,           # Spotify URI
            "album_art": str,     # Album artwork URL
            "external_url": str   # Spotify web link
        }
    ]
}
```

### Service Design Rules
- Each service should be independent and testable
- Use dependency injection for external clients (Spotify, Groq, Deepgram)
- Implement fallback mechanisms for API failures
- Keep API keys in environment variables, never hardcode

## Quick Reference

### Key Files
- [README.md](./README.md): Full documentation, setup, and API reference
- [main.py](./backend_new/main.py): FastAPI routes & application entry point
- [settings.py](./backend_new/config/settings.py): Environment configuration
- [mood_analyzer.py](./backend_new/services/mood_analyzer.py): AI mood analysis logic
- [song_recommender.py](./backend_new/services/song_recommender.py): Spotify recommendation strategies
- [App.tsx](./frontend_new/src/App.tsx): Main React component

### External Services
- **Groq**: LLM for mood analysis (Llama 4 Maverick, temp=0.7)
- **Spotify**: Music data via Spotipy (Client Credentials flow)
- **Deepgram**: Speech-to-text for audio transcription
- **VADER**: Fallback sentiment analysis (offline, rule-based)

### Backend Services Layer
| Service | File | Purpose |
|---------|------|---------|
| MoodAnalyzer | `mood_analyzer.py` | Groq AI + VADER sentiment analysis |
| SongRecommender | `song_recommender.py` | Multi-strategy Spotify search |
| SpotifyClient | `spotify_client.py` | Spotipy wrapper & authentication |
| AudioTranscriber | `audio_transcriber.py` | Deepgram audio-to-text |

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/recommend` | Analyze mood → Get 5 song recommendations |
| POST | `/transcribe` | Convert audio file to text |

### Frontend Components
| Component | File | Purpose |
|-----------|------|---------|
| App | `App.tsx` | Main UI, mood input, song display |
| AudioRecorder | `AudioRecorder.tsx` | Browser microphone recording |
| AudioUploader | `AudioUploader.tsx` | Audio file upload handling |

### Anti-Patterns
- ❌ Hardcode API keys → ✅ Load from `.env` via settings
- ❌ Generic exception catching → ✅ Specific exceptions with context
- ❌ No fallback for API failures → ✅ Always have fallback data/logic
- ❌ Blocking synchronous calls → ✅ Use async where beneficial
- ❌ Missing CORS configuration → ✅ Configure allowed origins in settings
