"""
Music Recommendation AI Agent

Uses Groq LLM with function calling to explore Spotify's catalog
via MCP (Model Context Protocol) and curate personalized song recommendations.

The agent can:
1. Search for artists, playlists, and tracks
2. Explore related artists and top tracks
3. Browse by genre and new releases
4. Iterate to refine results
5. Curate final playlist with reasoning

Falls back to VADER sentiment analysis if Groq API fails completely.
"""

import json
import logging
from typing import Dict, Any, Optional

from services.mcp_client import SpotifyMCPClient
from services.vader_fallback import get_fallback_songs

logger = logging.getLogger(__name__)

# Maximum iterations for agent loop
MAX_ITERATIONS = 5

# Tool definitions for Groq function calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_artist",
            "description": "Find an artist by name. Use this when user mentions a specific artist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Artist name to search for"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_artist_top_tracks",
            "description": "Get the top/popular tracks of an artist. Use after finding an artist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_id": {"type": "string", "description": "Spotify artist ID"}
                },
                "required": ["artist_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_artists",
            "description": "Find artists similar to a given artist. Great for discovery.",
            "parameters": {
                "type": "object",
                "properties": {
                    "artist_id": {"type": "string", "description": "Spotify artist ID"}
                },
                "required": ["artist_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_tracks",
            "description": "Search for tracks by keywords. Use for mood/activity-based queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (mood, activity, genre, etc.)"},
                    "limit": {"type": "integer", "description": "Number of results (default 10)", "default": 10}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_playlists",
            "description": "Search for curated playlists by theme/mood/activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Playlist search query"},
                    "limit": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_playlist_tracks",
            "description": "Get tracks from a specific playlist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "playlist_id": {"type": "string", "description": "Spotify playlist ID"},
                    "limit": {"type": "integer", "description": "Number of tracks (default 20)", "default": 20}
                },
                "required": ["playlist_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_genre",
            "description": "Search tracks by genre. Use when user asks for a specific genre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre name (e.g., rock, jazz, hip-hop)"},
                    "limit": {"type": "integer", "description": "Number of results (default 10)", "default": 10}
                },
                "required": ["genre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_genres",
            "description": "Get list of all available Spotify genres. Use to discover valid genre names.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_new_releases",
            "description": "Get recently released albums. Use when user wants fresh/new music.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of albums (default 10)", "default": 10}
                }
            }
        }
    }
]

# System prompt for the agent - Balanced for quality and efficiency
SYSTEM_PROMPT = """You are a music curation AI with access to Spotify tools. Your goal is to find 10 PERFECT songs that match the user's request.

## UNDERSTANDING USER INTENT:

1. **Specific Song Name**: If user mentions a song title → Use search_tracks with the exact song name
2. **Specific Artist**: If user names an artist → Use search_artist, then get_artist_top_tracks for their best songs
3. **Mood/Vibe/Activity**: If user describes a feeling or activity → Use search_tracks with descriptive mood keywords
4. **Genre Request**: If user asks for a genre → Use search_by_genre
5. **Discovery/Related**: If user likes an artist → Use get_related_artists to find similar artists, then explore their tracks
6. **New Music**: If user wants fresh releases → Use get_new_releases

## SEARCH STRATEGY:

- **Be thorough**: Call 2-4 tools to gather diverse options and ensure quality matches
- **Understand context**: Consider the mood, vibe, and intent behind the user's request
- **Explore wisely**: If searching by artist, also check related artists for variety
- **Match the energy**: Pay attention to whether user wants upbeat, calm, energetic, sad, etc.

## IMPORTANT RULES:

- When an artist name is mentioned, ALWAYS use search_artist first to get their ID
- For mood-based requests, use descriptive keywords in search_tracks (e.g., "happy upbeat", "calm relaxing")
- Aim for diversity in your final selection - mix popular and lesser-known gems
- Each track MUST have a clear reason explaining why it fits the request

## FINAL RESPONSE (return as JSON):

After exploring, return ONLY this JSON structure:
{
    "tracks": [
        {"name": "Song Name", "artist": "Artist Name", "uri": "spotify:track:...", "reason": "Why this fits the user's request"},
        ... (exactly 10 tracks)
    ],
    "mood": "detected mood/vibe from user's request",
    "summary": "Brief explanation of your curation approach"
}"""


class MusicRecommendationAgent:
    """AI Agent that uses Groq + MCP tools to recommend music"""
    
    def __init__(self, groq_client):
        """
        Initialize the agent with a Groq client.
        
        Args:
            groq_client: Initialized Groq client with API key
        """
        self.groq = groq_client
        self.mcp_client: Optional[SpotifyMCPClient] = None
    
    async def _ensure_mcp_connected(self):
        """Ensure MCP client is connected"""
        if self.mcp_client is None or not self.mcp_client._connected:
            self.mcp_client = SpotifyMCPClient()
            await self.mcp_client.connect()
        
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by calling the MCP server via stdio.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result from MCP server
        """
        try:
            result = await self.mcp_client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"error": str(e)}
    
    def _truncate_tool_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reduce token usage by sending only essential data to LLM.
        
        Metadata like album_art, external_url, etc. will be added later
        during _enrich_tracks_with_metadata() so LLM doesn't need them.
        
        This reduces token usage by 70-80% per tool result!
        
        Args:
            result: Raw tool result from MCP server
            
        Returns:
            Truncated result with only essential fields for LLM decision-making
        """
        truncated = result.copy()
        
        # Tracks: Only name, artist, uri (metadata added later during enrichment)
        if "tracks" in truncated:
            truncated["tracks"] = [
                {
                    "name": t.get("name"),
                    "artist": t.get("artist"),
                    "uri": t.get("uri")
                }
                for t in truncated["tracks"][:15]  # Limit to first 15 instead of 20
            ]
            truncated["count"] = len(truncated["tracks"])
        
        # Artists: Only name and id (enough for LLM to decide next steps)
        if "artists" in truncated:
            truncated["artists"] = [
                {"name": a.get("name"), "id": a.get("id")}
                for a in truncated["artists"][:8]
            ]
            truncated["count"] = len(truncated["artists"])
        
        # Playlists: Only id and name
        if "playlists" in truncated:
            truncated["playlists"] = [
                {"id": p.get("id"), "name": p.get("name")}
                for p in truncated["playlists"][:5]
            ]
            truncated["count"] = len(truncated["playlists"])
        
        # Albums: Only id and name
        if "albums" in truncated:
            truncated["albums"] = [
                {"id": alb.get("id"), "name": alb.get("name")}
                for alb in truncated["albums"][:10]
            ]
            truncated["count"] = len(truncated["albums"])
        
        return truncated

    async def run(self, user_query: str) -> Dict[str, Any]:
        """
        Run the agent loop to get music recommendations.
        
        Args:
            user_query: User's music request (e.g., "something like Arctic Monkeys")
            
        Returns:
            Dict with tracks, mood, summary, and thought_process
        """
        # Try Groq + MCP agent first
        try:
            return await self._run_agent(user_query)
        except Exception as e:
            logger.error(f"❌ Agent totally failed: {e}")
            logger.info("⚠️ Falling back to VADER sentiment analysis")
            
            # Use VADER fallback - returns 10 curated songs
            fallback_songs = get_fallback_songs(user_query)
            
            return {
                "tracks": [{
                    "name": song["name"],
                    "artist": song["artist"],
                    "uri": f"spotify:search:{song['name']} {song['artist']}",
                    "album_art": "",
                    "external_url": f"https://open.spotify.com/search/{song['name']}",
                    "reason": "Curated for your mood"
                } for song in fallback_songs],
                "mood": "fallback",
                "summary": "Curated songs based on sentiment analysis (Groq unavailable)",
                "thought_process": [{"iteration": 1, "action": "Used VADER fallback", "result": "10 curated songs"}],
                "iterations": 1
            }
    
    async def _run_agent(self, user_query: str) -> Dict[str, Any]:
        """
        Internal agent loop with Groq + MCP.
        
        Args:
            user_query: User's music request
            
        Returns:
            Dict with tracks, mood, summary, and thought_process
            
        Raises:
            Exception: If Groq API completely fails
        """
        # Connect to MCP server at startup (no delay during tool calls)
        await self._ensure_mcp_connected()
        
        # Track agent's thought process for UI display
        thought_process = []
        
        # Collect all tracks found during search
        all_tracks = []
        
        # Initialize messages with system prompt and user query
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ]
        
        logger.info(f"🎵 Agent starting for query: {user_query}")
        
        for iteration in range(MAX_ITERATIONS):
            logger.info(f"🔄 Agent iteration {iteration + 1}/{MAX_ITERATIONS}")
            
            # On last iteration, force final answer by not passing tools
            is_last_iteration = iteration >= MAX_ITERATIONS - 1
            
            try:
                # Call Groq with tools (or without on last iteration)
                if is_last_iteration and all_tracks:
                    # Force final answer by asking to pick from gathered tracks
                    messages.append({
                        "role": "user",
                        "content": f"""You MUST now provide your final recommendation. 
                        
Pick the 10 BEST tracks from what you've found and return ONLY this JSON:
{{
    "tracks": [
        {{"name": "...", "artist": "...", "uri": "spotify:track:...", "reason": "Why this fits"}},
        ... (exactly 10 tracks)
    ],
    "mood": "detected mood/vibe",
    "summary": "Brief explanation of your curation"
}}

Here are some tracks you found: {json.dumps(all_tracks[:20])}"""
                    })
                    
                    response = self.groq.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                else:
                    response = self.groq.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages,
                        tools=AGENT_TOOLS,
                        tool_choice="auto",
                        temperature=0.7,
                        max_tokens=2000
                    )
                
                message = response.choices[0].message
                
                # Check if agent wants to call tools
                if message.tool_calls and not is_last_iteration:
                    # Record the assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            arguments = {}
                        
                        logger.info(f"🔧 Tool: {tool_name}({arguments})")
                        
                        # Record thought for UI
                        thought_process.append({
                            "iteration": iteration + 1,
                            "thought": message.content or f"Calling {tool_name}",
                            "tool": tool_name,
                            "arguments": arguments
                        })
                        
                        # Execute the tool
                        result = await self.execute_tool(tool_name, arguments)
                        
                        # Collect tracks from results (BEFORE truncation - we need full data)
                        if "tracks" in result:
                            all_tracks.extend(result["tracks"])
                        
                        # Truncate result for LLM (remove metadata to save tokens)
                        truncated_result = self._truncate_tool_result(result)
                        
                        # Add truncated tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(truncated_result)
                        })
                        
                        logger.info(f"📦 Tool result: {len(str(result))} chars → {len(str(truncated_result))} chars (saved {len(str(result)) - len(str(truncated_result))} chars)")
                
                else:
                    # Agent returned final response (no more tool calls)
                    final_content = message.content or ""
                    
                    logger.info("✅ Agent finished, parsing final response")
                    
                    # Try to parse JSON from response
                    try:
                        # Find JSON in the response
                        json_start = final_content.find('{')
                        json_end = final_content.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = final_content[json_start:json_end]
                            result = json.loads(json_str)
                            
                            # Enrich tracks with album_art from collected data
                            if "tracks" in result and all_tracks:
                                result["tracks"] = self._enrich_tracks_with_metadata(
                                    result["tracks"], all_tracks
                                )
                            
                            # Add thought process to result
                            result["thought_process"] = thought_process
                            result["iterations"] = iteration + 1
                            
                            return result
                        else:
                            # No JSON found, build response from gathered tracks
                            if all_tracks:
                                return self._build_fallback_response(all_tracks, thought_process, iteration + 1)
                            
                            return {
                                "error": "Could not parse agent response",
                                "raw_response": final_content,
                                "thought_process": thought_process
                            }
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parse error: {e}")
                        # Try to build response from gathered tracks
                        if all_tracks:
                            return self._build_fallback_response(all_tracks, thought_process, iteration + 1)
                        
                        return {
                            "error": "Invalid JSON in agent response",
                            "raw_response": final_content,
                            "thought_process": thought_process
                        }
                        
            except Exception as e:
                logger.error(f"Agent iteration error: {e}")
                thought_process.append({
                    "iteration": iteration + 1,
                    "error": str(e)
                })
        
        # Max iterations reached - build response from gathered tracks
        if all_tracks:
            return self._build_fallback_response(all_tracks, thought_process, MAX_ITERATIONS)
        
        return {
            "error": "Agent reached maximum iterations without completing",
            "thought_process": thought_process
        }
    
    def _build_fallback_response(self, tracks: list, thought_process: list, iterations: int) -> Dict[str, Any]:
        """Build a response from gathered tracks when agent fails to return JSON"""
        # Deduplicate by URI
        seen_uris = set()
        unique_tracks = []
        for track in tracks:
            uri = track.get("uri", "")
            if uri and uri not in seen_uris:
                seen_uris.add(uri)
                unique_tracks.append({
                    "name": track.get("name", "Unknown"),
                    "artist": track.get("artist", "Unknown"),
                    "uri": uri,
                    "album_art": track.get("album_art", ""),
                    "reason": "Found by AI agent exploration"
                })
        
        # Return whatever we found (even if less than 10)
        return {
            "tracks": unique_tracks,
            "mood": "curated",
            "summary": f"Curated {len(unique_tracks)} tracks from AI agent exploration",
            "thought_process": thought_process,
            "iterations": iterations
        }
    
    def _enrich_tracks_with_metadata(self, agent_tracks: list, collected_tracks: list) -> list:
        """
        Enrich tracks returned by LLM with metadata from collected raw data.
        LLM only returns name/artist/uri/reason - we need album_art from the raw API data.
        """
        # Build lookup dict by URI for fast matching
        track_lookup = {}
        for track in collected_tracks:
            uri = track.get("uri", "")
            if uri:
                track_lookup[uri] = track
        
        enriched = []
        for agent_track in agent_tracks:
            uri = agent_track.get("uri", "")
            
            # Try to find matching track in collected data
            raw_track = track_lookup.get(uri, {})
            
            enriched.append({
                "name": agent_track.get("name", raw_track.get("name", "Unknown")),
                "artist": agent_track.get("artist", raw_track.get("artist", "Unknown")),
                "uri": uri,
                "album_art": raw_track.get("album_art", ""),  # Get from raw data
                "external_url": raw_track.get("external_url", ""),  # Get from raw data
                "reason": agent_track.get("reason", "")
            })
        
        return enriched
    
    async def close(self):
        """Close MCP client connection"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            self.mcp_client = None
