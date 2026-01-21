# 🎵 Groovi - Real-Time Voice AI Music Assistant

<div align="center">

**Voice-first AI music assistant with wake word detection, real-time speech processing, and AI agent-based recommendations via Model Context Protocol (MCP)**

[Voice AI](#️-voice-ai-architecture) • [MCP Integration](#-mcp-integration) • [AI Agent](#-ai-agent-workflow) • [Installation](#-installation)

</div>

---

## 📖 Table of Contents

- [About](#-about)
- [🎙️ Voice AI Architecture](#️-voice-ai-architecture) ⭐
- [🔌 MCP Integration](#-mcp-integration)
- [🤖 AI Agent Workflow](#-ai-agent-workflow)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the App](#-running-the-app)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 About

**Groovi** is a **real-time voice AI music assistant** demonstrating advanced voice processing, Model Context Protocol (MCP) integration, and AI agent-based music discovery.

### Key Features

1. **🎤 Full Voice-to-Voice Pipeline** - Wake word → STT → LLM → TTS (real-time, mostly local)
2. **🔌 MCP-Based Architecture** - Spotify integration via Model Context Protocol
3. **🤖 AI Agent with Function Calling** - Iterative music discovery using Groq LLM
4. **⚡ WebSocket Real-Time Processing** - Streaming audio processing
5. **🎯 Custom Wake Word** - "Hey Groovi" detection

### How It Works

1. **Say "Hey Groovi"** - Custom wake word activates the assistant
2. **Speak Your Request** - VAD detects speech, Faster-Whisper transcribes
3. **AI Agent Explores** - Function-calling agent searches Spotify via MCP
4. **Groovi Responds** - Local Piper TTS speaks recommendations

---

## 🎙️ Voice AI Architecture

Real-time voice-to-voice pipeline running via WebSocket.

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
{"event": "speech_detected", "transcript": "..."}
{"event": "processing"}
{"event": "speaking", "text": "..."}
{"event": "audio", "data": <bytes>}  // TTS audio
{"event": "music_results", "tracks": [...]}
```

---

## 🔌 MCP Integration

Uses **Model Context Protocol** for Spotify integration - an open standard for AI-to-tool communication.

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

10 Spotify tools exposed via MCP:
- `search_tracks`, `search_artists`, `search_playlists`
- `get_artist_top_tracks`, `get_related_artists`
- `browse_new_releases`, `browse_genres`
- `create_playlist`, and more

**Transport**: Stdio (Standard I/O)  
**Protocol**: JSON-RPC 2.0  
**Connection**: Per-request spawning

---

## 🤖 AI Agent Workflow

Autonomous AI agent using function calling to explore Spotify and curate recommendations.

**Model**: Llama 3.1 8B (via Groq)  
**Max Iterations**: 5  
**Strategy**: ReAct (Reasoning + Acting)

### Agent Loop

```python
while iteration < 5:
    # 1. LLM decides which tool to call
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=conversation_history,
        tools=SPOTIFY_TOOLS
    )
    
    # 2. Execute tool via MCP
    result = await mcp_client.call_tool(tool_name, args)
    
    # 3. Agent refines or finishes
    if agent_done:
        break
```

**Example**: User says "energetic workout music"
- Iteration 1: Search tracks → 15 results
- Iteration 2: Explore playlists → Extract top tracks
- Iteration 3: Browse genres → Diversify
- Result: 5 curated tracks with reasoning

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
- **Groq** - LLM inference (Llama 3.1 8B)
- **MCP SDK** - Model Context Protocol
- **Spotipy** - Spotify API wrapper
- **Python 3.13**

### Frontend
- **React 18 + TypeScript**
- **Vite** - Build tool
- **Tailwind CSS v4**
- **WebSocket API**

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

# Verify
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

# Optional
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

**Expected output**:
```
🎵 Starting Groovi Backend Server...
📡 Server: http://localhost:5000
🎤 Voice AI models ready
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
│   │   ├── voice_assistant.py  # State machine orchestrator
│   │   ├── wake_word_service.py
│   │   ├── vad_service.py
│   │   ├── streaming_STT.py
│   │   └── streaming_TTS.py
│   ├── services/
│   │   ├── mcp_client.py      # MCP client
│   │   ├── music_agent.py     # AI agent
│   │   ├── mood_analyzer.py
│   │   └── spotify_auth.py
│   ├── models/
│   │   ├── Hey_Groovi.tflite  # Wake word model
│   │   └── piper/             # TTS models
│   ├── main.py                # FastAPI app
│   └── pyproject.toml
│
├── spotify_mcp/               # 🔌 MCP Server
│   ├── server.py              # MCP server
│   ├── spotify_api.py
│   └── pyproject.toml
│
├── frontend/                  # 🎨 Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
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

**Spotify credentials error**:
- Verify `.env` exists in `backend/`
- No extra spaces in API keys
- Restart backend after changes

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

**Test backend**:
```bash
cd backend
uv run python tests/test_spotify.py
uv run python tests/test_local_audio.py
```

---

## 🎓 Resources

- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized Whisper
- [Piper TTS](https://github.com/rhasspy/piper) - Local text-to-speech
- [MCP Specification](https://spec.modelcontextprotocol.io/) - Model Context Protocol
- [Groq Docs](https://console.groq.com/docs) - LLM inference

---

<div align="center">

**Built with ❤️ using Voice AI + MCP**

**Groovi 🎵✨**

</div>
