#!/usr/bin/env python3
"""
Groovi Spotify MCP Server

Provides Spotify functionality through:
1. MCP (Model Context Protocol) - For AI agent integration via stdio
2. HTTP REST API - For backend/frontend integration via FastAPI
"""

import asyncio
import logging
import threading
from typing import Any, Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
import uvicorn

from mcp.server import Server
from mcp.types import Tool, TextContent

from spotify_client import spotify_client
from mood_mappings import get_audio_features_for_mood, MOOD_AUDIO_FEATURES
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class RecommendationRequest(BaseModel):
    mood: str
    limit: int = 5

class PlaybackRequest(BaseModel):
    uris: Optional[List[str]] = None
    device_id: Optional[str] = None

class PlaylistCreateRequest(BaseModel):
    name: str
    description: str = ""
    public: bool = False
    track_uris: Optional[List[str]] = None

class PlaylistAddRequest(BaseModel):
    playlist_id: str
    track_uris: List[str]


# ==================== HTTP API Server (FastAPI) ====================

http_app = FastAPI(
    title="Groovi Spotify MCP",
    version=settings.server_version,
    description="Spotify integration for Groovi - OAuth, Playback, Playlists"
)

# CORS - Allow frontend origins
http_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Health Check ----------

@http_app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "service": settings.server_name,
        "version": settings.server_version,
        "status": "healthy",
        "user_authenticated": spotify_client.is_user_authenticated()
    }


# ---------- OAuth Endpoints ----------

@http_app.get("/auth/login")
async def auth_login():
    """Get Spotify OAuth authorization URL"""
    auth_url = spotify_client.get_auth_url()
    return {"auth_url": auth_url}

@http_app.get("/auth/login/redirect")
async def auth_login_redirect():
    """Redirect directly to Spotify OAuth"""
    auth_url = spotify_client.get_auth_url()
    return RedirectResponse(url=auth_url)

@http_app.get("/callback")
async def auth_callback(code: str = Query(...), state: Optional[str] = None):
    """
    Handle Spotify OAuth callback.
    Exchanges auth code for tokens and saves refresh token.
    """
    try:
        result = spotify_client.exchange_code(code)
        
        # Return success page that closes popup and notifies parent
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

@http_app.get("/auth/token")
async def get_token():
    """Get current access token for Web Playback SDK"""
    token = spotify_client.get_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    return {"access_token": token}

@http_app.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    return {
        "authenticated": spotify_client.is_user_authenticated(),
        "has_refresh_token": settings.spotify_refresh_token is not None
    }


# ---------- Recommendations Endpoint ----------
# NOTE: Spotify deprecated /recommendations API for new apps (Nov 2024)
# Using search-based approach instead

@http_app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """
    Get song recommendations based on mood.
    Uses search with mood-based queries (since recommendations API is deprecated).
    """
    # Get mood-based search terms
    features = get_audio_features_for_mood(request.mood)
    genres = features.get('seed_genres', ['pop'])
    
    logger.info(f"🎯 Getting songs for mood: {request.mood}")
    logger.info(f"   Searching with genres: {genres}")
    
    # Build search query based on mood
    mood_search_terms = {
        "happy": "happy upbeat feel good",
        "energetic": "energetic pump up workout",
        "calm": "calm relaxing peaceful",
        "sad": "emotional sad melancholy",
        "angry": "intense angry powerful",
        "anxious": "soothing calm ambient",
        "romantic": "love romantic ballad",
        "neutral": "popular hits top"
    }
    
    search_query = mood_search_terms.get(request.mood.lower(), "popular hits")
    
    # Search for tracks
    tracks = spotify_client.search_tracks(f"{search_query} {genres[0]}", limit=request.limit * 2)
    
    if not tracks:
        # Fallback: try just genre search
        tracks = spotify_client.search_tracks(genres[0], limit=request.limit)
    
    if not tracks:
        raise HTTPException(status_code=404, detail="No songs found for this mood")
    
    # Return unique tracks up to limit
    return {"tracks": tracks[:request.limit], "mood": request.mood, "count": len(tracks[:request.limit])}

@http_app.get("/moods")
async def list_moods():
    """List all available mood categories and their audio features"""
    return {"moods": MOOD_AUDIO_FEATURES}


# ---------- Playback Control Endpoints ----------

@http_app.post("/player/play")
async def player_play(request: PlaybackRequest):
    """Start playback with optional track URIs"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = spotify_client.start_playback(
        uris=request.uris,
        device_id=request.device_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start playback")
    
    return {"status": "playing", "tracks": len(request.uris) if request.uris else 0}

@http_app.post("/player/pause")
async def player_pause(device_id: Optional[str] = None):
    """Pause playback"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = spotify_client.pause_playback(device_id=device_id)
    return {"status": "paused" if success else "error"}

@http_app.post("/player/next")
async def player_next(device_id: Optional[str] = None):
    """Skip to next track"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = spotify_client.next_track(device_id=device_id)
    return {"status": "skipped" if success else "error"}

@http_app.post("/player/previous")
async def player_previous(device_id: Optional[str] = None):
    """Go to previous track"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = spotify_client.previous_track(device_id=device_id)
    return {"status": "previous" if success else "error"}

@http_app.get("/player/state")
async def player_state():
    """Get current playback state"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    state = spotify_client.get_playback_state()
    return {"state": state}

@http_app.get("/player/devices")
async def player_devices():
    """Get available playback devices"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    devices = spotify_client.get_available_devices()
    return {"devices": devices}


# ---------- Playlist Endpoints ----------

@http_app.post("/playlist/create")
async def playlist_create(request: PlaylistCreateRequest):
    """Create a new playlist and optionally add tracks"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Create playlist
    playlist = spotify_client.create_playlist(
        name=request.name,
        description=request.description,
        public=request.public
    )
    
    if not playlist:
        raise HTTPException(status_code=500, detail="Failed to create playlist")
    
    # Add tracks if provided
    if request.track_uris:
        spotify_client.add_tracks_to_playlist(playlist['id'], request.track_uris)
        playlist['tracks_added'] = len(request.track_uris)
    
    return {"playlist": playlist}

@http_app.post("/playlist/add")
async def playlist_add_tracks(request: PlaylistAddRequest):
    """Add tracks to an existing playlist"""
    if not spotify_client.is_user_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    success = spotify_client.add_tracks_to_playlist(
        request.playlist_id,
        request.track_uris
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to add tracks")
    
    return {"status": "added", "tracks": len(request.track_uris)}


# ---------- Search & Track Info ----------

@http_app.get("/search")
async def search_tracks(q: str = Query(...), limit: int = 10):
    """Search for tracks"""
    tracks = spotify_client.search_tracks(q, limit=limit)
    return {"tracks": tracks, "query": q, "count": len(tracks)}

@http_app.get("/track/{track_id}")
async def get_track(track_id: str):
    """Get track details"""
    track = spotify_client.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {"track": track}

@http_app.get("/genres")
async def get_genres():
    """Get available genre seeds"""
    genres = spotify_client.get_available_genre_seeds()
    return {"genres": genres, "count": len(genres)}


# ==================== MCP Server (stdio) ====================

mcp_app = Server(settings.server_name)

@mcp_app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Spotify tools"""
    return [
        Tool(
            name="search_tracks",
            description="Search for tracks on Spotify by query string",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Results count (1-50)", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_recommendations",
            description="Get song recommendations based on mood/audio features",
            inputSchema={
                "type": "object",
                "properties": {
                    "mood": {"type": "string", "description": "Mood category (happy, sad, energetic, calm, angry, anxious, romantic, neutral)"},
                    "limit": {"type": "integer", "description": "Number of recommendations", "default": 5}
                },
                "required": ["mood"]
            }
        ),
        Tool(
            name="get_track_features",
            description="Get audio features for a specific track",
            inputSchema={
                "type": "object",
                "properties": {
                    "track_id": {"type": "string", "description": "Spotify track ID"}
                },
                "required": ["track_id"]
            }
        ),
        Tool(
            name="create_playlist",
            description="Create a playlist with recommended songs",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Playlist name"},
                    "track_uris": {"type": "array", "items": {"type": "string"}, "description": "Track URIs to add"},
                    "description": {"type": "string", "description": "Playlist description", "default": ""}
                },
                "required": ["name", "track_uris"]
            }
        )
    ]

@mcp_app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle MCP tool calls"""
    try:
        if name == "search_tracks":
            tracks = spotify_client.search_tracks(arguments["query"], arguments.get("limit", 10))
            return [TextContent(type="text", text=f"Found {len(tracks)} tracks:\n" + 
                "\n".join([f"🎵 {t['name']} by {t['artist']} (ID: {t['id']})" for t in tracks]))]
        
        elif name == "get_recommendations":
            features = get_audio_features_for_mood(arguments["mood"])
            tracks = spotify_client.get_recommendations(
                seed_genres=features.get('seed_genres'),
                limit=arguments.get("limit", 5),
                **{k: v for k, v in features.items() if k != 'seed_genres'}
            )
            return [TextContent(type="text", text=f"Recommended {len(tracks)} tracks for {arguments['mood']} mood:\n" +
                "\n".join([f"🎵 {t['name']} by {t['artist']} (URI: {t['uri']})" for t in tracks]))]
        
        elif name == "get_track_features":
            features = spotify_client.get_track_audio_features(arguments["track_id"])
            if features:
                return [TextContent(type="text", text=f"Audio Features:\n"
                    f"Valence: {features['valence']:.2f}\n"
                    f"Energy: {features['energy']:.2f}\n"
                    f"Danceability: {features['danceability']:.2f}")]
            return [TextContent(type="text", text="❌ Could not get features")]
        
        elif name == "create_playlist":
            playlist = spotify_client.create_playlist(arguments["name"], arguments.get("description", ""))
            if playlist and arguments.get("track_uris"):
                spotify_client.add_tracks_to_playlist(playlist['id'], arguments["track_uris"])
            return [TextContent(type="text", text=f"✅ Created playlist: {playlist['external_url']}" if playlist else "❌ Failed")]
        
        return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"❌ Error: {str(e)}")]


# ==================== Server Startup ====================

def run_http_server():
    """Run HTTP server in a separate thread"""
    uvicorn.run(
        http_app,
        host="0.0.0.0",
        port=settings.http_port,
        log_level="info"
    )

async def run_mcp_server():
    """Run MCP server with stdio transport"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_app.run(
            read_stream,
            write_stream,
            mcp_app.create_initialization_options()
        )

async def main():
    """Run both HTTP and MCP servers"""
    logger.info(f"🎵 Starting {settings.server_name} v{settings.server_version}")
    logger.info(f"🌐 HTTP Server: http://localhost:{settings.http_port}")
    logger.info(f"🔌 MCP Server: stdio")
    
    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    logger.info("✅ Servers started. HTTP ready for requests, MCP ready for connections.")
    
    # Keep main thread alive (MCP over stdio would be started separately if needed)
    # For now, just run HTTP server
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())