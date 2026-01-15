"""
MCP Client for Spotify Tools

Connects to the Spotify MCP server via stdio transport.
Spawns the MCP server as a subprocess and communicates via JSON-RPC.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

# Path to the MCP server
MCP_SERVER_PATH = Path(__file__).parent.parent.parent / "spotify_mcp" / "server.py"


class SpotifyMCPClient:
    """
    MCP Client for Spotify tools.
    
    Uses a per-request connection model - each call_tool spawns a fresh
    connection to avoid async context manager issues.
    """
    
    def __init__(self):
        self._connected = False
    
    async def connect(self) -> "SpotifyMCPClient":
        """Mark client as ready (actual connection happens per-request)"""
        self._connected = True
        logger.info("✅ MCP client ready")
        return self
    
    async def disconnect(self):
        """Mark client as disconnected"""
        self._connected = False
        logger.info("🔌 MCP client disconnected")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from the MCP server"""
        server_params = StdioServerParameters(
            command="uv",
            args=["--directory", str(MCP_SERVER_PATH.parent), "run", "server.py"],
            env=None
        )
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in result.tools
                ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Creates a fresh connection for each call to avoid async context issues.
        
        Args:
            name: Tool name (e.g., "search_tracks", "search_artist")
            arguments: Tool arguments as a dictionary
            
        Returns:
            Parsed JSON response from the tool
        """
        try:
            logger.debug(f"🔧 Calling tool: {name} with args: {arguments}")
            
            server_params = StdioServerParameters(
                command="uv",
                args=["--directory", str(MCP_SERVER_PATH.parent), "run", "server.py"],
                env=None
            )
            
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    result = await session.call_tool(name, arguments)
                    
                    # Extract text content and parse as JSON
                    if result.content and len(result.content) > 0:
                        text = result.content[0].text
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return {"text": text}
                    
                    return {"error": "Empty response from tool"}
            
        except Exception as e:
            logger.error(f"❌ Tool call failed: {name} - {e}")
            return {"error": str(e)}
    
    # ==================== Convenience Methods ====================
    
    async def search_tracks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tracks on Spotify"""
        result = await self.call_tool("search_tracks", {"query": query, "limit": limit})
        return result.get("tracks", [])
    
    async def search_artist(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an artist by name"""
        result = await self.call_tool("search_artist", {"name": name})
        return result.get("artist")
    
    async def get_artist_top_tracks(self, artist_id: str) -> List[Dict[str, Any]]:
        """Get top tracks of an artist"""
        result = await self.call_tool("get_artist_top_tracks", {"artist_id": artist_id})
        return result.get("tracks", [])
    
    async def get_related_artists(self, artist_id: str) -> List[Dict[str, Any]]:
        """Get artists similar to the given artist"""
        result = await self.call_tool("get_related_artists", {"artist_id": artist_id})
        return result.get("artists", [])
    
    async def search_playlists(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for playlists"""
        result = await self.call_tool("search_playlists", {"query": query, "limit": limit})
        return result.get("playlists", [])
    
    async def get_playlist_tracks(self, playlist_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get tracks from a playlist"""
        result = await self.call_tool("get_playlist_tracks", {"playlist_id": playlist_id, "limit": limit})
        return result.get("tracks", [])
    
    async def search_by_genre(self, genre: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tracks by genre"""
        result = await self.call_tool("search_by_genre", {"genre": genre, "limit": limit})
        return result.get("tracks", [])
    
    async def get_genres(self) -> List[str]:
        """Get list of available Spotify genres"""
        result = await self.call_tool("get_genres", {})
        return result.get("genres", [])
    
    async def get_new_releases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently released albums"""
        result = await self.call_tool("get_new_releases", {"limit": limit})
        return result.get("albums", [])
    
    async def create_playlist(self, name: str, track_uris: List[str], description: str = "") -> Optional[Dict[str, Any]]:
        """Create a playlist with tracks"""
        result = await self.call_tool("create_playlist", {
            "name": name,
            "track_uris": track_uris,
            "description": description
        })
        return result.get("playlist")


# ==================== Context Manager ====================

@asynccontextmanager
async def get_mcp_client():
    """
    Async context manager for MCP client.
    
    Usage:
        async with get_mcp_client() as mcp:
            tracks = await mcp.search_tracks("happy songs")
    """
    client = SpotifyMCPClient()
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()


# ==================== Singleton Pattern ====================

_mcp_client: Optional[SpotifyMCPClient] = None


async def get_shared_mcp_client() -> SpotifyMCPClient:
    """
    Get or create a shared MCP client instance.
    """
    global _mcp_client
    
    if _mcp_client is None or not _mcp_client._connected:
        _mcp_client = SpotifyMCPClient()
        await _mcp_client.connect()
    
    return _mcp_client


async def close_shared_mcp_client():
    """Close the shared MCP client connection"""
    global _mcp_client
    
    if _mcp_client is not None:
        await _mcp_client.disconnect()
        _mcp_client = None
