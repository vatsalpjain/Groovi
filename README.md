# 🎵 Groovi - Real-Time Voice AI Music Assistant

<div align="center">

**Voice-first AI music assistant with wake word detection, real-time speech processing, and AI agent-based recommendations via Model Context Protocol (MCP)**

[Architecture](#-system-architecture) • [Voice AI](#️-voice-ai-pipeline) • [AI Agent](#-ai-agent-workflow--fallbacks) • [Installation](#-installation)

</div>

---

## 📖 Table of Contents

- [About](#-about)
- [🏗️ System Architecture](#-system-architecture)
- [🎙️ Voice AI Pipeline](#️-voice-ai-pipeline)
- [🖱️ Click & Text Mode](#️-click--text-mode)
- [🔌 MCP Integration & Spotify Playback](#-mcp-integration--spotify-playback)
- [🤖 AI Agent Workflow & Fallbacks](#-ai-agent-workflow--fallbacks)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the App](#-running-the-app)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 About

**Groovi** is a **real-time voice AI music assistant** demonstrating advanced voice processing, Model Context Protocol (MCP) integration, and AI agent-based music discovery. Alongside its voice capabilities, it features a robust text-based interface and full in-app Spotify playback.

### Key Features

1. **🎤 Full Voice-to-Voice Pipeline & Fallback Text Mode** - Wake word → STT → LLM → TTS (real-time, mostly local) alongside a standard text-based interaction mode.
2. **🔌 MCP-Based Architecture** - Secure Spotify integration isolated via Model Context Protocol.
3. **🤖 AI Agent with Function Calling & VADER Fallback** - Iterative music discovery using Groq LLM, with local VADER sentiment analysis fallback if the LLM is unavailable.
4. **⚡ WebSocket & REST Processing** - Dual communication layers for streaming audio (WebSocket) and standard queries (REST).
5. **🎵 In-App Spotify Playback** - Direct playback using the Spotify Web Playback SDK with a fallback iframe embed player.
6. **🎯 Custom Wake Word** - "Hey Groovi" detection triggering real-time listening.

---

## 🏗️ System Architecture

Groovi is structured with an asynchronous backend (FastAPI) and a reactive frontend (React + Vite), bridged by dual communication channels for different modes of interaction.

### Frontend (React/Vite)
- **UI Components**: Glassmorphic styling, real-time "AI Orb" visualizer, and live "Thought Process" displays showing the agent's iterative reasoning.
- **State Management**: React hooks orchestrating WebSockets (`useVoiceWebSocket`), audio capture (`useAudioCapture`), and REST API flows.
- **Playback Layer**: Tries to instantiate the Spotify Web Playback SDK for seamless in-app listening (requires Premium). Falls back to the standard Spotify Embed iframe on failure.

### Backend (FastAPI)
- **Voice AI Subsystem**: Manages the local ML execution environment for Wake Word, VAD, STT, and TTS.
- **Agent Subsystem**: Connects to the Groq LLM API and orchestrates function calling.
- **MCP Client**: Standard Input/Output (stdio) bridge communicating with an isolated Python MCP server (`spotify_mcp/`) that executes the actual Spotify API calls securely.

### Communication Flow
- **WebSocket (`/ws/voice`)**: Dedicated full-duplex channel for streaming raw PCM audio chunks (16kHz, 16-bit mono), wake word notifications, and TTS audio distribution back to the client.
- **REST Endpoints (`/recommend`, `/transcribe`, `/synthesize`, `/playlist/create`)**: Standard stateless endpoints powering the "Click Mode", handling text uploads, authentication callbacks, and playlist generation.

---

## 🎙️ Voice AI Pipeline

Real-time voice-to-voice pipeline running entirely via WebSocket.

### State Machine

```
WAKE_WORD (Idle) → LISTENING (VAD + STT) → PROCESSING (LLM + Agent) → SPEAKING (TTS) → Loop
```

### Components

| Component | Technology | Purpose | Latency |
|-----------|-----------|---------|---------|
| **Wake Word** | openWakeWord + Custom Model | "Hey Groovi" detection | < 100ms |
| **VAD** | Silero VAD | Speech/silence detection | 30ms |
| **STT** | Faster-Whisper (base) | Speech-to-text | ~500ms |
| **LLM** | Groq (Llama 3.1 8B) | Conversation + reasoning | ~300ms |
| **TTS** | Piper TTS (ONNX) | Text-to-speech | ~200ms |

**Total Latency**: ~1.1s | **Memory**: ~300MB

### WebSocket Protocol (`/ws/voice`)

**Client → Server**: Binary PCM audio chunks (16kHz, 16-bit mono)

**Server → Client Events**:
```json
{"event": "ready"}
{"event": "wake_word_detected"}
{"event": "listening"}
{"event": "transcript", "text": "..."}
{"event": "response_text", "text": "..."} // For Chat Bubbles UI
{"event": "processing"}
{"event": "audio", "data": <bytes>}  // TTS audio
{"event": "songs", "mood_analysis": {...}, "songs": [...]}
```

---

## 🖱️ Click & Text Mode

Groovi guarantees accessibility and functionality without a microphone via its **Click Mode**.

- **Workflow**: Users type their mood/request into the UI textarea.
- **Execution**: The frontend utilizes the REST `/recommend` endpoint, bypassing STT/TTS overhead and directly triggering the backend Music AI Agent.
- **Visuals**: Displays the exact Thought Process the agent underwent to curate the playlist, followed by the Spotify Player and Mood Analysis breakdown.

---

## 🔌 MCP Integration & Spotify Playback

Uses **Model Context Protocol** for Spotify integration - an open standard for AI-to-tool communication, ensuring the LLM agent code is strictly separated from API credential management.

### Architecture

```
Backend AI Agent (Groq LLM)
    ↓ Function Calls
MCP Client (stdio)
    ↓ JSON-RPC
MCP Server (spotify_mcp/)
    ↓ Tool Execution
Spotify Web API
```

### MCP Server Tools

Spotify tools exposed via MCP to the agent:
- `search_tracks`, `search_artists`, `search_playlists`
- `get_playlist_tracks`
- *Note: Agent search logic relies strictly on available endpoints after recent Spotify API deprecations.*
- `create_playlist` (Triggered manually via the UI "Save to Spotify" button).

**Transport**: Stdio (Standard I/O)  
**Protocol**: JSON-RPC 2.0  
**Connection**: Per-request process spawning via UV

### In-App Playback
Groovi provides native playback inside the web app based on the authentication state:
1. **Web Playback SDK**: Requires user login and Spotify Premium. Streams full tracks directly inside the browser.
2. **Embed Fallback**: If the SDK fails, the `SpotifyPlayer` component automatically falls back to embedding standard 30-second Spotify preview iframes (`SpotifyEmbed`).

---

## 🤖 AI Agent Workflow & Fallbacks

Autonomous AI agent using ReAct function calling to explore Spotify and curate recommendations.

**Primary Model**: Llama 3.3 70B & 3.1 8B (via Groq)  
**Max Iterations**: 5  
**Strategy**: Reasoning + Acting (ReAct)

### Agent Loop (`music_agent.py`)

```python
while iteration < 5:
    # 1. LLM decides which tool to call
    response = groq_client.chat.completions.create(...)
    
    # 2. Execute tool via MCP stdio client
    result = await mcp_client.call_tool(tool_name, args)
    
    # 3. Truncate result metadata to save tokens (70-80% savings)
    truncated = truncate_mcp_result(result)
    
    # 4. Agent refines or finishes (returns JSON with final tracks)
```

**Example**: User says "energetic workout music"
- Iteration 1: `search_tracks` → 15 results
- Iteration 2: `search_playlists` → Extract top tracks
- Result: 10 curated tracks returned directly to the frontend.

### The VADER Fallback Mechanism
If the Groq API completely fails (e.g., rate limits or network issues), the backend automatically traps the exception and triggers **local VADER sentiment analysis** (`services/vader_fallback.py`).
- Parses the user prompt for sentiment compound scores (positive/negative/neutral).
- Returns 10 hardcoded, highly curated fallback tracks matching the calculated sentiment to ensure the application continues functioning regardless of LLM availability.

---

## 🛠️ Tech Stack

### Voice AI
- **Faster-Whisper** - Local STT (CTranslate2 optimized)
- **Piper TTS** - Local TTS (ONNX Runtime)
- **openWakeWord** - Custom wake word detection
- **Silero VAD** - Voice activity detection
- **PyTorch + ONNX** - ML inference engines

### Backend
- **FastAPI** - Async web framework
- **Groq** - LLM inference (Llama 3.3 70B & 3.1 8B)
- **MCP SDK** - Model Context Protocol
- **Spotipy** - Spotify API wrapper
- **VADER Sentiment** - Standalone NLP text fallback
- **Python 3.13**

### Frontend
- **React 18 + TypeScript**
- **Vite** - Build tool
- **Tailwind CSS v4**
- **Spotify Web Playback SDK**
- **WebSocket + REST** - Dual layer communication

---

## 📋 Prerequisites

**Required Software**:
- Python 3.13+
- uv (Python package manager)
- Node.js 18+
- npm 9+

**API Keys**:
1. [Spotify Developer](https://developer.spotify.com/dashboard) - Client ID & Secret
2. [Groq Console](https://console.groq.com/) - API Key (free tier available)

---

## 🚀 Installation

### Backend Setup

```bash
cd backend

# Install uv (if not installed)
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Verify ML dependencies
uv run python -c "import faster_whisper, piper; print('✅ Ready')"
```

### MCP Server Setup

```bash
cd spotify_mcp
uv sync
```

### Frontend Setup

```bash
cd frontend
npm install
```

---

## ⚙️ Configuration

Create `backend/.env`:

```env
# Spotify (REQUIRED)
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback

# Groq (REQUIRED)
GROQ_API_KEY=your_groq_api_key

# Optional ML settings
# WHISPER_MODEL_SIZE=base
# WAKE_WORD_THRESHOLD=0.5
```

**Get Spotify Keys**:
1. Go to [Spotify Dashboard](https://developer.spotify.com/dashboard)
2. Create app, add redirect URI: `http://localhost:5000/callback`
3. Copy Client ID & Secret

**Get Groq Key**:
1. Go to [Groq Console](https://console.groq.com/)
2. Create API key
3. Copy key (free tier: 30 requests/min)

---

## 🏃 Running the App

**Terminal 1 - Backend**:
```bash
cd backend
uv run python main.py
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

**Access**:
- 🎯 App: http://localhost:5173
- 🔧 API Docs: http://localhost:5000/docs

**First Run**: Models download (~300MB, 1-2 min). Cached afterwards.

---

## 📁 Project Structure

```
groovi/
├── backend/
│   ├── voice_ai/              # 🎙️ Voice AI Pipeline
│   │   ├── voice_assistant.py  # WebSocket state machine orchestrator
│   │   ├── wake_word_service.py
│   │   ├── vad_service.py
│   │   ├── streaming_STT.py
│   │   └── streaming_TTS.py
│   ├── services/
│   │   ├── mcp_client.py      # MCP stdio client connecting to isolated server
│   │   ├── music_agent.py     # AI ReAct agent with token truncation
│   │   ├── vader_fallback.py  # VADER sentiment fallback mechanism
│   │   └── spotify_auth.py
│   ├── models/                # Local ONNX/TFLite model cache
│   ├── main.py                # FastAPI app (REST + WebSocket router)
│   └── pyproject.toml
│
├── spotify_mcp/               # 🔌 MCP Server Project
│   ├── server.py              # MCP server exposing Spotify API
│   ├── spotify_api.py
│   └── pyproject.toml
│
├── frontend/                  # 🎨 Frontend (React/Vite)
│   ├── src/
│   │   ├── components/        # SpotifyPlayer, AIOrb, ThoughtProcess, etc.
│   │   ├── hooks/             # WebSocket, audio processors, playback SDK
│   │   └── services/          # REST API callers
│   └── package.json
│
└── README.md
```

---

## 🐛 Troubleshooting

**WebSocket connection failed**:
- Ensure backend running: `cd backend && uv run python main.py`
- Check port 5000 available

**Wake word not detecting**:
- Check model exists: `backend/models/Hey_Groov*.onnx`
- Speak clearly in quiet environment
- Lower threshold in `.env`: `WAKE_WORD_THRESHOLD=0.3`

**Spotify SDK / Playback not working**:
- Ensure you have a Spotify Premium account (required by the Web Playback SDK).
- If playback fails, ensure the app falls back to the embedded iframe player visually.
- Verify `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` in `.env`.

**Module not found**:
```bash
cd backend
uv sync
```

**MCP server spawn failed**:
```bash
cd spotify_mcp
uv sync
```

---

## 🎓 Resources

- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper
- [Piper TTS](https://github.com/rhasspy/piper) - Local text-to-speech
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Model Context Protocol
- [Groq Docs](https://console.groq.com/docs) - LLM inference
- [Spotify Web Playback SDK](https://developer.spotify.com/documentation/web-playback-sdk)

---

<div align="center">

**Built with ❤️ using Voice AI + MCP**

**Groovi 🎵✨**

</div>
