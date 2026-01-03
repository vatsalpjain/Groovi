
# 🎵 Groovi - AI-Powered Mood-Based Music Recommender
<div align="center">
**Describe your mood with text or voice, and discover the perfect soundtrack powered by AI**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) 

</div>

---

## 📖 Table of Contents

- [About](#-about-the-project)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 About The Project

**Groovi** is an intelligent music recommendation system that analyzes your mood through text or voice input and curates a personalized playlist of 5 songs that perfectly match your emotional state. 

### How It Works

1. **Input Your Mood** - Type, speak, or upload audio describing how you feel
2. **AI Analysis** - Advanced AI (Groq LLM) analyzes sentiment and generates insights
3. **Smart Recommendations** - Get 5 perfectly matched songs from Spotify
4. **Enjoy** - Listen directly on Spotify with one click

---

## ✨ Features

### 🧠 **Intelligent Mood Analysis**
- **AI-Powered Sentiment Analysis** using Groq LLM (Llama 4 Maverick)
- **Fallback VADER Analysis** for reliable offline processing
- **100-word AI-generated mood summaries** that celebrate and uplift your emotions

### 🎤 **Multi-Modal Input**
- ✍️ **Text Input** - Type your mood in natural language
- 🎙️ **Voice Recording** - Record your mood directly in the browser
- 📁 **Audio Upload** - Upload audio files (MP3, WAV, WebM, OGG, M4A)
- 🗣️ **Speech-to-Text** - Local Faster-Whisper for accurate transcription (no API key needed)

### 🎵 **Smart Music Recommendations**
- **5 Curated Songs** per mood analysis
- **Spotify Integration** - Direct links to play on Spotify
- **Album Artwork** - Beautiful visual presentation
- **Fallback System** - Always returns recommendations even if APIs fail

### 🎨 **Modern UI/UX**
- **Dark Mode Design** with glassmorphism effects
- **Responsive Layout** - Works on desktop, tablet, and mobile
- **Smooth Animations** - Engaging user experience
- **Real-time Feedback** - Loading states and error handling

---

## 🛠️ Tech Stack

### **Backend**
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Spotipy](https://spotipy.readthedocs.io/)** - Spotify API wrapper
- **[Groq](https://groq.com/)** - AI/LLM for mood analysis
- **[Faster-Whisper](https://github.com/guillaumekln/faster-whisper)** - Local speech-to-text
- **[Piper TTS](https://github.com/rhasspy/piper)** - Local text-to-speech
- **[VADER Sentiment](https://github.com/cjhutto/vaderSentiment)** - Fallback sentiment analyzer
- **[Pydantic](https://pydantic.dev/)** - Data validation
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server

### **Frontend**
- **[React 18](https://react.dev/)** - UI library
- **[TypeScript](https://www.typescriptlang.org/)** - Type-safe JavaScript
- **[Vite](https://vitejs.dev/)** - Build tool and dev server
- **[CSS3](https://developer.mozilla.org/en-US/docs/Web/CSS)** - Modern styling with animations

### **APIs & Services**
- **[Spotify Web API](https://developer.spotify.com/documentation/web-api)** - Music data and playback
- **[Groq API](https://console.groq.com/)** - AI-powered mood analysis

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Text Input  │  │ Voice Recorder│  │  Audio Uploader │   │
│  └─────────────┘  └──────────────┘  └─────────────────┘   │
│                           │                                  │
│                           ▼                                  │
│                  ┌─────────────────┐                        │
│                  │   App.tsx       │                        │
│                  └─────────────────┘                        │
└────────────────────────│───────────────────────────────────┘
                         │
                         │ HTTP Requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                     main.py (Routes)                  │  │
│  │  ┌─────────────────┐      ┌──────────────────────┐  │  │
│  │  │ /transcribe     │      │    /recommend        │  │  │
│  │  └─────────────────┘      └──────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Services Layer                         │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │  │
│  │  │ AudioTranscriber│  │    MoodAnalyzer          │  │  │
│  │  │ (Faster-Whisper)│  │  (Groq AI + VADER)       │  │  │
│  │  └─────────────────┘  └──────────────────────────┘  │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │  │
│  │  │SongRecommender  │  │   SpotifyClient          │  │  │
│  │  │  (Multi-strategy)│  │   (Spotipy)              │  │  │
│  │  └─────────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data & Config Layer                      │  │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │  │
│  │  │ mood_libraries  │  │      settings            │  │  │
│  │  │  (Fallback data)│  │   (Environment vars)     │  │  │
│  │  └─────────────────┘  └──────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                             │
│  ┌──────────────┐  ┌────────────┐                           │
│  │ Spotify API  │  │  Groq API  │                           │
│  └──────────────┘  └────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### **Required Software**

| Software | Version | Download Link |
|----------|---------|---------------|
| **Python** | 3.8 or higher | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 16.0 or higher | [nodejs.org](https://nodejs.org/) |
| **npm** | 8.0 or higher | Comes with Node.js |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |

### **API Keys Required**

You'll need to sign up for free API keys from:

1. **[Spotify for Developers](https://developer.spotify.com/dashboard)**
   - Create an app to get `Client ID` and `Client Secret`
   - Free tier: Unlimited requests

2. **[Groq Console](https://console.groq.com/)**
   - Sign up for free API key
   - Free tier: Generous rate limits

---

## 🚀 Installation

### **Step 1: Clone the Repository**

```bash
# Clone the repo
git clone https://github.com/yourusername/groovi.git

# Navigate to project directory
cd groovi
```

### **Step 2: Backend Setup**

#### **2.1 Navigate to backend folder**
```bash
cd backend_new
```

#### **2.2 Create virtual environment**

**Windows (Command Prompt):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

#### **2.3 Install Python dependencies**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Expected packages installed:**
- fastapi
- uvicorn[standard]
- spotipy
- groq
- faster-whisper
- piper-tts
- vaderSentiment
- pydantic
- python-dotenv
- requests

#### **2.4 Verify installation**
```bash
pip list
```

### **Step 3: Frontend Setup**

#### **3.1 Open new terminal and navigate to frontend**
```bash
cd ../frontend_new
```

#### **3.2 Install Node.js dependencies**
```bash
npm install
```

**Expected output:**
```
✓ Dependencies installed successfully
```

---

## ⚙️ Configuration

### **Backend Configuration**

#### **Create `.env` file in `backend_new/` folder:**

```bash
# Navigate to backend_new folder
cd backend_new

# Create .env file
# Windows: use notepad
notepad .env

# macOS/Linux: use nano or vim
nano .env
```

#### **Add your API keys to `.env`:**

```env
# Spotify API Credentials (REQUIRED)
# Get from: https://developer.spotify.com/dashboard
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret_here

# Groq API Key (REQUIRED for AI mood analysis)
# Get from: https://console.groq.com/keys
GROQ_API_KEY=your_groq_api_key_here

# Optional: Local audio model settings
# WHISPER_MODEL_SIZE=base  # Options: tiny, base, small, medium
# PIPER_VOICE=en_US-lessac-medium
```

#### **How to get API keys:**

<details>
<summary><b>🎵 Spotify API Setup (Click to expand)</b></summary>

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create app"**
4. Fill in:
   - **App name:** `Groovi`
   - **App description:** `Mood-based music recommender`
   - **Redirect URI:** `http://localhost:8000/callback`
5. Check the box for **"Web API"**
6. Click **"Save"**
7. Click **"Settings"**
8. Copy your **Client ID** and **Client Secret**
9. Paste them into your `.env` file

</details>

<details>
<summary><b>🤖 Groq API Setup (Click to expand)</b></summary>

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **"Create API Key"**
5. Give it a name: `Groovi`
6. Copy the API key (you won't see it again!)
7. Paste it into your `.env` file

</details>

</details>

### **Frontend Configuration**

No configuration needed! The frontend is pre-configured to connect to `http://127.0.0.1:8000`.

If you need to change the backend URL, edit:
- `frontend_new/src/App.tsx` (line with `fetch('http://127.0.0.1:8000/recommend'`)
- `frontend_new/src/components/AudioRecorder.tsx` (line with `fetch('http://127.0.0.1:8000/transcribe'`)
- `frontend_new/src/components/AudioUploader.tsx` (line with `fetch('http://127.0.0.1:8000/transcribe'`)

---

## 🏃 Running the Application

### **Option 1: Manual Start (Recommended for Development)**

#### **Terminal 1 - Start Backend:**
```bash
cd backend_new

# Activate virtual environment
# Windows Command Prompt:
venv\Scripts\activate
# Windows PowerShell:
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Start server
python main.py
```

**Expected output:**
```
🎵 Starting Groovi Backend Server...
📡 Server: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
✅ Spotify client initialized
✅ Groq AI initialized
✅ Local Whisper transcriber initialized
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

#### **Terminal 2 - Start Frontend:**
```bash
cd frontend_new

# Start dev server
npm run dev
```

**Expected output:**
```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

### **Option 2: Quick Start Scripts**

#### **Windows - Create `start.bat` in project root:**
```batch
@echo off
echo Starting Groovi Backend and Frontend...
start cmd /k "cd backend_new && venv\Scripts\activate && python start_server.py"
timeout /t 3
start cmd /k "cd frontend_new && npm run dev"
```

**Run:** Double-click `start.bat` or run `start.bat` in terminal

#### **macOS/Linux - Create `start.sh` in project root:**
```bash
#!/bin/bash
echo "Starting Groovi Backend and Frontend..."
cd backend_new && source venv/bin/activate && python start_server.py &
sleep 3
cd ../frontend_new && npm run dev
```

**Run:** 
```bash
chmod +x start.sh
./start.sh
```

---

## 🌐 Access the Application

1. **Frontend UI**: Open browser to [http://localhost:5173](http://localhost:5173)
2. **Backend API**: [http://localhost:8000](http://localhost:8000)
3. **API Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
4. **Alternative API Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📚 API Documentation

### **Base URL**
```
http://localhost:8000
```

### **Endpoints**

#### **1. Health Check**
```http
GET /
```

**Response:**
```json
{
  "message": "Groovi API is running!",
  "version": "1.0.0",
  "status": "healthy"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/
```

---

#### **2. Transcribe Audio**
```http
POST /transcribe
```

**Description:** Transcribe audio file to text using Deepgram AI

**Request:**
- **Content-Type:** `multipart/form-data`
- **Body:** Audio file (MP3, WAV, WebM, OGG, M4A)
- **Max size:** 10MB

**Response:**
```json
{
  "transcript": "I'm feeling really happy and energetic today!",
  "filename": "recording.webm",
  "duration_estimate": 5.2
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "audio=@recording.mp3"
```

**Python Example:**
```python
import requests

with open("recording.mp3", "rb") as audio_file:
    files = {"audio": audio_file}
    response = requests.post("http://localhost:8000/transcribe", files=files)
    print(response.json())
```

---

#### **3. Get Song Recommendations**
```http
POST /recommend
```

**Description:** Analyze mood from text and get 5 song recommendations

**Request:**
```json
{
  "text": "I'm feeling really happy and energetic today!"
}
```

**Response:**
```json
{
  "mood_analysis": {
    "category": "Very Positive",
    "description": "You're feeling fantastic and energetic!",
    "summary": "What an incredible energy you're radiating! Your positivity is infectious and it's the perfect time to celebrate with music that matches your soaring spirits. Whether you're dancing or conquering the world, these songs will amplify your amazing mood and keep those good vibes flowing!",
    "score": 0.85,
    "intensity": "moderate"
  },
  "songs": [
    {
      "name": "Happy",
      "artist": "Pharrell Williams",
      "uri": "spotify:track:60nZcImufyMA1MKQY3dcCH",
      "album_art": "https://i.scdn.co/image/ab67616d0000b273...",
      "external_url": "https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH"
    },
    // ... 4 more songs
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{"text":"I am feeling great today!"}'
```

**Python Example:**
```python
import requests

data = {"text": "I'm feeling great today!"}
response = requests.post("http://localhost:8000/recommend", json=data)
print(response.json())
```

**JavaScript Example:**
```javascript
fetch('http://localhost:8000/recommend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: "I'm feeling great today!" })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 📁 Project Structure

```
groovi/
├── backend_new/                    # Backend application (Modular FastAPI)
│   ├── config/
│   │   └── settings.py            # Environment variables & config
│   ├── models/
│   │   └── schemas.py             # Pydantic data models
│   ├── services/
│   │   ├── audio_transcriber.py   # Local Faster-Whisper STT
│   │   ├── local_audio_service.py # STT + TTS service
│   │   ├── mood_analyzer.py       # Groq AI + VADER sentiment
│   │   ├── song_recommender.py    # Multi-strategy recommendations
│   │   └── spotify_client.py      # Spotify API wrapper
│   ├── data/
│   │   └── mood_libraries.py      # Curated fallback songs by mood
│   ├── tests/
│   │   ├── test_spotify.py        # Spotify connection test
│   │   └── test_local_audio.py    # STT/TTS tests
│   ├── main.py                    # FastAPI app & server entry
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # API keys (create this)
│   └── .gitignore                 # Git ignore rules
│
├── frontend_new/                   # Frontend application (React + TypeScript + Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioRecorder.tsx  # Voice recording component
│   │   │   └── AudioUploader.tsx  # File upload component
│   │   ├── App.tsx                # Main React component
│   │   ├── App.css                # Component styles
│   │   ├── main.tsx               # React entry point
│   │   └── index.css              # Global styles
│   ├── public/                    # Static assets
│   ├── index.html                 # HTML template
│   ├── package.json               # Node.js dependencies
│   ├── tsconfig.json              # TypeScript config
│   ├── vite.config.ts             # Vite build config
│   └── .gitignore                 # Git ignore rules
│
└── README.md                       # This file
```

---

## 🐛 Troubleshooting

### **Common Issues**

<details>
<summary><b>❌ "Failed to fetch" Error</b></summary>

**Cause:** Backend server is not running.

**Solution:**
1. Ensure backend is running: `python main.py`
2. Check backend is accessible: Open [http://localhost:8000](http://localhost:8000)
3. Verify no firewall blocking port 8000
4. Check backend terminal for errors

</details>

<details>
<summary><b>❌ "Spotify credentials missing" Error</b></summary>

**Cause:** `.env` file missing or incorrect.

**Solution:**
1. Verify `.env` file exists in `backend_new/` folder
2. Check API keys are correct (no extra spaces)
3. Restart backend server after updating `.env`
4. Test connection: `python test_spotify.py`

</details>

<details>
<summary><b>❌ "Deepgram API key not configured" Error</b></summary>

**Cause:** Deepgram API key missing (optional feature).

**Solution:**
1. Add `DEEPGRAM_API_KEY` to `.env` file
2. Or disable audio features and use text input only
3. Text input will work fine without Deepgram

</details>

<details>
<summary><b>❌ "Module not found" Error</b></summary>

**Cause:** Python dependencies not installed or wrong virtual environment.

**Solution:**
```bash
cd backend_new
# Activate venv first!
pip install -r requirements.txt
```

</details>

<details>
<summary><b>❌ "Port 8000 already in use" Error</b></summary>

**Cause:** Another application using port 8000.

**Solution:**

**Option 1 - Kill existing process:**
```bash
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

**Option 2 - Change port:**
Edit `backend_new/start_server.py`:
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=8001,  # Changed from 8000
    reload=True
)
```

Then update frontend URLs to use port 8001.

</details>

<details>
<summary><b>❌ Microphone Access Denied</b></summary>

**Cause:** Browser blocking microphone access.

**Solution:**
1. Click the lock icon in browser address bar
2. Allow microphone permissions for the site
3. Refresh the page
4. Try recording again

**Chrome:** Settings → Privacy and security → Site Settings → Microphone
**Firefox:** Preferences → Privacy & Security → Permissions → Microphone

</details>

<details>
<summary><b>❌ CORS Error</b></summary>

**Cause:** Frontend URL not in allowed origins.

**Solution:**
Edit `backend_new/config/settings.py`:
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://your-custom-url:port"  # Add your URL here
]
```

Restart backend after changes.

</details>

<details>
<summary><b>❌ "No songs found" Error</b></summary>

**Cause:** All recommendation strategies failed.

**Solution:**
1. Check internet connection
2. Verify Spotify API credentials
3. Check backend logs for specific errors
4. Try simpler mood text (e.g., "happy" instead of complex sentences)

</details>

### **Testing Backend**

```bash
# Test Spotify connection
cd backend_new
python test_spotify.py

# Expected output:
# 🎵 Testing Spotify API...
# ✅ Spotify client initialized
# ✅ Connected! Test: Happy by Pharrell Williams

# Test API health
curl http://localhost:8000/

# Test text recommendation
curl -X POST "http://localhost:8000/recommend" \
  -H "Content-Type: application/json" \
  -d '{"text":"I am happy"}'

# Test audio transcription (if you have an audio file)
curl -X POST "http://localhost:8000/transcribe" \
  -F "audio=@test.mp3"
```


## 🎓 Learn More

<div align="center">

## 💖 **Made with ❤️ by the Groovi Team**

**Happy vibing with Groovi! 🎵✨**

---
</div>
