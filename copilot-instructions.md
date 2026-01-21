# Groovi Project - AI Agent Instructions

## 🚨 CRITICAL WORKFLOW RULES - MANDATORY COMPLIANCE

### RULE 1: CODE DOCUMENTATION (REQUIRED)

* **ALWAYS** write concise, meaningful comments in code
* Comments must explain  **WHY** , not just **WHAT**
* No verbose explanations - keep comments brief and purposeful
* **NO EXCEPTIONS** - all code must include comments

### RULE 2: TRANSPARENCY (REQUIRED)

* **EXPLAIN EVERY CHANGE** you make before and after implementing it
* Never make silent modifications to the codebase
* State clearly: "I am doing X because Y"
* After changes: "I have completed X, here's what changed..."
* **NO EXCEPTIONS** - user must understand all actions

### RULE 3: USER APPROVAL (REQUIRED - HARD STOP)

* **ASK BEFORE DECIDING** on:
  * Project structure changes
  * Technology stack choices
  * Implementation approaches
  * Library/dependency additions
  * Architecture patterns
  * File organization
* **WAIT FOR EXPLICIT APPROVAL** before proceeding
* **NO ASSUMPTIONS** about what the user wants
* **NO EXCEPTIONS** - user has final say on all decisions

### RULE 4: INCREMENTAL PROGRESS (REQUIRED - HARD STOP)

* **ONE TASK AT A TIME** - complete one thing fully before moving forward
* After completing each task:
  1. Explain what was done
  2. Show the result
  3. **STOP and ASK** : "Should I proceed with [next step], or would you like to review/modify this first?"
* **NEVER** assume the user wants you to continue to the next step
* **NEVER** chain multiple tasks together without approval
* **NO EXCEPTIONS** - user controls the pace

### RULE 5: USER EXECUTES COMMANDS (REQUIRED)

* **NEVER** assume commands have been run
* **ALWAYS** provide terminal commands for the user to execute
* Format: "Please run: `command here`"
* Wait for user to confirm results before proceeding
* User handles ALL testing and command execution
* **NO EXCEPTIONS** - agent provides instructions, user executes

### RULE 6: NO MARKDOWN FILES (REQUIRED)

* **NEVER** create .md files for explanations, documentation, or instructions
* **ALL** communication happens directly in chat
* Explanations, updates, and instructions go in chat messages only
* **NO EXCEPTIONS** - no README updates, no doc files, no markdown artifacts for explanation purposes

### RULE 7: RESUME PROJECT CONTROL (REQUIRED)

* This is a **RESUME PROJECT** - the developer (user) is learning and building their portfolio
* User must understand every decision and implementation
* Agent is a  **guide and implementer** , not an autonomous builder
* **NO EXCEPTIONS** - user's learning and control are paramount

## Project Overview

Groovi - AI-Powered Mood-Based Music Recommender

**📖 Full Documentation:** Read [README.md](./README.md) for complete architecture, setup, and API documentation.

## Architecture (Quick Reference)

- **Backend** (`backend/`): FastAPI application with modular services
- **Frontend** (`frontend/`): React 18 + TypeScript + Vite
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
- [main.py](./backend/main.py): FastAPI routes & application entry point
- [settings.py](./backend/config/settings.py): Environment configuration
- [mood_analyzer.py](./backend/services/mood_analyzer.py): AI mood analysis logic
- [song_recommender.py](./backend/services/song_recommender.py): Spotify recommendation strategies
- [App.tsx](./frontend/src/App.tsx): Main React component

### External Services

- **Groq**: LLM for mood analysis (Llama 4 Maverick, temp=0.7)
- **Spotify**: Music data via Spotipy (Client Credentials flow)
- **Deepgram**: Speech-to-text for audio transcription
- **VADER**: Fallback sentiment analysis (offline, rule-based)

### Backend Services Layer

| Service          | File                     | Purpose                            |
| ---------------- | ------------------------ | ---------------------------------- |
| MoodAnalyzer     | `mood_analyzer.py`     | Groq AI + VADER sentiment analysis |
| SongRecommender  | `song_recommender.py`  | Multi-strategy Spotify search      |
| SpotifyClient    | `spotify_client.py`    | Spotipy wrapper & authentication   |
| AudioTranscriber | `audio_transcriber.py` | Deepgram audio-to-text             |

### API Endpoints

| Method | Endpoint        | Description                                |
| ------ | --------------- | ------------------------------------------ |
| GET    | `/`           | Health check                               |
| POST   | `/recommend`  | Analyze mood → Get 5 song recommendations |
| POST   | `/transcribe` | Convert audio file to text                 |

### Frontend Components

| Component     | File                  | Purpose                           |
| ------------- | --------------------- | --------------------------------- |
| App           | `App.tsx`           | Main UI, mood input, song display |
| AudioRecorder | `AudioRecorder.tsx` | Browser microphone recording      |
| AudioUploader | `AudioUploader.tsx` | Audio file upload handling        |

### Anti-Patterns

- ❌ Hardcode API keys → ✅ Load from `.env` via settings
- ❌ Generic exception catching → ✅ Specific exceptions with context
- ❌ No fallback for API failures → ✅ Always have fallback data/logic
- ❌ Blocking synchronous calls → ✅ Use async where beneficial
- ❌ Missing CORS configuration → ✅ Configure allowed origins in settings
