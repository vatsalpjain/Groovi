#!/usr/bin/env python3
"""
Groovi Spotify MCP Server

Pure MCP server providing Spotify tools via stdio transport.
Used by the backend's MCP client to access Spotify functionality.

NOTE: Removed tools for endpoints Spotify killed in Feb/Mar 2026:
- get_artist_top_tracks, get_related_artists, get_genres, get_new_releases, get_track_features
"""

import asyncio
import logging
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from spotify_api import spotify_api
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MCP Server ====================

mcp_app = Server(settings.server_name)


@mcp_app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Spotify tools"""
    return [
        # Search tools (still supported by Spotify)
        Tool(
            name="search_tracks",
            description="Search for tracks on Spotify by query string",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (song name, artist, mood, etc.)"},
                    "limit": {"type": "integer", "description": "Number of results (1-10, max 10)", "default": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_artist",
            description="Find an artist by name. Returns artist ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Artist name to search for"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="search_playlists",
            description="Search for curated playlists by theme, mood, or activity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Playlist search query"},
                    "limit": {"type": "integer", "description": "Number of results (1-10, max 10)", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_playlist_tracks",
            description="Get tracks from a specific playlist.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Spotify playlist ID"},
                    "limit": {"type": "integer", "description": "Number of tracks", "default": 20}
                },
                "required": ["playlist_id"]
            }
        ),
        Tool(
            name="search_by_genre",
            description="Search tracks by genre. Use when user asks for a specific genre.",
            inputSchema={
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre name (e.g., rock, jazz, hip-hop)"},
                    "limit": {"type": "integer", "description": "Number of results (1-10, max 10)", "default": 10}
                },
                "required": ["genre"]
            }
        ),
        # Playlist tools (require user auth)
        Tool(
            name="create_playlist",
            description="Create a playlist in user's Spotify account with given tracks.",
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
        logger.info(f"🔧 Tool called: {name} with args: {arguments}")
        
        if name == "search_tracks":
            tracks = spotify_api.search_tracks(arguments["query"], arguments.get("limit", 10))
            return [TextContent(type="text", text=json.dumps({"tracks": tracks, "count": len(tracks)}))]
        
        elif name == "search_artist":
            artist = spotify_api.search_artist(arguments["name"])
            if artist:
                return [TextContent(type="text", text=json.dumps({"artist": artist}))]
            return [TextContent(type="text", text=json.dumps({"error": f"Artist '{arguments['name']}' not found"}))]
        
        elif name == "search_playlists":
            playlists = spotify_api.search_playlists(arguments["query"], arguments.get("limit", 5))
            return [TextContent(type="text", text=json.dumps({"playlists": playlists, "count": len(playlists)}))]
        
        elif name == "get_playlist_tracks":
            tracks = spotify_api.get_playlist_tracks(arguments["playlist_id"], arguments.get("limit", 20))
            return [TextContent(type="text", text=json.dumps({"tracks": tracks, "count": len(tracks)}))]
        
        elif name == "search_by_genre":
            tracks = spotify_api.search_by_genre(arguments["genre"], arguments.get("limit", 10))
            return [TextContent(type="text", text=json.dumps({"tracks": tracks, "count": len(tracks)}))]
        
        elif name == "create_playlist":
            playlist = spotify_api.create_playlist(arguments["name"], arguments.get("description", ""))
            if playlist and arguments.get("track_uris"):
                spotify_api.add_tracks_to_playlist(playlist['id'], arguments["track_uris"])
                playlist['tracks_added'] = len(arguments["track_uris"])
            return [TextContent(type="text", text=json.dumps({"playlist": playlist} if playlist else {"error": "Failed to create playlist"}))]
        
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ==================== Server Startup ====================

async def main():
    """Run MCP server with stdio transport"""
    logger.info(f"🎵 Starting {settings.server_name} v{settings.server_version}")
    logger.info("🔌 MCP Server: stdio transport")
    logger.info("✅ Waiting for MCP client connection...")
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_app.run(
            read_stream,
            write_stream,
            mcp_app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())